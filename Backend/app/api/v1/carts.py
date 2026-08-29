from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import get_current_auth, AuthContext
from app.models import Cart, CartStatus
from app.schemas import CartResponse

router = APIRouter(prefix="/carts", tags=["carts"])


@router.get("", response_model=list[CartResponse])
async def list_carts(
    db: AsyncSession = Depends(get_db),
    current_user: AuthContext = Depends(get_current_auth),
):
    """List all carts for the current merchant"""
    query = (
        select(Cart)
        .where(Cart.merchant_id == current_user.merchant_id)
        .order_by(Cart.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    carts = result.scalars().all()
    
    return [
        CartResponse(
            id=str(cart.id),
            merchant_id=str(cart.merchant_id),
            customer_id=str(cart.customer_id) if cart.customer_id else None,
            session_id=cart.session_id,
            status=cart.status.value,
            subtotal=float(cart.subtotal),
            currency=cart.currency,
            items=[],  # Items not included in list view
            created_at=cart.created_at.isoformat(),
            updated_at=cart.updated_at.isoformat() if cart.updated_at else None,
        )
        for cart in carts
    ]


@router.get("/{cart_id}", response_model=CartResponse)
async def get_cart(
    cart_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthContext = Depends(get_current_auth),
):
    """Get a specific cart by ID"""
    query = select(Cart).where(
        Cart.id == cart_id,
        Cart.merchant_id == current_user.merchant_id
    )
    result = await db.execute(query)
    cart = result.scalar_one_or_none()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    return CartResponse(
        id=str(cart.id),
        merchant_id=str(cart.merchant_id),
        customer_id=str(cart.customer_id) if cart.customer_id else None,
        session_id=cart.session_id,
        status=cart.status.value,
        subtotal=float(cart.subtotal),
        currency=cart.currency,
        items=[],  # Items not included for now
        created_at=cart.created_at.isoformat(),
        updated_at=cart.updated_at.isoformat() if cart.updated_at else None,
    )
