from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.core import (
    create_access_token,
    generate_api_key,
    generate_uuid,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import Merchant, MerchantSettings
from app.repositories import MerchantRepository, MerchantSettingsRepository
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    MerchantResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = MerchantRepository(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    ai_buyer_api_key = generate_api_key()
    merchant = Merchant(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        store_name=body.store_name,
        ai_buyer_api_key_hash=hash_api_key(ai_buyer_api_key),
    )
    merchant = await repo.create(merchant)

    settings = MerchantSettings(merchant_id=merchant.id)
    db.add(settings)
    await db.flush()

    token = create_access_token({
        "sub": str(merchant.id),
        "merchant_id": str(merchant.id),
        "role": "merchant",
    })

    return TokenResponse(
        access_token=token,
        merchant_id=merchant.id,
        user_id=merchant.id,
        ai_buyer_api_key=ai_buyer_api_key,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    repo = MerchantRepository(db)
    merchant = await repo.get_by_email(body.email)
    if not merchant or not verify_password(body.password, merchant.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(merchant.id),
        "merchant_id": str(merchant.id),
        "role": "merchant",
    })

    return TokenResponse(
        access_token=token,
        merchant_id=merchant.id,
        user_id=merchant.id,
    )


@router.get("/me", response_model=MerchantResponse)
async def get_me(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> MerchantResponse:
    repo = MerchantRepository(db)
    merchant = await repo.get_by_id(uuid.UUID(auth.merchant_id))
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return MerchantResponse.model_validate(merchant)
