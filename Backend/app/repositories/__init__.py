from __future__ import annotations

import uuid
from typing import Any, Sequence

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Product,
    ProductVariant,
    Inventory,
    Customer,
    Order,
    OrderItem,
    Cart,
    CartItem,
    Payment,
    PaymentAttempt,
    AbandonedCart,
    Opportunity,
    OpportunityEvidence,
    Recommendation,
    RecommendationEvent,
    Campaign,
    CampaignVariant,
    Experiment,
    ExperimentAssignment,
    Agent,
    AgentRun,
    AgentDecision,
    AgentAction,
    Policy,
    PolicyEvaluation,
    Approval,
    AuditEvent,
    RevenueAttribution,
    RecoveryCase,
    WebhookEvent,
    Merchant,
    MerchantSettings,
    LearningEvent,
    ModelEvaluation,
    ModelFeedback,
)
from app.repositories.base import BaseRepository


class MerchantRepository(BaseRepository[Merchant]):
    model = Merchant

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.merchant_id = uuid.UUID(int=0)

    async def get_by_email(self, email: str) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: uuid.UUID) -> Merchant | None:
        stmt = select(Merchant).where(Merchant.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _base_query(self):
        return select(Merchant)


class MerchantSettingsRepository(BaseRepository[MerchantSettings]):
    model = MerchantSettings

    async def get_by_merchant(self) -> MerchantSettings | None:
        stmt = select(MerchantSettings).where(
            MerchantSettings.merchant_id == self.merchant_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ProductRepository(BaseRepository[Product]):
    model = Product

    async def search(
        self,
        query: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        brand: str | None = None,
        in_stock_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Product], int]:
        stmt = self._base_query().where(Product.is_active == True)

        if query:
            like = f"%{query}%"
            stmt = stmt.where(or_(
                Product.name.ilike(like),
                Product.description.ilike(like),
                Product.category.ilike(like),
                Product.brand.ilike(like),
            ))
        if category:
            stmt = stmt.where(Product.category.ilike(f"%{category}%"))
        if min_price is not None:
            price_col = func.coalesce(Product.sale_price, Product.base_price)
            stmt = stmt.where(price_col >= min_price)
        if max_price is not None:
            price_col = func.coalesce(Product.sale_price, Product.base_price)
            stmt = stmt.where(price_col <= max_price)
        if brand:
            stmt = stmt.where(Product.brand.ilike(f"%{brand}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        if in_stock_only:
            stmt = stmt.join(Inventory, and_(
                Inventory.product_id == Product.id,
                Inventory.merchant_id == self.merchant_id,
                Inventory.quantity > Inventory.reserved,
            ))

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def get_categories(self) -> list[str]:
        stmt = (
            select(Product.category)
            .where(Product.merchant_id == self.merchant_id, Product.is_active == True)
            .distinct()
        )
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_by_ids(self, ids: list[uuid.UUID]) -> Sequence[Product]:
        stmt = self._base_query().where(Product.id.in_(ids))
        result = await self.session.execute(stmt)
        return result.scalars().all()


class InventoryRepository(BaseRepository[Inventory]):
    model = Inventory

    async def get_by_product(self, product_id: uuid.UUID) -> Inventory | None:
        stmt = self._base_query().where(Inventory.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_get_by_products(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, Inventory]:
        stmt = self._base_query().where(Inventory.product_id.in_(product_ids))
        result = await self.session.execute(stmt)
        return {inv.product_id: inv for inv in result.scalars().all()}

    async def reserve_stock(self, product_id: uuid.UUID, quantity: int) -> bool:
        inv = await self.get_by_product(product_id)
        if not inv or inv.available < quantity:
            return False
        inv.reserved += quantity
        await self.session.flush()
        return True

    async def release_stock(self, product_id: uuid.UUID, quantity: int) -> None:
        inv = await self.get_by_product(product_id)
        if inv:
            inv.reserved = max(0, inv.reserved - quantity)
            await self.session.flush()

    async def confirm_stock(self, product_id: uuid.UUID, quantity: int) -> None:
        inv = await self.get_by_product(product_id)
        if inv:
            inv.quantity -= quantity
            inv.reserved = max(0, inv.reserved - quantity)
            await self.session.flush()


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    async def get_by_email(self, email: str) -> Customer | None:
        stmt = self._base_query().where(Customer.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def get_by_order_number(self, order_number: str) -> Order | None:
        stmt = self._base_query().where(Order.order_number == order_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_items(self, order_id: uuid.UUID) -> Order | None:
        stmt = (
            self._base_query()
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_revenue_stats(self) -> dict[str, float]:
        from app.models import OrderStatus
        stmt = select(
            func.count(Order.id).label("total_orders"),
            func.coalesce(func.sum(Order.total), 0).label("total_revenue"),
            func.coalesce(func.avg(Order.total), 0).label("avg_order_value"),
        ).where(
            Order.merchant_id == self.merchant_id,
            Order.status == OrderStatus.PAID,
        )
        result = await self.session.execute(stmt)
        row = result.one()
        return {
            "total_orders": row.total_orders or 0,
            "total_revenue": float(row.total_revenue or 0),
            "avg_order_value": float(row.avg_order_value or 0),
        }


class CartRepository(BaseRepository[Cart]):
    model = Cart

    async def get_active_by_session(self, session_id: str) -> Cart | None:
        from app.models import CartStatus
        stmt = (
            self._base_query()
            .options(selectinload(Cart.items))
            .where(Cart.session_id == session_id, Cart.status == CartStatus.ACTIVE)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_items(self, cart_id: uuid.UUID) -> Cart | None:
        stmt = (
            self._base_query()
            .options(selectinload(Cart.items))
            .where(Cart.id == cart_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def get_by_razorpay_payment_id(self, rzp_payment_id: str) -> Payment | None:
        stmt = self._base_query().where(Payment.razorpay_payment_id == rzp_payment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_order(self, order_id: uuid.UUID) -> Sequence[Payment]:
        stmt = self._base_query().where(Payment.order_id == order_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class OpportunityRepository(BaseRepository[Opportunity]):
    model = Opportunity

    async def get_with_evidence(self, opp_id: uuid.UUID) -> Opportunity | None:
        stmt = (
            self._base_query()
            .options(selectinload(Opportunity.evidence))
            .where(Opportunity.id == opp_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation


class RecommendationEventRepository(BaseRepository[RecommendationEvent]):
    model = RecommendationEvent


class CampaignRepository(BaseRepository[Campaign]):
    model = Campaign


class ExperimentRepository(BaseRepository[Experiment]):
    model = Experiment


class PolicyRepository(BaseRepository[Policy]):
    model = Policy

    async def get_active_policies(self) -> Sequence[Policy]:
        stmt = (
            self._base_query()
            .where(Policy.is_active == True)
            .order_by(Policy.priority.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PolicyEvaluationRepository(BaseRepository[PolicyEvaluation]):
    model = PolicyEvaluation


class ApprovalRepository(BaseRepository[Approval]):
    model = Approval

    async def get_pending(self) -> Sequence[Approval]:
        from app.models import ApprovalStatus
        stmt = self._base_query().where(Approval.status == ApprovalStatus.PENDING)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class AuditEventRepository(BaseRepository[AuditEvent]):
    model = AuditEvent

    async def get_recent(self, limit: int = 50) -> Sequence[AuditEvent]:
        stmt = (
            self._base_query()
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class RevenueAttributionRepository(BaseRepository[RevenueAttribution]):
    model = RevenueAttribution

    async def get_total_attributed(self) -> float:
        stmt = select(func.coalesce(func.sum(RevenueAttribution.attributed_amount), 0)).where(
            RevenueAttribution.merchant_id == self.merchant_id
        )
        result = await self.session.execute(stmt)
        return float(result.scalar_one())

    async def get_total_attributed_by_type(self, attribution_type: str) -> float:
        stmt = select(func.coalesce(func.sum(RevenueAttribution.attributed_amount), 0)).where(
            RevenueAttribution.merchant_id == self.merchant_id,
            RevenueAttribution.attribution_type == attribution_type,
        )
        result = await self.session.execute(stmt)
        return float(result.scalar_one())


class RecoveryCaseRepository(BaseRepository[RecoveryCase]):
    model = RecoveryCase


class WebhookEventRepository(BaseRepository[WebhookEvent]):
    model = WebhookEvent

    async def get_by_razorpay_event_id(self, event_id: str) -> WebhookEvent | None:
        stmt = select(WebhookEvent).where(WebhookEvent.razorpay_event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AgentRunRepository(BaseRepository[AgentRun]):
    model = AgentRun


class AgentActionRepository(BaseRepository[AgentAction]):
    model = AgentAction


class AgentRepository(BaseRepository[Agent]):
    model = Agent


class LearningEventRepository(BaseRepository[LearningEvent]):
    model = LearningEvent


class ModelEvaluationRepository(BaseRepository[ModelEvaluation]):
    model = ModelEvaluation
