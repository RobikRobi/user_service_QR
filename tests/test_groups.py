import datetime
import os
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("USERS_DATABASE_URL", "postgresql://test:test@localhost/test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_response import success_response
from app.enum import UserRole
from app.routers import group_router
from app.schemas.group import CreateGroup


def fake_current_user():
    return SimpleNamespace(id=uuid.uuid4(), role=UserRole.ADMIN)


def show_group_payload(group_id=None, owner_id=None, name_group="Math"):
    now = datetime.datetime.now(datetime.UTC)
    return {
        "id": group_id or uuid.uuid4(),
        "name_group": name_group,
        "user_id": owner_id or uuid.uuid4(),
        "createdAt": now,
        "updatedAt": now,
    }


class GroupEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_group_returns_group(self):
        async def fake_create_group(data, current_user, session):
            return show_group_payload(owner_id=current_user.id, name_group=data.name_group)

        with patch.object(group_router, "create_group_service", fake_create_group):
            body = await group_router.create_group(
                CreateGroup(name_group="Physics"),
                current_user=fake_current_user(),
                session=object(),
            )

        self.assertEqual(body["name_group"], "Physics")
        self.assertIn("id", body)
        self.assertIn("user_id", body)

    async def test_get_groups_returns_group_list(self):
        async def fake_get_groups(current_user, session):
            return [show_group_payload(name_group="Math"), show_group_payload(name_group="Physics")]

        with patch.object(group_router, "get_groups_service", fake_get_groups):
            body = await group_router.get_groups(
                current_user=fake_current_user(),
                session=object(),
            )

        self.assertEqual(len(body), 2)
        self.assertEqual(body[0]["name_group"], "Math")

    async def test_add_user_to_group_returns_unified_success_response(self):
        group_id = uuid.uuid4()
        user_id = uuid.uuid4()

        async def fake_add_user_to_group(received_group_id, received_user_id, current_user, session):
            self.assertEqual(received_group_id, group_id)
            self.assertEqual(received_user_id, user_id)
            return success_response(
                "User added to group",
                {"group_id": received_group_id, "user_id": received_user_id},
            )

        with patch.object(group_router, "add_user_to_group_service", fake_add_user_to_group):
            body = await group_router.add_user_to_group(
                group_id,
                user_id,
                current_user=fake_current_user(),
                session=object(),
            )

        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "User added to group")
        self.assertEqual(body["data"]["group_id"], group_id)
        self.assertEqual(body["data"]["user_id"], user_id)

    async def test_remove_user_from_group_returns_unified_success_response(self):
        group_id = uuid.uuid4()
        user_id = uuid.uuid4()

        async def fake_remove_user_from_group(received_group_id, received_user_id, current_user, session):
            self.assertEqual(received_group_id, group_id)
            self.assertEqual(received_user_id, user_id)
            return success_response(
                "User removed from group",
                {"group_id": received_group_id, "user_id": received_user_id},
            )

        with patch.object(group_router, "remove_user_from_group_service", fake_remove_user_from_group):
            body = await group_router.remove_user_from_group(
                group_id,
                user_id,
                current_user=fake_current_user(),
                session=object(),
            )

        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "User removed from group")
        self.assertEqual(body["data"]["group_id"], group_id)
        self.assertEqual(body["data"]["user_id"], user_id)


if __name__ == "__main__":
    unittest.main()
