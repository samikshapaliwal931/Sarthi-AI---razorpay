from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import generate_uuid, utcnow
from app.models import (
    Opportunity,
    OpportunityEvidence,
    OpportunityStatus,
    OpportunityType,
    OrderStatus,
    CartStatus,
    RecoveryCase,
    RecoveryCaseStatus,
)
from app.repositories import (
    OpportunityRepository,
    OrderRepository,
    CartRepository,
    CustomerRepository,
    RevenueAttributionRepository,
    RecoveryCaseRepository,
)

logger = structlog.get_logger()


class GrowthAnalystService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.opp_repo = OpportunityRepository(session, merchant_id)
        self.order_repo = OrderRepository(session, merchant_id)
        self.cart_repo = CartRepository(session, merchant_id)
        self.customer_repo = CustomerRepository(session, merchant_id)

    async def _active_types(self) -> set[OpportunityType]:
        """Opportunity types that already have a live (undecided) finding.

        Re-running analysis shouldn't pile up duplicate near-identical
        opportunities every time it's called — one open finding per type is
        enough until the merchant decides on it or it goes stale.
        """
        from sqlalchemy import select
        stmt = select(Opportunity.type).where(
            Opportunity.merchant_id == self.merchant_id,
            Opportunity.status.in_([
                OpportunityStatus.DISCOVERED,
                OpportunityStatus.VALIDATED,
                OpportunityStatus.PROPOSED,
            ]),
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def analyze_opportunities(self) -> list[Opportunity]:
        import time
        t0 = time.monotonic()

        active_types = await self._active_types()
        opportunities: list[Opportunity] = []

        if OpportunityType.ABANDONED_CART not in active_types:
            ac_opp = await self._analyze_abandoned_carts()
            if ac_opp:
                opportunities.append(ac_opp)

        if OpportunityType.CROSS_SELL not in active_types:
            cs_opp = await self._analyze_cross_sell()
            if cs_opp:
                opportunities.append(cs_opp)

        if OpportunityType.UPSELL not in active_types:
            upsell_opp = await self._analyze_upsell()
            if upsell_opp:
                opportunities.append(upsell_opp)

        if OpportunityType.PAYMENT_RECOVERY not in active_types:
            recovery_opp = await self._analyze_payment_recovery()
            if recovery_opp:
                opportunities.append(recovery_opp)

        for opp in opportunities:
            await self.opp_repo.create(opp)

        from app.agents import record_agent_run
        await record_agent_run(
            self.session,
            self.merchant_id,
            agent_type="growth_analyst",
            agent_name="Growth Analyst",
            input_data={"active_types_skipped": [t.value for t in active_types]},
            output_data={
                "opportunities_found": len(opportunities),
                "types": [o.type.value for o in opportunities],
                "total_expected_impact": sum(o.expected_impact for o in opportunities),
            },
            duration_ms=int((time.monotonic() - t0) * 1000),
        )

        logger.info(
            "growth_analysis_complete",
            merchant_id=str(self.merchant_id),
            opportunities_found=len(opportunities),
            skipped_existing_types=len(active_types),
        )
        return opportunities

    async def _analyze_abandoned_carts(self) -> Opportunity | None:
        abandoned_count = await self.cart_repo.count(status=CartStatus.ABANDONED)
        if abandoned_count < 5:
            return None

        from sqlalchemy import select, func
        from app.models import Cart
        stmt = select(func.coalesce(func.sum(Cart.subtotal), 0)).where(
            Cart.merchant_id == self.merchant_id,
            Cart.status == CartStatus.ABANDONED,
        )
        result = await self.session.execute(stmt)
        total_value = float(result.scalar_one())

        if total_value <= 0:
            return None

        opp = Opportunity(
            merchant_id=self.merchant_id,
            type=OpportunityType.ABANDONED_CART,
            status=OpportunityStatus.DISCOVERED,
            title=f"Recover {abandoned_count} abandoned carts worth ₹{total_value:,.0f}",
            description=f"There are {abandoned_count} abandoned carts with a total value of ₹{total_value:,.0f}. Sending targeted recovery messages could recover 5-15% of this revenue.",
            expected_impact=total_value * 0.10,
            confidence=0.7,
            risk="low",
            recommended_action="Send personalized recovery messages with optional small discount",
            required_approval=True,
            policy_requirements={"max_discount_percent": 10},
        )
        self.session.add(opp)
        await self.session.flush()

        evidence = OpportunityEvidence(
            opportunity_id=opp.id,
            merchant_id=self.merchant_id,
            evidence_type="cart_analysis",
            metric_name="abandoned_cart_count",
            metric_value=float(abandoned_count),
            description=f"{abandoned_count} carts abandoned",
        )
        self.session.add(evidence)

        evidence2 = OpportunityEvidence(
            opportunity_id=opp.id,
            merchant_id=self.merchant_id,
            evidence_type="revenue_analysis",
            metric_name="abandoned_cart_value",
            metric_value=total_value,
            description=f"Total abandoned cart value: ₹{total_value:,.0f}",
        )
        self.session.add(evidence2)
        await self.session.flush()

        return opp

    async def _analyze_cross_sell(self) -> Opportunity | None:
        from sqlalchemy import select, func
        from app.models import OrderItem, Order
        stmt = (
            select(
                OrderItem.product_id,
                func.count(OrderItem.id).label("purchase_count"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.merchant_id == self.merchant_id,
                Order.status == OrderStatus.PAID,
            )
            .group_by(OrderItem.product_id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(10)
        )
        result = await self.session.execute(stmt)
        top_products = result.all()

        if len(top_products) < 2:
            return None

        opp = Opportunity(
            merchant_id=self.merchant_id,
            type=OpportunityType.CROSS_SELL,
            status=OpportunityStatus.DISCOVERED,
            title="Cross-sell opportunity on top products",
            description="Analysis of purchase patterns reveals cross-sell opportunities between frequently co-purchased products.",
            expected_impact=5000.0,
            confidence=0.6,
            risk="low",
            recommended_action="Enable AI-powered cross-sell recommendations at checkout",
            required_approval=False,
        )
        self.session.add(opp)
        await self.session.flush()

        for product_id, count in top_products[:3]:
            evidence = OpportunityEvidence(
                opportunity_id=opp.id,
                merchant_id=self.merchant_id,
                evidence_type="purchase_pattern",
                metric_name="product_purchase_count",
                metric_value=float(count),
                description=f"Product purchased {count} times",
                data_source=str(product_id),
            )
            self.session.add(evidence)

        await self.session.flush()
        return opp

    async def _analyze_upsell(self) -> Opportunity | None:
        stats = await self.order_repo.get_revenue_stats()
        aov = stats.get("avg_order_value", 0)
        if aov <= 0:
            return None

        opp = Opportunity(
            merchant_id=self.merchant_id,
            type=OpportunityType.UPSELL,
            status=OpportunityStatus.DISCOVERED,
            title=f"Increase AOV from ₹{aov:,.0f}",
            description=f"Current average order value is ₹{aov:,.0f}. Strategic upsell recommendations could increase AOV by 10-15%.",
            expected_impact=aov * 0.12 * stats.get("total_orders", 0) * 0.1,
            confidence=0.5,
            risk="low",
            recommended_action="Implement AI-powered upsell recommendations based on cart contents",
            required_approval=False,
        )
        self.session.add(opp)
        await self.session.flush()

        evidence = OpportunityEvidence(
            opportunity_id=opp.id,
            merchant_id=self.merchant_id,
            evidence_type="revenue_analysis",
            metric_name="current_aov",
            metric_value=aov,
            description=f"Current AOV: ₹{aov:,.0f}",
        )
        self.session.add(evidence)
        await self.session.flush()

        return opp

    async def _analyze_payment_recovery(self) -> Opportunity | None:
        from sqlalchemy import select, func
        from app.models import Payment, PaymentStatus
        stmt = select(func.count(Payment.id)).where(
            Payment.merchant_id == self.merchant_id,
            Payment.status == PaymentStatus.FAILED,
        )
        result = await self.session.execute(stmt)
        failed_count = int(result.scalar_one())

        if failed_count < 3:
            return None

        stmt2 = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.merchant_id == self.merchant_id,
            Payment.status == PaymentStatus.FAILED,
        )
        result2 = await self.session.execute(stmt2)
        failed_value = float(result2.scalar_one())

        opp = Opportunity(
            merchant_id=self.merchant_id,
            type=OpportunityType.PAYMENT_RECOVERY,
            status=OpportunityStatus.DISCOVERED,
            title=f"Recover {failed_count} failed payments worth ₹{failed_value:,.0f}",
            description=f"There are {failed_count} failed payment attempts totaling ₹{failed_value:,.0f}. Automated retry and alternative payment suggestions could recover 20-30% of failed payments.",
            expected_impact=failed_value * 0.25,
            confidence=0.65,
            risk="low",
            recommended_action="Implement smart payment retry with alternative payment method suggestions",
            required_approval=True,
        )
        self.session.add(opp)
        await self.session.flush()

        evidence = OpportunityEvidence(
            opportunity_id=opp.id,
            merchant_id=self.merchant_id,
            evidence_type="payment_analysis",
            metric_name="failed_payment_count",
            metric_value=float(failed_count),
            baseline_value=failed_value,
            description=f"{failed_count} failed payments totaling ₹{failed_value:,.0f}",
        )
        self.session.add(evidence)
        await self.session.flush()

        return opp


class AttributionService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.attribution_repo = RevenueAttributionRepository(session, merchant_id)

    async def attribute_order(
        self,
        order_id: uuid.UUID,
        recommendation_event_id: uuid.UUID | None = None,
        campaign_id: uuid.UUID | None = None,
        attribution_type: str = "direct",
        amount: float | None = None,
    ) -> None:
        from app.repositories import OrderRepository
        order_repo = OrderRepository(self.session, self.merchant_id)
        order = await order_repo.get_by_id(order_id)
        if not order:
            return

        from app.models import RevenueAttribution, AttributionType
        attr_type = AttributionType(attribution_type)
        total = amount or order.total

        attribution = RevenueAttribution(
            merchant_id=self.merchant_id,
            order_id=order_id,
            recommendation_event_id=recommendation_event_id,
            campaign_id=campaign_id,
            attribution_type=attr_type,
            attributed_amount=total,
            total_order_amount=total,
            confidence=1.0 if recommendation_event_id else 0.5,
        )
        self.session.add(attribution)
        await self.session.flush()

        logger.info(
            "revenue_attributed",
            order_id=str(order_id),
            amount=total,
            type=attribution_type,
        )

    async def get_total_attributed_revenue(self) -> float:
        return await self.attribution_repo.get_total_attributed()

    async def get_recovered_revenue(self) -> float:
        return await self.attribution_repo.get_total_attributed_by_type("recovery")


class RecoveryService:
    """Detects failed payments / abandoned carts and lets the merchant send a bounded intervention."""

    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.case_repo = RecoveryCaseRepository(session, merchant_id)

    async def _open_cart_ids(self) -> set[uuid.UUID]:
        from sqlalchemy import select
        stmt = select(RecoveryCase.cart_id).where(
            RecoveryCase.merchant_id == self.merchant_id,
            RecoveryCase.case_type == "abandoned_cart",
            RecoveryCase.status.notin_([RecoveryCaseStatus.RECOVERED, RecoveryCaseStatus.EXPIRED, RecoveryCaseStatus.FAILED]),
        )
        result = await self.session.execute(stmt)
        return {cid for cid in result.scalars().all() if cid is not None}

    async def _open_order_ids(self) -> set[uuid.UUID]:
        from sqlalchemy import select
        stmt = select(RecoveryCase.order_id).where(
            RecoveryCase.merchant_id == self.merchant_id,
            RecoveryCase.case_type == "payment_failure",
            RecoveryCase.status.notin_([RecoveryCaseStatus.RECOVERED, RecoveryCaseStatus.EXPIRED, RecoveryCaseStatus.FAILED]),
        )
        result = await self.session.execute(stmt)
        return {oid for oid in result.scalars().all() if oid is not None}

    async def detect_cases(self) -> list[RecoveryCase]:
        """Scan abandoned carts and failed payments for new recovery cases (deduped)."""
        from sqlalchemy import select
        from app.models import Cart, Payment, PaymentStatus

        new_cases: list[RecoveryCase] = []

        open_cart_ids = await self._open_cart_ids()
        cart_stmt = select(Cart).where(Cart.merchant_id == self.merchant_id, Cart.status == CartStatus.ABANDONED)
        cart_result = await self.session.execute(cart_stmt)
        for cart in cart_result.scalars().all():
            if cart.id in open_cart_ids or cart.subtotal <= 0:
                continue
            case = RecoveryCase(
                merchant_id=self.merchant_id,
                customer_id=cart.customer_id,
                cart_id=cart.id,
                case_type="abandoned_cart",
                status=RecoveryCaseStatus.DETECTED,
                potential_value=cart.subtotal,
            )
            self.session.add(case)
            new_cases.append(case)

        open_order_ids = await self._open_order_ids()
        payment_stmt = select(Payment).where(
            Payment.merchant_id == self.merchant_id, Payment.status == PaymentStatus.FAILED
        )
        payment_result = await self.session.execute(payment_stmt)
        for payment in payment_result.scalars().all():
            if payment.order_id in open_order_ids or payment.amount <= 0:
                continue
            case = RecoveryCase(
                merchant_id=self.merchant_id,
                order_id=payment.order_id,
                case_type="payment_failure",
                status=RecoveryCaseStatus.DETECTED,
                potential_value=payment.amount,
            )
            self.session.add(case)
            new_cases.append(case)

        await self.session.flush()
        for case in new_cases:
            await self.session.refresh(case)
        return new_cases

    async def send_intervention(self, case_id: uuid.UUID, intervention_type: str = "reminder_message") -> RecoveryCase:
        case = await self.case_repo.get_by_id(case_id)
        if not case:
            raise ValueError("Recovery case not found")
        if case.status not in (RecoveryCaseStatus.DETECTED, RecoveryCaseStatus.ANALYZING):
            raise ValueError(f"Case already {case.status.value}")

        case.status = RecoveryCaseStatus.INTERVENTION_SENT
        case.intervention_type = intervention_type
        case.intervention_data = {"sent_at": utcnow().isoformat()}

        if case.cart_id:
            from sqlalchemy import select
            from app.models import AbandonedCart
            stmt = select(AbandonedCart).where(AbandonedCart.cart_id == case.cart_id)
            result = await self.session.execute(stmt)
            abandoned = result.scalar_one_or_none()
            if abandoned:
                abandoned.recovery_sent = True

        await self.session.flush()
        await self.session.refresh(case)
        return case

    async def mark_recovered_by_cart(self, cart_id: uuid.UUID, order) -> None:
        """Called when an order is placed from a cart that had an open recovery case."""
        from sqlalchemy import select
        stmt = select(RecoveryCase).where(
            RecoveryCase.merchant_id == self.merchant_id,
            RecoveryCase.cart_id == cart_id,
            RecoveryCase.status.notin_([RecoveryCaseStatus.RECOVERED, RecoveryCaseStatus.EXPIRED, RecoveryCaseStatus.FAILED]),
        )
        result = await self.session.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            return

        case.status = RecoveryCaseStatus.RECOVERED
        case.recovered_value = order.total
        case.order_id = order.id

        from app.models import AbandonedCart
        ac_stmt = select(AbandonedCart).where(AbandonedCart.cart_id == cart_id)
        ac_result = await self.session.execute(ac_stmt)
        abandoned = ac_result.scalar_one_or_none()
        if abandoned:
            abandoned.recovered = True
            abandoned.recovered_order_id = order.id

        await self.session.flush()
