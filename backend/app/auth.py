
import os
from datetime import datetime, timedelta, timezone
from typing import Generator

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_jwt_secret() -> str:
    secret = os.getenv("SHIP_JWT_SECRET")

    if not secret or len(secret) < 32:
        raise RuntimeError(
            "SHIP_JWT_SECRET must contain at least 32 characters"
        )

    if "REPLACE_WITH" in secret:
        raise RuntimeError("SHIP_JWT_SECRET must be replaced")

    return secret


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> User | None:
    user = db.query(User).filter(User.username == username).first()

    if user is None or not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_access_token(username: str) -> str:
    try:
        expire_minutes = int(
            os.getenv("SHIP_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
    except ValueError as exc:
        raise RuntimeError(
            "SHIP_ACCESS_TOKEN_EXPIRE_MINUTES must be an integer"
        ) from exc

    if expire_minutes <= 0:
        raise RuntimeError(
            "SHIP_ACCESS_TOKEN_EXPIRE_MINUTES must be positive"
        )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes
    )

    payload = {
        "sub": username,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm="HS256",
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=["HS256"],
        )

        username = payload.get("sub")

        if not isinstance(username, str) or not username:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def create_admin_user() -> None:
    username = os.getenv("SHIP_ADMIN_USERNAME")
    password = os.getenv("SHIP_ADMIN_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "SHIP_ADMIN_USERNAME and SHIP_ADMIN_PASSWORD are required"
        )

    if "CHANGE_ME" in password or len(password) < 12:
        raise RuntimeError(
            "SHIP_ADMIN_PASSWORD must be replaced and contain "
            "at least 12 characters"
        )

    get_jwt_secret()

    if SessionLocal is None:
        raise RuntimeError("Database is unavailable")

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user is None:
            admin = User(
                username=username,
                hashed_password=hash_password(password),
                is_active=True,
            )

            db.add(admin)
            db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

