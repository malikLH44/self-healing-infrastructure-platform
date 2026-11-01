
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User
from app import auth


class AuthTests(unittest.TestCase):

    def setUp(self):
        self.secret = "test-secret-key-for-ship-auth-tests-123456789"

        self.env_patcher = patch.dict(
            os.environ,
            {
                "SHIP_JWT_SECRET": self.secret,
                "SHIP_ADMIN_USERNAME": "test-admin",
                "SHIP_ADMIN_PASSWORD": "StrongAdminPassword123!",
                "SHIP_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            },
        )
        self.env_patcher.start()

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        Base.metadata.create_all(bind=self.engine)

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

        self.session_patcher = patch(
            "app.auth.SessionLocal",
            self.SessionLocal,
        )
        self.session_patcher.start()

        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

        self.session_patcher.stop()
        self.env_patcher.stop()

    def add_user(
        self,
        username="test-admin",
        password="StrongAdminPassword123!",
        is_active=True,
    ):
        user = User(
            username=username,
            hashed_password=auth.hash_password(password),
            is_active=is_active,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def test_password_hash_and_verification(self):
        password = "StrongPassword123!"

        hashed = auth.hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(auth.verify_password(password, hashed))
        self.assertFalse(auth.verify_password("WrongPassword", hashed))

    def test_authenticate_user_success(self):
        self.add_user()

        user = auth.authenticate_user(
            self.db,
            "test-admin",
            "StrongAdminPassword123!",
        )

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test-admin")

    def test_authenticate_user_rejects_wrong_password(self):
        self.add_user()

        user = auth.authenticate_user(
            self.db,
            "test-admin",
            "WrongPassword123!",
        )

        self.assertIsNone(user)

    def test_authenticate_user_rejects_unknown_username(self):
        user = auth.authenticate_user(
            self.db,
            "unknown-user",
            "StrongAdminPassword123!",
        )

        self.assertIsNone(user)

    def test_authenticate_user_rejects_inactive_account(self):
        self.add_user(is_active=False)

        user = auth.authenticate_user(
            self.db,
            "test-admin",
            "StrongAdminPassword123!",
        )

        self.assertIsNone(user)

    def test_create_access_token(self):
        token = auth.create_access_token("test-admin")

        payload = jwt.decode(
            token,
            self.secret,
            algorithms=["HS256"],
        )

        self.assertEqual(payload["sub"], "test-admin")
        self.assertGreater(
            payload["exp"],
            datetime.now(timezone.utc).timestamp(),
        )

    def test_create_access_token_rejects_invalid_expiration(self):
        with patch.dict(
            os.environ,
            {"SHIP_ACCESS_TOKEN_EXPIRE_MINUTES": "invalid"},
        ):
            with self.assertRaises(RuntimeError):
                auth.create_access_token("test-admin")

        with patch.dict(
            os.environ,
            {"SHIP_ACCESS_TOKEN_EXPIRE_MINUTES": "0"},
        ):
            with self.assertRaises(RuntimeError):
                auth.create_access_token("test-admin")

    def test_create_access_token_rejects_invalid_secret(self):
        with patch.dict(
            os.environ,
            {"SHIP_JWT_SECRET": "short"},
        ):
            with self.assertRaises(RuntimeError):
                auth.create_access_token("test-admin")

    def test_get_current_user_accepts_valid_token(self):
        self.add_user()

        token = auth.create_access_token("test-admin")

        user = auth.get_current_user(token, self.db)

        self.assertEqual(user.username, "test-admin")

    def test_get_current_user_rejects_invalid_token(self):
        with self.assertRaises(HTTPException) as context:
            auth.get_current_user("invalid-token", self.db)

        self.assertEqual(context.exception.status_code, 401)

    def test_get_current_user_rejects_expired_token(self):
        expired_token = jwt.encode(
            {
                "sub": "test-admin",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            self.secret,
            algorithm="HS256",
        )

        with self.assertRaises(HTTPException) as context:
            auth.get_current_user(expired_token, self.db)

        self.assertEqual(context.exception.status_code, 401)

    def test_get_current_user_rejects_unknown_user(self):
        token = auth.create_access_token("unknown-user")

        with self.assertRaises(HTTPException) as context:
            auth.get_current_user(token, self.db)

        self.assertEqual(context.exception.status_code, 401)

    def test_get_current_user_rejects_inactive_user(self):
        self.add_user(is_active=False)

        token = auth.create_access_token("test-admin")

        with self.assertRaises(HTTPException) as context:
            auth.get_current_user(token, self.db)

        self.assertEqual(context.exception.status_code, 401)

    def test_create_admin_user_creates_account(self):
        auth.create_admin_user()

        user = (
            self.db.query(User)
            .filter(User.username == "test-admin")
            .first()
        )

        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)

        self.assertTrue(
            auth.verify_password(
                "StrongAdminPassword123!",
                user.hashed_password,
            )
        )

    def test_create_admin_user_is_idempotent(self):
        auth.create_admin_user()

        with patch.dict(
            os.environ,
            {"SHIP_ADMIN_PASSWORD": "AnotherStrongPassword456!"},
        ):
            auth.create_admin_user()

        user = (
            self.db.query(User)
            .filter(User.username == "test-admin")
            .first()
        )

        self.assertEqual(
            self.db.query(User).filter(
                User.username == "test-admin"
            ).count(),
            1,
        )

        self.assertTrue(
            auth.verify_password(
                "StrongAdminPassword123!",
                user.hashed_password,
            )
        )

        self.assertFalse(
            auth.verify_password(
                "AnotherStrongPassword456!",
                user.hashed_password,
            )
        )

    def test_create_admin_user_rejects_weak_password(self):
        with patch.dict(
            os.environ,
            {"SHIP_ADMIN_PASSWORD": "short"},
        ):
            with self.assertRaises(RuntimeError):
                auth.create_admin_user()

    def test_create_admin_user_rejects_placeholder_password(self):
        with patch.dict(
            os.environ,
            {"SHIP_ADMIN_PASSWORD": "CHANGE_ME_TO_A_REAL_PASSWORD"},
        ):
            with self.assertRaises(RuntimeError):
                auth.create_admin_user()

    def test_get_db_rejects_unavailable_database(self):
        with patch("app.auth.SessionLocal", None):
            generator = auth.get_db()

            with self.assertRaises(HTTPException) as context:
                next(generator)

            self.assertEqual(context.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()

