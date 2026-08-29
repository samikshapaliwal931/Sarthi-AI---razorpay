from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_password
from app.models import Merchant, MerchantSettings, Product, Inventory, Order, OrderStatus
from app.repositories import (
    ProductRepository,
    OrderRepository,
    InventoryRepository,
    MerchantRepository,
)


@pytest.mark.asyncio
async def test_tenant_isolation_products(db_session: AsyncSession):
    m1 = Merchant(
        name="Merchant 1",
        email=f"m1_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 1",
    )
    m2 = Merchant(
        name="Merchant 2",
        email=f"m2_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 2",
    )
    db_session.add_all([m1, m2])
    await db_session.flush()

    p1 = Product(
        merchant_id=m1.id, name="Product M1", category="Shoes",
        base_price=1000, is_active=True,
    )
    p2 = Product(
        merchant_id=m2.id, name="Product M2", category="Shoes",
        base_price=2000, is_active=True,
    )
    db_session.add_all([p1, p2])
    await db_session.flush()

    repo1 = ProductRepository(db_session, m1.id)
    repo2 = ProductRepository(db_session, m2.id)

    m1_products = await repo1.get_all()
    m2_products = await repo2.get_all()

    assert len(m1_products) == 1
    assert len(m2_products) == 1
    assert m1_products[0].name == "Product M1"
    assert m2_products[0].name == "Product M2"


@pytest.mark.asyncio
async def test_tenant_isolation_orders(db_session: AsyncSession):
    m1 = Merchant(
        name="Merchant 1",
        email=f"m1o_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 1",
    )
    m2 = Merchant(
        name="Merchant 2",
        email=f"m2o_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 2",
    )
    db_session.add_all([m1, m2])
    await db_session.flush()

    o1 = Order(merchant_id=m1.id, order_number="ORD-M1-001", status=OrderStatus.CREATED, total=100)
    o2 = Order(merchant_id=m2.id, order_number="ORD-M2-001", status=OrderStatus.CREATED, total=200)
    db_session.add_all([o1, o2])
    await db_session.flush()

    repo1 = OrderRepository(db_session, m1.id)
    repo2 = OrderRepository(db_session, m2.id)

    m1_orders = await repo1.get_all()
    m2_orders = await repo2.get_all()

    assert len(m1_orders) == 1
    assert len(m2_orders) == 1
    assert m1_orders[0].order_number == "ORD-M1-001"
    assert m2_orders[0].order_number == "ORD-M2-001"


@pytest.mark.asyncio
async def test_tenant_isolation_inventory(db_session: AsyncSession):
    m1 = Merchant(
        name="Merchant 1",
        email=f"m1i_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 1",
    )
    db_session.add(m1)
    await db_session.flush()

    p1 = Product(merchant_id=m1.id, name="P1", category="C", base_price=100, is_active=True)
    p2 = Product(merchant_id=m1.id, name="P2", category="C", base_price=200, is_active=True)
    db_session.add_all([p1, p2])
    await db_session.flush()

    inv1 = Inventory(product_id=p1.id, merchant_id=m1.id, quantity=100)
    inv2 = Inventory(product_id=p2.id, merchant_id=m1.id, quantity=50)
    db_session.add_all([inv1, inv2])
    await db_session.flush()

    repo = InventoryRepository(db_session, m1.id)
    result = await repo.bulk_get_by_products([p1.id, p2.id])

    assert len(result) == 2
    assert result[p1.id].quantity == 100
    assert result[p2.id].quantity == 50


@pytest.mark.asyncio
async def test_cannot_access_other_merchant_data(db_session: AsyncSession):
    m1 = Merchant(
        name="Merchant 1",
        email=f"m1x_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 1",
    )
    m2 = Merchant(
        name="Merchant 2",
        email=f"m2x_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        store_name="Store 2",
    )
    db_session.add_all([m1, m2])
    await db_session.flush()

    p = Product(merchant_id=m1.id, name="Secret Product", category="X", base_price=9999, is_active=True)
    db_session.add(p)
    await db_session.flush()

    repo_as_m2 = ProductRepository(db_session, m2.id)
    found = await repo_as_m2.get_by_id(p.id)

    assert found is None
