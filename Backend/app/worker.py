from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings

from app.config import settings


async def startup(ctx: dict) -> None:
    from app.database import init_db
    await init_db()
    ctx["started"] = True


async def shutdown(ctx: dict) -> None:
    from app.database import close_db
    await close_db()


async def run_growth_analysis(ctx: dict) -> None:
    from app.database import async_session_factory
    from app.models import Merchant
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(Merchant))
        merchants = result.scalars().all()

        for merchant in merchants:
            from app.services.growth import GrowthAnalystService
            analyst = GrowthAnalystService(session, merchant.id)
            await analyst.analyze_opportunities()


async def detect_abandoned_carts(ctx: dict) -> None:
    pass


async def process_pending_webhooks(ctx: dict) -> None:
    pass


class WorkerSettings:
    functions = [run_growth_analysis, detect_abandoned_carts, process_pending_webhooks]
    cron_jobs = [
        cron(run_growth_analysis, hour={6, 12, 18}, minute=0),
        cron(detect_abandoned_carts, minute={0, 15, 30, 45}),
        cron(process_pending_webhooks, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    timeout = 300
