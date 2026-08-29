from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth, get_optional_auth
from app.database import get_db
from app.razorpay import RazorpayService
from app.services import OrderService
from app.schemas import CheckoutRequest, CheckoutResponse, PaymentResponse, VerifyPaymentRequest

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    merchant_id = uuid.UUID(auth.merchant_id)
    order_service = OrderService(db, merchant_id)
    rzp_service = RazorpayService(db, merchant_id)

    order = None
    if body.order_id:
        order = await order_service.get_order(body.order_id)
    elif body.cart_id:
        from app.services import CartService
        cart_service = CartService(db, merchant_id)
        cart = await cart_service.get_cart(body.cart_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
        order = await order_service.create_order_from_cart(cart)

    if not order:
        raise HTTPException(status_code=400, detail="No order or cart provided")

    try:
        result = await rzp_service.create_checkout_order(order)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return CheckoutResponse(**result)


@router.post("/verify", status_code=200)
async def verify_payment(
    body: VerifyPaymentRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    rzp_service = RazorpayService(db, uuid.UUID(auth.merchant_id))
    valid = await rzp_service.verify_payment_signature(
        body.razorpay_order_id, body.razorpay_payment_id, body.razorpay_signature
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    return {"status": "verified"}


@router.post("/webhook", status_code=200)
async def webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    import json

    from app.models import Order
    from sqlalchemy import select

    body = await request.body()
    raw_body = body.decode()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        payload = json.loads(raw_body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    # Payload is untrusted at this point — only used to route to the right
    # merchant's RazorpayService, which independently verifies the signature
    # against that merchant's own webhook secret before acting on anything.
    entity = payload.get("payload", {})
    rzp_order_id = (
        entity.get("payment", {}).get("entity", {}).get("order_id")
        or entity.get("order", {}).get("entity", {}).get("id")
    )
    if not rzp_order_id:
        raise HTTPException(status_code=400, detail="Unable to resolve order from webhook payload")

    stmt = select(Order.merchant_id).where(Order.razorpay_order_id == rzp_order_id)
    result = await db.execute(stmt)
    merchant_id = result.scalar_one_or_none()
    if not merchant_id:
        raise HTTPException(status_code=404, detail="No order found for webhook event")

    rzp_service = RazorpayService(db, merchant_id)
    try:
        result = await rzp_service.process_webhook(raw_body, signature)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/{order_id}", response_model=list[PaymentResponse])
async def get_order_payments(
    order_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[PaymentResponse]:
    from app.repositories import PaymentRepository
    repo = PaymentRepository(db, uuid.UUID(auth.merchant_id))
    payments = await repo.get_by_order(order_id)
    return [PaymentResponse.model_validate(p) for p in payments]
