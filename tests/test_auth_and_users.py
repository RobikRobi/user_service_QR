import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("USERS_DATABASE_URL", "postgresql://test:test@localhost/test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt
from fastapi import HTTPException
from sqlalchemy.sql.dml import Delete

from app.api_response import success_response
from app.config import config
from app.main import http_exception_handler
from app.routers import auth_router, user_router
from app.schemas.auth import LoginUser
from app.schemas.user import RegisterUser
from app.services import auth_service
from app.utillits import create_access_token, create_refresh_token, decode_refresh_token, verify_access_token


class UserRegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_register_user_returns_unified_success_response(self):
        async def fake_register_user(data, session):
            return success_response(
                "User registered successfully",
                {
                    "id": uuid.uuid4(),
                    "name": data.name,
                    "surname": data.surname,
                    "email": data.email,
                    "dob": data.dob,
                    "role": data.role,
                    "token": "access-token",
                },
            )

        data = RegisterUser(
            name="Ivan",
            surname="Petrov",
            email="ivan@example.com",
            password="strong-password",
            dob="2000-01-01",
            role="STUDENT",
        )

        with patch.object(user_router, "register_user_service", fake_register_user):
            body = await user_router.register_user(data, session=object())

        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "User registered successfully")
        self.assertEqual(body["data"]["email"], data.email)
        self.assertNotIn("password", body["data"])

    async def test_register_existing_user_returns_unified_error_response(self):
        response = await http_exception_handler(
            SimpleNamespace(),
            HTTPException(status_code=409, detail="User already exists"),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.body.decode(),
            '{"success":false,"error":{"code":409,"message":"User already exists"}}',
        )


class AuthEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_returns_tokens_in_unified_success_response(self):
        async def fake_login_user(data, session):
            return success_response(
                "Login successful",
                {
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                    "token_type": "bearer",
                },
            )

        data = LoginUser(email="ivan@example.com", password="strong-password")

        with patch.object(auth_router, "login_user", fake_login_user):
            body = await auth_router.login(data, session=object())

        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["token_type"], "bearer")
        self.assertIn("access_token", body["data"])
        self.assertIn("refresh_token", body["data"])

    async def test_refresh_returns_new_tokens(self):
        async def fake_refresh_user_token(refresh_token, session):
            self.assertEqual(refresh_token, "old-refresh-token")
            return success_response(
                "Token refreshed",
                {
                    "access_token": "new-access-token",
                    "refresh_token": "new-refresh-token",
                    "token_type": "bearer",
                },
            )

        with patch.object(auth_router, "refresh_user_token", fake_refresh_user_token):
            body = await auth_router.refresh("old-refresh-token", session=object())

        self.assertEqual(body["data"]["access_token"], "new-access-token")

    async def test_logout_returns_unified_success_response(self):
        async def fake_logout_user(refresh_token, session):
            self.assertEqual(refresh_token, "refresh-token")
            return success_response("Logged out successfully")

        with patch.object(auth_router, "logout_user", fake_logout_user):
            body = await auth_router.logout("refresh-token", session=object())

        self.assertEqual(
            body,
            {
                "success": True,
                "message": "Logged out successfully",
            },
        )


class TokenTests(unittest.IsolatedAsyncioTestCase):
    async def test_access_token_contains_user_id(self):
        user_id = uuid.uuid4()

        token = create_access_token(user_id)
        decoded_user_id = await verify_access_token(token)

        self.assertEqual(decoded_user_id, user_id)

    async def test_refresh_token_contains_user_id_and_type(self):
        user_id = uuid.uuid4()

        token = create_refresh_token(user_id)
        payload = decode_refresh_token(token)

        self.assertEqual(payload["sub"], str(user_id))
        self.assertEqual(payload["type"], "refresh")

    async def test_access_token_cannot_be_decoded_as_refresh_token(self):
        token = create_access_token(uuid.uuid4())

        with self.assertRaises(HTTPException) as exc:
            decode_refresh_token(token)

        self.assertEqual(exc.exception.status_code, 401)
        self.assertEqual(exc.exception.detail, "Invalid token type")

    async def test_expired_refresh_token_returns_unauthorized(self):
        token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "jti": str(uuid.uuid4()),
                "type": "refresh",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            key=config.auth_data.private_key.read_text(),
            algorithm=config.auth_data.algorithm,
        )

        with self.assertRaises(HTTPException) as exc:
            decode_refresh_token(token)

        self.assertEqual(exc.exception.status_code, 401)
        self.assertEqual(exc.exception.detail, "Token expired")


class RefreshTokenServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_expired_refresh_tokens_deletes_old_rows(self):
        class FakeSession:
            def __init__(self):
                self.statements = []
                self.commits = 0

            async def execute(self, statement):
                self.statements.append(statement)

            async def commit(self):
                self.commits += 1

        session = FakeSession()

        await auth_service.cleanup_expired_refresh_tokens(session)

        self.assertIsInstance(session.statements[0], Delete)
        self.assertEqual(session.commits, 1)

    async def test_refresh_rejects_expired_stored_token(self):
        user_id = uuid.uuid4()
        token_db = SimpleNamespace(
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            revoked=False,
        )

        class FakeResult:
            def scalar_one_or_none(self):
                return token_db

        class FakeSession:
            async def execute(self, statement):
                return FakeResult()

            async def commit(self):
                pass

        with patch.object(
            auth_service,
            "decode_refresh_token",
            return_value={"sub": str(user_id), "type": "refresh"},
        ):
            with self.assertRaises(HTTPException) as exc:
                await auth_service.refresh_user_token("refresh-token", FakeSession())

        self.assertEqual(exc.exception.status_code, 401)
        self.assertEqual(exc.exception.detail, "Token expired")
        self.assertTrue(token_db.revoked)


if __name__ == "__main__":
    unittest.main()
