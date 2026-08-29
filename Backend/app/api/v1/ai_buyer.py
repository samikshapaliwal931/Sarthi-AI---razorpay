from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import ProductService, CartService, OrderService
from app.recommendations import RecommendationEngine
from app.razorpay import RazorpayService
from app.schemas import (
    StorefrontProductResponse,
    StorefrontSearchRequest,
    AIBuyerCheckoutRequest,
    AIBuyerCheckoutResponse,
    AIBuyerCartResponse,
)

router = APIRouter(prefix="/ai-buyer", tags=["ai-buyer"])


async def _get_merchant_by_api_key(db: AsyncSession, api_key: str) -> uuid.UUID:
    """Resolve the merchant that issued this AI-buyer API key."""
    from app.core import hash_api_key
    from app.models import Merchant
    from sqlalchemy import select

    stmt = select(Merchant).where(Merchant.ai_buyer_api_key_hash == hash_api_key(api_key))
    result = await db.execute(stmt)
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return merchant.id


@router.post("/search", response_model=list[StorefrontProductResponse])
async def ai_buyer_search(
    body: StorefrontSearchRequest,
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> list[StorefrontProductResponse]:
    """AI buyer: Search product catalog"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
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
        from app.repositories import InventoryRepository
        inv_repo = InventoryRepository(db, merchant_id)
        inv = await inv_repo.get_by_product(p.id)
        
        results.append(StorefrontProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            price=p.sale_price or p.base_price,
            currency=p.currency,
            in_stock=inv.is_in_stock if inv else True,
            images=p.images,
        ))
    return results


@router.get("/products/{product_id}", response_model=StorefrontProductResponse)
async def ai_buyer_get_product(
    product_id: uuid.UUID,
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> StorefrontProductResponse:
    """AI buyer: Get product details"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    service = ProductService(db, merchant_id)
    product = await service.get_product(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.repositories import InventoryRepository
    inv_repo = InventoryRepository(db, merchant_id)
    inv = await inv_repo.get_by_product(product_id)

    return StorefrontProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.sale_price or product.base_price,
        currency=product.currency,
        in_stock=inv.is_in_stock if inv else True,
        images=product.images,
    )


@router.get("/catalog")
async def ai_buyer_get_catalog(
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    category: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """AI buyer: Get full catalog (for AI agents to analyze)"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    service = ProductService(db, merchant_id)
    
    products, total = await service.search_products(
        category=category,
        limit=limit,
        offset=offset,
    )

    from app.repositories import InventoryRepository
    inv_repo = InventoryRepository(db, merchant_id)

    catalog_items = []
    for p in products:
        inv = await inv_repo.get_by_product(p.id)
        catalog_items.append({
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "subcategory": p.subcategory,
            "brand": p.brand,
            "price": p.sale_price or p.base_price,
            "currency": p.currency,
            "in_stock": inv.is_in_stock if inv else True,
            "available_quantity": inv.available if inv else 0,
            "images": p.images,
            "tags": p.tags,
            "attributes": p.attributes,
        })

    return {
        "merchant_id": str(merchant_id),
        "products": catalog_items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/cart/create", response_model=AIBuyerCartResponse)
async def ai_buyer_create_cart(
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> AIBuyerCartResponse:
    """AI buyer: Create a new cart"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    session_id = f"ai_buyer_{uuid.uuid4().hex[:16]}"
    
    service = CartService(db, merchant_id)
    cart = await service.get_or_create_cart(session_id)
    
    return AIBuyerCartResponse(
        cart_id=str(cart.id),
        session_id=session_id,
        items=[],
        subtotal=cart.subtotal,
        currency=cart.currency,
    )


@router.post("/cart/{cart_id}/add")
async def ai_buyer_add_to_cart(
    cart_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: int = Query(1, ge=1, le=10),
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> AIBuyerCartResponse:
    """AI buyer: Add item to cart"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    service = CartService(db, merchant_id)
    
    cart = await service.repo.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    try:
        cart = await service.add_item(cart, product_id, quantity=quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AIBuyerCartResponse(
        cart_id=str(cart.id),
        session_id=cart.session_id,
        items=[
            {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.unit_price * item.quantity,
            }
            for item in cart.items
        ],
        subtotal=cart.subtotal,
        currency=cart.currency,
    )


@router.get("/cart/{cart_id}", response_model=AIBuyerCartResponse)
async def ai_buyer_get_cart(
    cart_id: uuid.UUID,
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> AIBuyerCartResponse:
    """AI buyer: Get cart details"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    service = CartService(db, merchant_id)
    
    cart = await service.repo.get_by_id(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return AIBuyerCartResponse(
        cart_id=str(cart.id),
        session_id=cart.session_id,
        items=[
            {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.unit_price * item.quantity,
            }
            for item in cart.items
        ],
        subtotal=cart.subtotal,
        currency=cart.currency,
    )


@router.post("/checkout", response_model=AIBuyerCheckoutResponse)
async def ai_buyer_checkout(
    body: AIBuyerCheckoutRequest,
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> AIBuyerCheckoutResponse:
    """AI buyer: Create checkout session"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    
    # Get or create cart
    cart_service = CartService(db, merchant_id)
    cart = await cart_service.get_or_create_cart(body.session_id or f"ai_buyer_{uuid.uuid4().hex[:16]}")
    
    # Add items to cart
    for item in body.items:
        try:
            cart = await cart_service.add_item(cart, item.product_id, item.variant_id, item.quantity)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Create order
    order_service = OrderService(db, merchant_id)
    order = await order_service.create_order_from_cart(cart)
    
    # Create Razorpay checkout
    rzp_service = RazorpayService(db, merchant_id)
    try:
        result = await rzp_service.create_checkout_order(order)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    
    return AIBuyerCheckoutResponse(
        order_id=str(order.id),
        order_number=order.order_number,
        razorpay_order_id=result["razorpay_order_id"],
        amount=result["amount"],
        currency=result["currency"],
        key_id=result["key_id"],
        checkout_url=result.get("checkout_url"),
    )


@router.get("/order/{order_id}")
async def ai_buyer_get_order(
    order_id: uuid.UUID,
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """AI buyer: Get order status"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    
    from app.repositories import OrderRepository
    order_repo = OrderRepository(db, merchant_id)
    order = await order_repo.get_by_id(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status.value,
        "subtotal": order.subtotal,
        "discount": order.discount,
        "tax": order.tax,
        "total": order.total,
        "currency": order.currency,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            }
            for item in order.items
        ],
    }


@router.post("/recommendations")
async def ai_buyer_recommendations(
    product_id: uuid.UUID | None = None,
    query: str | None = None,
    limit: int = Query(5, ge=1, le=20),
    api_key: str = Query(..., description="Merchant API key for AI buyer access"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """AI buyer: Get product recommendations"""
    merchant_id = await _get_merchant_by_api_key(db, api_key)
    session_id = f"ai_buyer_{uuid.uuid4().hex[:16]}"
    
    engine = RecommendationEngine(db, merchant_id)
    
    if query:
        # Search-based recommendations
        service = ProductService(db, merchant_id)
        products, _ = await service.search_products(query=query, limit=limit)
        return [
            {
                "product_id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "price": p.sale_price or p.base_price,
                "currency": p.currency,
                "recommendation_type": "search",
                "score": 1.0,
            }
            for p in products
        ]
    else:
        # Standard recommendations
        recs = await engine.get_recommendations(
            session_id=session_id,
            product_id=product_id,
            limit=limit,
        )
        return [
            {
                "product_id": str(r["product"].id),
                "name": r["product"].name,
                "description": r["product"].description,
                "category": r["product"].category,
                "price": r["product"].sale_price or r["product"].base_price,
                "currency": r["product"].currency,
                "recommendation_type": r["type"],
                "score": r["score"],
            }
            for r in recs
        ]
