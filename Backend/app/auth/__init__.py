from __future__ import annotations

from typing import Any

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core import decode_access_token

logger = structlog.get_logger()

security = HTTPBearer(auto_error=False)


class AuthContext:
    def __init__(
        self,
        merchant_id: str,
        user_id: str,
        role: str,
        token_data: dict[str, Any],
    ) -> None:
        self.merchant_id = merchant_id
        self.user_id = user_id
        self.role = role
        self.token_data = token_data


async def get_current_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication",
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    merchant_id = payload.get("merchant_id")
    user_id = payload.get("sub")
    role = payload.get("role", "merchant")
    if not merchant_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    return AuthContext(
        merchant_id=str(merchant_id),
        user_id=str(user_id),
        role=role,
        token_data=payload,
    )


async def get_optional_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthContext | None:
    if credentials is None:
        return None
    return await get_current_auth(credentials)
