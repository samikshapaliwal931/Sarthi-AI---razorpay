from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.services import OrderService
from app.services.growth import AttributionService
from app.repositories import (
    OpportunityRepository,
    ApprovalRepository,
    CampaignRepository,
    AuditEventRepository,
)
from app.schemas import (
    DashboardResponse,
    RevenueMetricsResponse,
    AuditEventResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    merchant_id = uuid.UUID(auth.merchant_id)

    order_service = OrderService(db, merchant_id)
    stats = await order_service.get_revenue_stats()

    attr_service = AttributionService(db, merchant_id)
    attributed = await attr_service.get_total_attributed_revenue()
    recovered = await attr_service.get_recovered_revenue()

    from app.models import Cart, CartStatus, Opportunity, OpportunityStatus, Approval, ApprovalStatus, Campaign, CampaignStatus
    total_carts = await _count(db, merchant_id, Cart)
    abandoned = await _count_filtered(db, merchant_id, Cart, Cart.status == CartStatus.ABANDONED)
    abandonment_rate = abandoned / max(1, total_carts)

    opp_repo = OpportunityRepository(db, merchant_id)
    active_opps = await opp_repo.count(status=OpportunityStatus.DISCOVERED)

    approval_repo = ApprovalRepository(db, merchant_id)
    pending_approvals = len(await approval_repo.get_pending())

    campaign_repo = CampaignRepository(db, merchant_id)
    active_campaigns = await campaign_repo.count(status=CampaignStatus.RUNNING)

    from app.models import Recommendation, RecommendationStatus
    total_recs = await _count(db, merchant_id, Recommendation)
    clicked_recs = await _count_filtered(db, merchant_id, Recommendation, Recommendation.status == RecommendationStatus.CLICKED)
    ctr = clicked_recs / max(1, total_recs)

    total_orders = int(stats.get("total_orders", 0))
    total_revenue = stats.get("total_revenue", 0)
    aov = stats.get("avg_order_value", 0)

    conversion_rate = 0.0
    if total_carts > 0:
        from app.models import CartStatus as CS
        converted = await _count_filtered(db, merchant_id, Cart, Cart.status == CS.CONVERTED)
        conversion_rate = converted / total_carts

    revenue_metrics = RevenueMetricsResponse(
        total_revenue=total_revenue,
        ai_attributed_revenue=attributed,
        recovered_revenue=recovered,
        average_order_value=aov,
        conversion_rate=round(conversion_rate, 4),
        cart_abandonment_rate=round(abandonment_rate, 4),
        recommendation_ctr=round(ctr, 4),
        total_orders=total_orders,
        period="all_time",
    )

    audit_repo = AuditEventRepository(db, merchant_id)
    recent_events = await audit_repo.get_recent(limit=10)

    return DashboardResponse(
        revenue_metrics=revenue_metrics,
        active_opportunities=active_opps + await opp_repo.count(status=OpportunityStatus.PROPOSED),
        pending_approvals=pending_approvals,
        active_campaigns=active_campaigns,
        recent_audit_events=[AuditEventResponse.model_validate(e) for e in recent_events],
    )


@router.get("/revenue", response_model=RevenueMetricsResponse)
async def get_revenue_metrics(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> RevenueMetricsResponse:
    merchant_id = uuid.UUID(auth.merchant_id)
    order_service = OrderService(db, merchant_id)
    stats = await order_service.get_revenue_stats()

    attr_service = AttributionService(db, merchant_id)
    attributed = await attr_service.get_total_attributed_revenue()
    recovered = await attr_service.get_recovered_revenue()

    return RevenueMetricsResponse(
        total_revenue=stats.get("total_revenue", 0),
        ai_attributed_revenue=attributed,
        recovered_revenue=recovered,
        average_order_value=stats.get("avg_order_value", 0),
        conversion_rate=0.0,
        cart_abandonment_rate=0.0,
        recommendation_ctr=0.0,
        total_orders=int(stats.get("total_orders", 0)),
        period="all_time",
    )


async def _count(db: AsyncSession, merchant_id: uuid.UUID, model) -> int:
    stmt = select(func.count(model.id)).where(model.merchant_id == merchant_id)
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def _count_filtered(db: AsyncSession, merchant_id: uuid.UUID, model, *conditions) -> int:
    from sqlalchemy import and_
    stmt = select(func.count(model.id)).where(
        and_(model.merchant_id == merchant_id, *conditions)
    )
    result = await db.execute(stmt)
    return int(result.scalar_one())
