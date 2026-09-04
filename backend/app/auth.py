import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request

from app.database import get_connection


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =====================================================
# CONFIGURATION
# =====================================================

JWT_ALGORITHM = "HS256"

JWT_SECRET = os.getenv(
    "RECOVERAI_JWT_SECRET",
    "change-this-secret-before-production",
)

TOKEN_EXPIRE_MINUTES = 60


# =====================================================
# PASSWORD HASHING
# =====================================================

def hash_password(password: str) -> str:

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120000,
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:

    try:

        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)

        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120000,
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash,
        )

    except Exception:

        return False


# =====================================================
# CREATE ADMIN USER
# =====================================================

def initialize_admin_user():

    username = os.getenv(
        "RECOVERAI_ADMIN_USERNAME",
        "admin",
    )

    password = os.getenv(
        "RECOVERAI_ADMIN_PASSWORD",
    )

    if not password:

        print(
            "WARNING: RECOVERAI_ADMIN_PASSWORD "
            "is not configured."
        )

        return

    connection = get_connection()

    existing = connection.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if not existing:

        password_hash = hash_password(password)

        connection.execute(
            """
            INSERT INTO users (
                username,
                password_hash
            )
            VALUES (?, ?)
            """,
            (
                username,
                password_hash,
            ),
        )

        connection.commit()

        print(
            f"RecoverAI admin user created: {username}"
        )

    connection.close()


# =====================================================
# JWT
# =====================================================

def create_access_token(username: str):

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": username,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(request: Request):

    authorization = request.headers.get("Authorization")

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not authorization.startswith("Bearer "):

        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    token = authorization.split(
        " ",
        1,
    )[1]

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        username = payload.get("sub")

        if not username:

            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
            )

        return username

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Authentication token expired",
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )


# =====================================================
# LOGIN
# =====================================================

@router.post("/login")
def login(credentials: dict):

    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:

        raise HTTPException(
            status_code=400,
            detail="Username and password are required",
        )

    connection = get_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    connection.close()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not verify_password(
        password,
        user["password_hash"],
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    token = create_access_token(username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60,
        "username": username,
    }


# =====================================================
# AUTH CHECK
# =====================================================

@router.get("/me")
def current_user(
    username: str = Depends(get_current_user),
):

    return {
        "authenticated": True,
        "username": username,
    }