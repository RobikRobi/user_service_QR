import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("USERS_DATABASE_URL", "postgresql://test:test@localhost/test")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.middleware.cors import CORSMiddleware

from app.config import EnvData
from app.main import app


class CorsConfigTests(unittest.TestCase):
    def test_cors_origins_are_parsed_from_comma_separated_env_value(self):
        env_data = EnvData(
            USERS_DATABASE_URL="postgresql://test:test@localhost/test",
            CORS_ORIGINS="http://localhost:3000, http://localhost:5173",
        )

        self.assertEqual(
            env_data.cors_origins,
            ["http://localhost:3000", "http://localhost:5173"],
        )

    def test_cors_middleware_is_registered(self):
        middleware_classes = [middleware.cls for middleware in app.user_middleware]

        self.assertIn(CORSMiddleware, middleware_classes)


if __name__ == "__main__":
    unittest.main()
