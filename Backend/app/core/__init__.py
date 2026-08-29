from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def generate_api_key() -> str:
    """Generate a new plaintext AI-buyer API key. Shown to the merchant once."""
    return f"sk_aib_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Deterministic hash used to look up an API key by value."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _fernet() -> Any:
    import base64

    from cryptography.fernet import Fernet

    key = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = uuid.uuid4().hex
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, hash_hex = hashed.split(":", 1)
        expected = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100000)
        return hmac.compare_digest(expected.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    to_encode.setdefault("exp", datetime.now(timezone.utc).timestamp() + settings.jwt_expiry_minutes * 60)
    to_encode.setdefault("iat", datetime.now(timezone.utc).timestamp())
    to_encode.setdefault("jti", str(generate_uuid()))
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def verify_razorpay_webhook_signature(
    body: str, signature: str, secret: str
) -> bool:
    expected = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def generate_idempotency_key(*parts: str) -> str:
    raw = ":".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def hash_dict(data: dict[str, Any]) -> str:
    import json
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()
