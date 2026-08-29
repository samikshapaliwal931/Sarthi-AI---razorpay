from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.services import CartService, OrderService
from app.schemas import (
    CartAddItem,
    CartResponse,
    CartItemResponse,
    CartUpdateItem,
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
)

router = APIRouter(tags=["carts"])


@router.get("/carts/{session_id}", response_model=CartResponse)
async def get_cart(
    session_id: str,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db, uuid.UUID(auth.merchant_id))
    cart = await service.repo.get_active_by_session(session_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart = await service.get_cart(cart.id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return CartResponse(
        id=cart.id,
        merchant_id=cart.merchant_id,
        customer_id=cart.customer_id,
        session_id=cart.session_id,
        status=cart.status.value,
        subtotal=cart.subtotal,
        currency=cart.currency,
        items=[
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in cart.items
        ],
    )


@router.post("/carts/{session_id}/items", response_model=CartResponse)
async def add_to_cart(
    session_id: str,
    body: CartAddItem,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CartResponse:
    service = CartService(db, uuid.UUID(auth.merchant_id))
    cart = await service.get_or_create_cart(session_id)

    try:
        cart = await service.add_item(
            cart, body.product_id, body.variant_id, body.quantity
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cart = await service.get_cart(cart.id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return CartResponse(
        id=cart.id,
        merchant_id=cart.merchant_id,
        customer_id=cart.customer_id,
        session_id=cart.session_id,
        status=cart.status.value,
        subtotal=cart.subtotal,
        currency=cart.currency,
        items=[
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in cart.items
        ],
    )


@router.delete("/carts/items/{item_id}", status_code=204)
async def remove_from_cart(
    item_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = CartService(db, uuid.UUID(auth.merchant_id))
    from app.repositories import CartRepository
    repo = CartRepository(db, uuid.UUID(auth.merchant_id))
    from sqlalchemy import select
    from app.models import CartItem
    stmt = select(CartItem).where(
        CartItem.id == item_id,
        CartItem.merchant_id == uuid.UUID(auth.merchant_id),
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart = await repo.get_by_id(item.cart_id)
    if cart:
        await service.remove_item(cart, item_id)


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[OrderResponse]:
    from app.models import OrderStatus
    from app.repositories import OrderRepository

    status_filter = None
    if status:
        try:
            status_filter = OrderStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    repo = OrderRepository(db, uuid.UUID(auth.merchant_id))
    orders = await repo.get_all(limit=min(limit, 200), offset=offset, status=status_filter)
    
    result = []
    for order in orders:
        order_with_items = await repo.get_with_items(order.id)
        if order_with_items:
            result.append(OrderResponse(
                id=order_with_items.id,
                merchant_id=order_with_items.merchant_id,
                customer_id=order_with_items.customer_id,
                order_number=order_with_items.order_number,
                status=order_with_items.status.value,
                subtotal=order_with_items.subtotal,
                discount=order_with_items.discount,
                tax=order_with_items.tax,
                total=order_with_items.total,
                currency=order_with_items.currency,
                razorpay_order_id=order_with_items.razorpay_order_id,
                created_at=order_with_items.created_at,
                updated_at=order_with_items.updated_at,
                items=[
                    OrderItemResponse(
                        id=item.id,
                        product_id=item.product_id,
                        variant_id=item.variant_id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                    )
                    for item in order_with_items.items
                ],
            ))
    return result


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    body: OrderCreate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    service = OrderService(db, uuid.UUID(auth.merchant_id))
    cart_service = CartService(db, uuid.UUID(auth.merchant_id))

    if body.customer_id:
        from app.repositories import CustomerRepository
        cust_repo = CustomerRepository(db, uuid.UUID(auth.merchant_id))
        customer = await cust_repo.get_by_id(body.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

    from app.models import Cart
    from sqlalchemy import select
    stmt = select(Cart).where(
        Cart.merchant_id == uuid.UUID(auth.merchant_id),
        Cart.status == "active",
    ).limit(1)
    result = await db.execute(stmt)
    cart = result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=400, detail="No active cart found")

    cart = await cart_service.get_cart(cart.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    try:
        order = await service.create_order_from_cart(cart, body.customer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    order = await service.get_order(order.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id,
        merchant_id=order.merchant_id,
        customer_id=order.customer_id,
        order_number=order.order_number,
        status=order.status.value,
        subtotal=order.subtotal,
        discount=order.discount,
        tax=order.tax,
        total=order.total,
        currency=order.currency,
        razorpay_order_id=order.razorpay_order_id,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
            for item in order.items
        ],
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    service = OrderService(db, uuid.UUID(auth.merchant_id))
    order = await service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(
        id=order.id,
        merchant_id=order.merchant_id,
        customer_id=order.customer_id,
        order_number=order.order_number,
        status=order.status.value,
        subtotal=order.subtotal,
        discount=order.discount,
        tax=order.tax,
        total=order.total,
        currency=order.currency,
        razorpay_order_id=order.razorpay_order_id,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
            for item in order.items
        ],
    )
