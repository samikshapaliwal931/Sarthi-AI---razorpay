from __future__ import annotations

import asyncio

import structlog

from app.demo import seed_demo_data
from app.database import init_db, close_db

logger = structlog.get_logger()


async def main() -> None:
    await init_db()
    logger.info("seeding_demo_data")
    await seed_demo_data()
    await close_db()
    logger.info("demo_seed_complete")


if __name__ == "__main__":
    asyncio.run(main())
