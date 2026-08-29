from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Merchant, MerchantSettings, Product, Inventory, Policy

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def merchant(db_session: AsyncSession) -> Merchant:
    m = Merchant(
        name="Test Merchant",
        email=f"test_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password("testpass123"),
        store_name="Test Store",
    )
    db_session.add(m)
    await db_session.flush()

    settings = MerchantSettings(merchant_id=m.id)
    db_session.add(settings)
    await db_session.commit()
    return m


@pytest_asyncio.fixture
async def merchant_with_products(db_session: AsyncSession, merchant: Merchant) -> tuple[Merchant, list[Product]]:
    products = []
    for i in range(10):
        p = Product(
            merchant_id=merchant.id,
            name=f"Test Product {i}",
            description=f"Description for product {i}",
            category="Running Shoes" if i < 5 else "Sports Socks",
            brand="TestBrand",
            base_price=1000.0 + (i * 500),
            sale_price=900.0 + (i * 500) if i % 2 == 0 else None,
            is_active=True,
        )
        db_session.add(p)
        products.append(p)

    await db_session.flush()

    for p in products:
        inv = Inventory(
            product_id=p.id,
            merchant_id=merchant.id,
            quantity=50,
            reserved=5,
            low_stock_threshold=5,
        )
        db_session.add(inv)

    await db_session.flush()
    return merchant, products


@pytest_asyncio.fixture
async def auth_token(merchant: Merchant) -> str:
    from app.core import create_access_token
    return create_access_token({
        "sub": str(merchant.id),
        "merchant_id": str(merchant.id),
        "role": "merchant",
    })


@pytest_asyncio.fixture
async def client(auth_token: str) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {auth_token}"
        yield ac

    app.dependency_overrides.clear()
