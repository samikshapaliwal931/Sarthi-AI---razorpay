from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_password
from app.models import (
    Merchant,
    MerchantSettings,
    Product,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    Cart,
    CartItem,
    CartStatus,
)
from app.services import ProductService, CartService, OrderService
from app.services.growth import AttributionService


@pytest.mark.asyncio
async def test_product_search_with_price_filter(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"ps_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    cheap = Product(
        merchant_id=merchant.id, name="Cheap Shoe", category="Shoes",
        base_price=1000, is_active=True,
    )
    expensive = Product(
        merchant_id=merchant.id, name="Expensive Shoe", category="Shoes",
        base_price=10000, is_active=True,
    )
    db_session.add_all([cheap, expensive])
    await db_session.flush()

    for p in [cheap, expensive]:
        db_session.add(Inventory(product_id=p.id, merchant_id=merchant.id, quantity=50))
    await db_session.flush()

    service = ProductService(db_session, merchant.id)

    products, total = await service.search_products(max_price=5000)
    assert total == 1
    assert products[0].name == "Cheap Shoe"

    products, total = await service.search_products(min_price=5000)
    assert total == 1
    assert products[0].name == "Expensive Shoe"


@pytest.mark.asyncio
async def test_inventory_validation(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"iv_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    product = Product(
        merchant_id=merchant.id, name="Test Shoe", category="Shoes",
        base_price=3000, is_active=True,
    )
    db_session.add(product)
    await db_session.flush()

    inv = Inventory(product_id=product.id, merchant_id=merchant.id, quantity=5, reserved=3)
    db_session.add(inv)
    await db_session.flush()

    assert inv.available == 2
    assert inv.is_in_stock is True

    inv2 = Inventory(product_id=product.id, merchant_id=merchant.id, quantity=0, reserved=0)

    assert inv2.available == 0
    assert inv2.is_in_stock is False


@pytest.mark.asyncio
async def test_cart_consistency(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"cc_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    p1 = Product(merchant_id=merchant.id, name="P1", category="C", base_price=1000, is_active=True)
    p2 = Product(merchant_id=merchant.id, name="P2", category="C", base_price=2000, is_active=True)
    db_session.add_all([p1, p2])
    await db_session.flush()

    for p in [p1, p2]:
        db_session.add(Inventory(product_id=p.id, merchant_id=merchant.id, quantity=50))
    await db_session.flush()

    service = CartService(db_session, merchant.id)
    cart = await service.get_or_create_cart("test_session_123")

    cart = await service.add_item(cart, p1.id, quantity=2)
    assert cart.subtotal == 2000

    cart = await service.add_item(cart, p2.id, quantity=1)
    assert cart.subtotal == 4000


@pytest.mark.asyncio
async def test_attribution_tracking(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"at_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        order_number="ORD-ATTR-001",
        status=OrderStatus.PAID,
        total=5000,
    )
    db_session.add(order)
    await db_session.flush()

    attr_service = AttributionService(db_session, merchant.id)
    await attr_service.attribute_order(
        order_id=order.id,
        attribution_type="direct",
        amount=5000,
    )

    total = await attr_service.get_total_attributed_revenue()
    assert total == 5000
