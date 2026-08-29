from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.services import ProductService
from app.schemas import ProductCreate, ProductResponse, ProductSearchResponse
from app.repositories import InventoryRepository
from app.schemas import InventoryResponse, InventoryUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductSearchResponse)
async def list_products(
    q: str | None = Query(None),
    category: str | None = Query(None),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    brand: str | None = Query(None),
    in_stock: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> ProductSearchResponse:
    service = ProductService(db, uuid.UUID(auth.merchant_id))
    products, total = await service.search_products(
        query=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        brand=brand,
        in_stock_only=in_stock,
        limit=limit,
        offset=offset,
    )
    return ProductSearchResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(db, uuid.UUID(auth.merchant_id))
    product = await service.create_product(**body.model_dump())
    return ProductResponse.model_validate(product)


@router.get("/categories", response_model=list[str])
async def get_categories(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    service = ProductService(db, uuid.UUID(auth.merchant_id))
    return await service.get_categories()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(db, uuid.UUID(auth.merchant_id))
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.get("/{product_id}/inventory", response_model=InventoryResponse)
async def get_inventory(
    product_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> InventoryResponse:
    repo = InventoryRepository(db, uuid.UUID(auth.merchant_id))
    inv = await repo.get_by_product(product_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return InventoryResponse(
        id=inv.id,
        product_id=inv.product_id,
        merchant_id=inv.merchant_id,
        quantity=inv.quantity,
        reserved=inv.reserved,
        available=inv.available,
        is_in_stock=inv.is_in_stock,
        is_low_stock=inv.is_low_stock,
        low_stock_threshold=inv.low_stock_threshold,
    )


@router.put("/{product_id}/inventory", response_model=InventoryResponse)
async def update_inventory(
    product_id: uuid.UUID,
    body: InventoryUpdate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> InventoryResponse:
    repo = InventoryRepository(db, uuid.UUID(auth.merchant_id))
    inv = await repo.get_by_product(product_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")

    update_data = body.model_dump(exclude_unset=True)
    inv = await repo.update(inv, **update_data)
    return InventoryResponse(
        id=inv.id,
        product_id=inv.product_id,
        merchant_id=inv.merchant_id,
        quantity=inv.quantity,
        reserved=inv.reserved,
        available=inv.available,
        is_in_stock=inv.is_in_stock,
        is_low_stock=inv.is_low_stock,
        low_stock_threshold=inv.low_stock_threshold,
    )
