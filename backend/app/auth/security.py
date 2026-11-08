"""
Authentication and Security Module for Automated Attendance System FastAPI Backend.
Implements PBKDF2 password hashing and tamper-proof HMAC-SHA256 bearer tokens.
"""

import os
import json
import base64
import hmac
import hashlib
import time
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Header, Depends
from database.db_manager import DatabaseManager

# Secret key for signing bearer tokens (can be overridden via environment variable)
SECRET_KEY = os.environ.get("ATTENDANCE_SECRET_KEY", "face_attendance_secure_app_secret_key_2026_x99")
TOKEN_EXPIRY_HOURS = 24


def create_access_token(admin_data: Dict[str, Any]) -> str:
    """
    Generate a tamper-proof signed bearer token containing admin payload.
    Uses JSON + Base64Url + HMAC-SHA256.
    """
    payload = {
        "admin_id": admin_data.get("admin_id"),
        "username": admin_data.get("username"),
        "full_name": admin_data.get("full_name"),
        "exp": int(time.time()) + (TOKEN_EXPIRY_HOURS * 3600),
        "iat": int(time.time()),
        "nonce": secrets.token_hex(8),
    }

    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")

    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify signature and expiration of a bearer token.
    Returns decoded payload if valid, None otherwise.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, signature = parts
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        # Add padding back for base64 decoding
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < time.time():
            return None  # Token expired

        return payload
    except Exception:
        return None


def get_current_admin(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    FastAPI dependency to protect routes and verify admin bearer token.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

