from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.repositories import MerchantSettingsRepository, MerchantRepository
from app.schemas import MerchantResponse, MerchantSettingsResponse, MerchantSettingsUpdate

router = APIRouter(prefix="/merchant", tags=["merchant"])


@router.get("", response_model=MerchantResponse)
async def get_merchant(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> MerchantResponse:
    repo = MerchantRepository(db)
    merchant = await repo.get_by_id(uuid.UUID(auth.merchant_id))
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return MerchantResponse.model_validate(merchant)


@router.get("/settings", response_model=MerchantSettingsResponse)
async def get_settings(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> MerchantSettingsResponse:
    repo = MerchantSettingsRepository(db, uuid.UUID(auth.merchant_id))
    settings = await repo.get_by_merchant()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return MerchantSettingsResponse.model_validate(settings)


@router.put("/settings", response_model=MerchantSettingsResponse)
async def update_settings(
    body: MerchantSettingsUpdate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> MerchantSettingsResponse:
    repo = MerchantSettingsRepository(db, uuid.UUID(auth.merchant_id))
    settings = await repo.get_by_merchant()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    update_data = body.model_dump(exclude_unset=True)
    settings = await repo.update(settings, **update_data)
    return MerchantSettingsResponse.model_validate(settings)
