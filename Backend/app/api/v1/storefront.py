from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import ProductService, CartService, OrderService
from app.razorpay import RazorpayService
from app.recommendations import RecommendationEngine
from app.schemas import (
    StorefrontProductResponse,
    StorefrontSearchRequest,
    StorefrontCheckoutRequest,
    StorefrontCheckoutResponse,
    InventoryResponse,
)

router = APIRouter(prefix="/storefront", tags=["storefront"])


async def _get_demo_merchant(db: AsyncSession) -> uuid.UUID:
    from app.models import Merchant
    from sqlalchemy import select
    stmt = select(Merchant).order_by(Merchant.created_at.asc()).limit(1)
    result = await db.execute(stmt)
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(status_code=404, detail="No merchant available")
    return merchant.id


@router.get("/products", response_model=list[StorefrontProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
) -> list[StorefrontProductResponse]:
    merchant_id = await _get_demo_merchant(db)
    service = ProductService(db, merchant_id)
    products, _ = await service.search_products(limit=100)

    results = []
    for p in products:
        results.append(StorefrontProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            price=p.sale_price or p.base_price,
            currency=p.currency,
            in_stock=True,
            images=p.images,
        ))
    return results


@router.post("/search", response_model=list[StorefrontProductResponse])
async def search_products(
    body: StorefrontSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[StorefrontProductResponse]:
    merchant_id = await _get_demo_merchant(db)
    service = ProductService(db, merchant_id)
    products, _ = await service.search_products(
        query=body.query,
        category=body.category,
        min_price=body.min_price,
        max_price=body.max_price,
        limit=body.limit,
    )

    results = []
    for p in products:
        results.append(StorefrontProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            price=p.sale_price or p.base_price,
            currency=p.currency,
            in_stock=True,
            images=p.images,
        ))
    return results


@router.get("/products/{product_id}", response_model=StorefrontProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StorefrontProductResponse:
    merchant_id = await _get_demo_merchant(db)
    service = ProductService(db, merchant_id)
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return StorefrontProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.sale_price or product.base_price,
        currency=product.currency,
        in_stock=True,
        images=product.images,
    )


@router.get("/products/{product_id}/availability")
async def check_availability(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool | int]:
    merchant_id = await _get_demo_merchant(db)
    from app.repositories import InventoryRepository
    repo = InventoryRepository(db, merchant_id)
    inv = await repo.get_by_product(product_id)
    if not inv:
        return {"in_stock": False, "available": 0}
    return {"in_stock": inv.is_in_stock, "available": inv.available}


@router.post("/cart/{session_id}/add")
async def add_to_cart(
    session_id: str,
    product_id: uuid.UUID,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | float]:
    merchant_id = await _get_demo_merchant(db)
    service = CartService(db, merchant_id)
    cart = await service.get_or_create_cart(session_id)
    try:
        cart = await service.add_item(cart, product_id, quantity=quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "added", "cart_subtotal": cart.subtotal}


@router.get("/cart/{session_id}")
async def get_cart(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    merchant_id = await _get_demo_merchant(db)
    service = CartService(db, merchant_id)
    cart = await service.repo.get_active_by_session(session_id)
    if not cart:
        return {"items": [], "subtotal": 0}
    cart = await service.get_cart(cart.id)
    if not cart:
        return {"items": [], "subtotal": 0}
    return {
        "id": str(cart.id),
        "items": [
            {"product_id": str(i.product_id), "quantity": i.quantity, "unit_price": i.unit_price}
            for i in cart.items
        ],
        "subtotal": cart.subtotal,
    }


@router.post("/checkout", response_model=StorefrontCheckoutResponse)
async def checkout(
    body: StorefrontCheckoutRequest,
    db: AsyncSession = Depends(get_db),
) -> StorefrontCheckoutResponse:
    merchant_id = await _get_demo_merchant(db)
    session_id = f"storefront_{uuid.uuid4().hex[:12]}"

    cart_service = CartService(db, merchant_id)
    cart = await cart_service.get_or_create_cart(session_id)

    for item in body.items:
        try:
            cart = await cart_service.add_item(cart, item.product_id, item.variant_id, item.quantity)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    order_service = OrderService(db, merchant_id)
    order = await order_service.create_order_from_cart(cart)

    rzp_service = RazorpayService(db, merchant_id)
    try:
        result = await rzp_service.create_checkout_order(order)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return StorefrontCheckoutResponse(
        razorpay_order_id=result["razorpay_order_id"],
        amount=result["amount"],
        currency=result["currency"],
        key_id=result["key_id"],
        order_id=order.id,
        test_mode=result.get("test_mode", False),
    )


@router.post("/order/{order_id}/confirm")
async def confirm_order_payment(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Simulate a successful payment capture in demo/test mode.

    In production this endpoint does not exist — payment state is driven
    exclusively by Razorpay webhooks with signature verification.
    """
    merchant_id = await _get_demo_merchant(db)
    rzp_service = RazorpayService(db, merchant_id)
    if not await rzp_service.is_test_mode():
        raise HTTPException(status_code=400, detail="Payment confirmation is handled by Razorpay in production")
    try:
        return await rzp_service.simulate_payment_success(str(order_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/recommendations")
async def get_recommendations(
    session_id: str,
    product_id: uuid.UUID | None = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    merchant_id = await _get_demo_merchant(db)
    engine = RecommendationEngine(db, merchant_id)
    recs = await engine.get_recommendations(
        session_id=session_id,
        product_id=product_id,
        limit=limit,
    )
    return [
        {
            "product_id": str(r["product"].id),
            "name": r["product"].name,
            "price": r["product"].sale_price or r["product"].base_price,
            "score": r["score"],
            "type": r["type"],
        }
        for r in recs
    ]
