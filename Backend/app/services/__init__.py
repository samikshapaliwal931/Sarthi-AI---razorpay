from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import generate_uuid, utcnow
from app.models import (
    Cart,
    CartItem,
    CartStatus,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    Product,
)
from app.repositories import (
    CartRepository,
    InventoryRepository,
    OrderRepository,
    ProductRepository,
)

logger = structlog.get_logger()


class ProductService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.repo = ProductRepository(session, merchant_id)
        self.inventory_repo = InventoryRepository(session, merchant_id)
        self.session = session
        self.merchant_id = merchant_id

    async def create_product(self, **kwargs: Any) -> Product:
        product = Product(merchant_id=self.merchant_id, **kwargs)
        product = await self.repo.create(product)
        inventory = Inventory(
            product_id=product.id,
            merchant_id=self.merchant_id,
            quantity=0,
        )
        await self.inventory_repo.create(inventory)
        logger.info("product_created", product_id=str(product.id), merchant_id=str(self.merchant_id))
        return product

    async def get_product(self, product_id: uuid.UUID) -> Product | None:
        return await self.repo.get_by_id(product_id)

    async def search_products(
        self,
        query: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        brand: str | None = None,
        in_stock_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Product], int]:
        products, total = await self.repo.search(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            brand=brand,
            in_stock_only=in_stock_only,
            limit=limit,
            offset=offset,
        )
        return list(products), total

    async def get_categories(self) -> list[str]:
        return await self.repo.get_categories()

    async def get_total_count(self) -> int:
        """Get total count of active products for merchant"""
        from sqlalchemy import select, func
        from app.models import Product
        
        stmt = select(func.count(Product.id)).where(
            Product.merchant_id == self.merchant_id,
            Product.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_effective_price(self, product: Product) -> float:
        return product.sale_price if product.sale_price is not None else product.base_price


class OrderService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.repo = OrderRepository(session, merchant_id)
        self.product_repo = ProductRepository(session, merchant_id)
        self.inventory_repo = InventoryRepository(session, merchant_id)
        self.session = session
        self.merchant_id = merchant_id

    async def create_order_from_cart(self, cart: Cart, customer_id: uuid.UUID | None = None) -> Order:
        # Query cart items directly to avoid stale relationship state in the identity map.
        from sqlalchemy import select
        from app.models import CartItem
        stmt = select(CartItem).where(CartItem.cart_id == cart.id)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        subtotal = sum(item.unit_price * item.quantity for item in items)

        order = Order(
            merchant_id=self.merchant_id,
            customer_id=customer_id,
            order_number=order_number,
            status=OrderStatus.CREATED,
            subtotal=subtotal,
            total=subtotal,
        )
        order = await self.repo.create(order)

        for cart_item in items:
            product = await self.product_repo.get_by_id(cart_item.product_id)
            if not product:
                raise ValueError(f"Product {cart_item.product_id} not found")

            order_item = OrderItem(
                order_id=order.id,
                merchant_id=self.merchant_id,
                product_id=cart_item.product_id,
                variant_id=cart_item.variant_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.unit_price * cart_item.quantity,
            )
            self.session.add(order_item)

            inv = await self.inventory_repo.get_by_product(cart_item.product_id)
            if inv:
                await self.inventory_repo.confirm_stock(cart_item.product_id, cart_item.quantity)

        was_abandoned = cart.status == CartStatus.ABANDONED
        cart.status = CartStatus.CONVERTED
        await self.session.flush()

        # Every order here is placed through a Sarthi-driven surface (AI buyer,
        # shop chat, or storefront checkout), so it's real AI-influenced revenue.
        # A cart that had gone ABANDONED and is now converting is a recovery.
        from app.services.growth import AttributionService, RecoveryService
        attribution = AttributionService(self.session, self.merchant_id)
        await attribution.attribute_order(
            order.id,
            attribution_type="recovery" if was_abandoned else "assisted",
        )

        if was_abandoned:
            recovery = RecoveryService(self.session, self.merchant_id)
            await recovery.mark_recovered_by_cart(cart.id, order)

        logger.info("order_created", order_id=str(order.id), order_number=order_number)
        return order

    async def get_order(self, order_id: uuid.UUID) -> Order | None:
        return await self.repo.get_with_items(order_id)

    async def update_order_status(self, order_id: uuid.UUID, status: OrderStatus) -> Order | None:
        order = await self.repo.get_by_id(order_id)
        if not order:
            return None
        return await self.repo.update(order, status=status)

    async def get_revenue_stats(self) -> dict[str, float]:
        return await self.repo.get_revenue_stats()


class CartService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.repo = CartRepository(session, merchant_id)
        self.product_repo = ProductRepository(session, merchant_id)
        self.inventory_repo = InventoryRepository(session, merchant_id)
        self.session = session
        self.merchant_id = merchant_id

    async def get_or_create_cart(self, session_id: str, customer_id: uuid.UUID | None = None) -> Cart:
        cart = await self.repo.get_active_by_session(session_id)
        if cart:
            return cart

        cart = Cart(
            merchant_id=self.merchant_id,
            customer_id=customer_id,
            session_id=session_id,
            status=CartStatus.ACTIVE,
        )
        return await self.repo.create(cart)

    async def add_item(
        self,
        cart: Cart,
        product_id: uuid.UUID,
        variant_id: uuid.UUID | None = None,
        quantity: int = 1,
    ) -> Cart:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        if not product.is_active:
            raise ValueError(f"Product {product_id} is not active")

        inv = await self.inventory_repo.get_by_product(product_id)
        if not inv or not inv.is_in_stock:
            raise ValueError(f"Product {product_id} is out of stock")

        price = product.sale_price if product.sale_price is not None else product.base_price

        existing = None
        cart_with_items = await self.repo.get_with_items(cart.id)
        if cart_with_items:
            for item in cart_with_items.items:
                if item.product_id == product_id and item.variant_id == variant_id:
                    existing = item
                    break

        if existing:
            existing.quantity += quantity
        else:
            item = CartItem(
                cart_id=cart.id,
                merchant_id=self.merchant_id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=price,
            )
            self.session.add(item)

        await self.session.flush()
        await self._recalculate_cart(cart)
        logger.info("cart_item_added", cart_id=str(cart.id), product_id=str(product_id))
        return cart

    async def remove_item(self, cart: Cart, item_id: uuid.UUID) -> Cart:
        cart_with_items = await self.repo.get_with_items(cart.id)
        if not cart_with_items:
            raise ValueError("Cart not found")

        for item in cart_with_items.items:
            if item.id == item_id:
                await self.session.delete(item)
                break

        await self.session.flush()
        await self._recalculate_cart(cart)
        return cart

    async def get_cart(self, cart_id: uuid.UUID) -> Cart | None:
        return await self.repo.get_with_items(cart_id)

    async def _recalculate_cart(self, cart: Cart) -> None:
        from sqlalchemy import select
        from app.models import CartItem
        stmt = select(CartItem).where(CartItem.cart_id == cart.id)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        cart.subtotal = sum(item.unit_price * item.quantity for item in items)
        await self.session.flush()
