from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.database import init_db, close_db
from app.observability import setup_observability

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_observability()
    await init_db()
    logger.info("sarthi_started", env=settings.app_env.value)
    yield
    await close_db()
    logger.info("sarthi_stopped")


app = FastAPI(
    title="Sarthi",
    description="Autonomous revenue optimization layer for ecommerce merchants",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "sarthi"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/widget/sarthi.js")
async def public_widget_js() -> Response:
    """Publicly accessible widget script (embedded on merchant sites)."""
    from fastapi.responses import Response
    from app.integrations.widget import WidgetService
    from app.models import Merchant
    from sqlalchemy import select
    from app.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(select(Merchant).order_by(Merchant.created_at.asc()).limit(1))
        merchant = result.scalar_one_or_none()
        merchant_id = merchant.id if merchant else uuid.uuid4()

    service = WidgetService(merchant_id, settings.api_base_url)
    js = service.generate_widget_js()
    return Response(
        content=js,
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"},
    )
