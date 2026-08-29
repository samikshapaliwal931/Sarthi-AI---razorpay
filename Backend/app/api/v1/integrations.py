from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.integrations.catalog_sync import CatalogSyncService
from app.integrations.widget import WidgetService
from app.schemas import (
    CatalogSyncRequest,
    CatalogSyncResponse,
    WidgetConfigRequest,
    WidgetEmbedResponse,
    IntegrationListResponse,
    IntegrationResponse,
    RazorpayConnectRequest,
    AIBuyerApiKeyResponse,
)
from app.models import MerchantIntegration
from sqlalchemy import select

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/catalog/sync", response_model=CatalogSyncResponse)
async def sync_catalog(
    body: CatalogSyncRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CatalogSyncResponse:
    """Sync product catalog from external source"""
    merchant_id = uuid.UUID(auth.merchant_id)
    service = CatalogSyncService(db, merchant_id)
    
    if body.sync_type == "json":
        stats = await service.sync_from_json(body.products_data)
    elif body.sync_type == "api":
        stats = await service.sync_from_api(body.api_config)
    elif body.sync_type == "database":
        stats = await service.sync_from_database(body.db_config)
    else:
        raise HTTPException(status_code=400, detail="Invalid sync type")
    
    # Record sync result
    await service.record_sync_result(body.sync_type, stats)
    
    return CatalogSyncResponse(
        sync_type=body.sync_type,
        products_created=stats["created"],
        products_updated=stats["updated"],
        products_skipped=stats["skipped"],
        errors=stats["errors"],
        status="completed" if stats["errors"] == 0 else "completed_with_errors"
    )


@router.post("/widget/generate", response_model=WidgetEmbedResponse)
async def generate_widget(
    body: WidgetConfigRequest | None = None,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> WidgetEmbedResponse:
    """Generate embed code for Sarthi widget"""
    from app.config import settings
    
    merchant_id = uuid.UUID(auth.merchant_id)
    api_base_url = settings.api_base_url or "http://localhost:8000"
    
    service = WidgetService(merchant_id, api_base_url)
    config = body.model_dump() if body else None
    
    embed_code = service.generate_embed_code(config)
    
    return WidgetEmbedResponse(
        merchant_id=merchant_id,
        script_url=embed_code["script_url"],
        html_snippet=embed_code["html_snippet"],
        react_snippet=embed_code["react_snippet"],
        vue_snippet=embed_code["vue_snippet"],
        config=embed_code["config"]
    )


@router.get("/widget/js")
async def get_widget_js(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get the actual widget JavaScript file"""
    from app.config import settings
    from fastapi.responses import Response
    
    merchant_id = uuid.UUID(auth.merchant_id)
    api_base_url = settings.api_base_url or "http://localhost:8000"
    
    service = WidgetService(merchant_id, api_base_url)
    js_content = service.generate_widget_js()
    
    return Response(
        content=js_content,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/widget/public/{merchant_id}")
async def get_public_widget_js(
    merchant_id: str,
):
    """Public widget JS endpoint - no auth required for embedded widgets"""
    from app.config import settings
    
    api_base_url = settings.api_base_url or "http://localhost:8000"
    
    service = WidgetService(uuid.UUID(merchant_id), api_base_url)
    js_content = service.generate_widget_js()
    
    return Response(
        content=js_content,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.get("/widget/no-code/{platform}")
async def get_no_code_snippet(
    platform: str,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get no-code platform snippet"""
    from app.config import settings
    
    merchant_id = uuid.UUID(auth.merchant_id)
    api_base_url = settings.api_base_url or "http://localhost:8000"
    
    service = WidgetService(merchant_id, api_base_url)
    snippet = service.generate_no_code_snippet(platform)
    
    if "Platform not supported" in snippet:
        raise HTTPException(status_code=400, detail=f"Platform {platform} not supported")
    
    return {"platform": platform, "snippet": snippet}


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[IntegrationResponse]:
    """List all merchant integrations"""
    merchant_id = uuid.UUID(auth.merchant_id)
    
    stmt = select(MerchantIntegration).where(
        MerchantIntegration.merchant_id == merchant_id
    )
    result = await db.execute(stmt)
    integrations = result.scalars().all()
    
    return [
        IntegrationResponse(
            id=integration.id,
            provider=integration.provider,
            integration_type=integration.integration_type,
            config=integration.config,
            is_active=integration.is_active,
            created_at=integration.created_at,
            updated_at=integration.updated_at
        )
        for integration in integrations
    ]


@router.post("/razorpay/connect")
async def connect_razorpay(
    body: RazorpayConnectRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Connect Razorpay account"""
    from app.core import encrypt_secret
    from app.core import utcnow
    from app.models import Merchant
    from sqlalchemy import select

    merchant_id = uuid.UUID(auth.merchant_id)

    stmt = select(Merchant).where(Merchant.id == merchant_id)
    result = await db.execute(stmt)
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    merchant.razorpay_key_id = body.key_id
    merchant.razorpay_key_secret_encrypted = encrypt_secret(body.key_secret)
    merchant.razorpay_webhook_secret_encrypted = (
        encrypt_secret(body.webhook_secret) if body.webhook_secret else None
    )

    await db.flush()

    connected_at = utcnow()
    integration = MerchantIntegration(
        merchant_id=merchant_id,
        provider="razorpay",
        integration_type="payments",
        config={"key_id": body.key_id, "connected_at": connected_at.isoformat()},
        is_active=True
    )
    db.add(integration)
    await db.flush()

    return {"status": "connected", "provider": "razorpay"}


@router.post("/ai-buyer/api-key/regenerate", response_model=AIBuyerApiKeyResponse)
async def regenerate_ai_buyer_api_key(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> AIBuyerApiKeyResponse:
    """Issue a new AI-buyer API key for this merchant. Invalidates the previous one."""
    from app.core import generate_api_key, hash_api_key
    from app.models import Merchant
    from sqlalchemy import select

    merchant_id = uuid.UUID(auth.merchant_id)

    stmt = select(Merchant).where(Merchant.id == merchant_id)
    result = await db.execute(stmt)
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    api_key = generate_api_key()
    merchant.ai_buyer_api_key_hash = hash_api_key(api_key)
    await db.flush()

    return AIBuyerApiKeyResponse(api_key=api_key)


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete an integration"""
    merchant_id = uuid.UUID(auth.merchant_id)
    
    stmt = select(MerchantIntegration).where(
        MerchantIntegration.id == integration_id,
        MerchantIntegration.merchant_id == merchant_id
    )
    result = await db.execute(stmt)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    await db.delete(integration)
    await db.flush()
    
    return {"status": "deleted", "integration_id": str(integration_id)}
