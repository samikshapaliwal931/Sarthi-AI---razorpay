from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import AuditService
from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.models import Campaign, CampaignStatus
from app.policies import PolicyEngine, PolicyDecision
from app.schemas import CampaignResponse, CampaignCreate, CampaignDecisionRequest

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    body: CampaignCreate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Create a new campaign"""
    campaign = Campaign(
        merchant_id=uuid.UUID(auth.merchant_id),
        name=body.name,
        campaign_type=body.campaign_type,
        budget=body.budget,
        config=body.config,
        status="draft",
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    
    return CampaignResponse.model_validate(campaign)


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    """Get all campaigns for the merchant"""
    from sqlalchemy import select
    
    query = (
        select(Campaign)
        .where(Campaign.merchant_id == uuid.UUID(auth.merchant_id))
        .order_by(Campaign.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    campaigns = result.scalars().all()
    
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.post("/{campaign_id}/decision", response_model=CampaignResponse)
async def decide_campaign(
    campaign_id: uuid.UUID,
    body: CampaignDecisionRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Merchant approves or rejects a draft campaign.

    Approval still passes the campaign's budget through the deterministic
    policy gate before it's allowed to go live — the merchant's sign-off is
    necessary but not sufficient to spend money outside configured limits.
    """
    from sqlalchemy import select

    merchant_id = uuid.UUID(auth.merchant_id)
    stmt = select(Campaign).where(Campaign.id == campaign_id, Campaign.merchant_id == merchant_id)
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.PENDING_APPROVAL):
        raise HTTPException(status_code=400, detail=f"Campaign already {campaign.status.value}")

    already_had_merchant_approval = campaign.status == CampaignStatus.PENDING_APPROVAL

    audit = AuditService(db, merchant_id)

    if body.action == "reject":
        campaign.status = CampaignStatus.REJECTED
        await db.flush()
        await audit.record(
            actor_type="merchant",
            actor_id=auth.user_id,
            action="campaign_rejected",
            decision="rejected",
            input_data={"campaign_id": str(campaign_id), "notes": body.notes},
        )
        return CampaignResponse.model_validate(campaign)

    if body.action != "approve":
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    engine = PolicyEngine(db, merchant_id)
    decision, reason, _evaluations = await engine.evaluate(
        action_type="create_campaign",
        input_data={"budget": campaign.budget, "amount": campaign.budget},
    )

    if decision == PolicyDecision.BLOCK:
        campaign.status = CampaignStatus.REJECTED
        await db.flush()
        await audit.record(
            actor_type="system",
            actor_id="policy_engine",
            action="campaign_blocked",
            decision="blocked",
            policy_result=reason,
            input_data={"campaign_id": str(campaign_id), "budget": campaign.budget},
        )
        raise HTTPException(status_code=400, detail=reason or "Blocked by policy")

    needs_second_look = decision == PolicyDecision.REQUIRES_APPROVAL and not already_had_merchant_approval

    if needs_second_look:
        # First pass and the policy engine wants explicit confirmation — pause
        # here rather than launching. A second "approve" call on this same
        # campaign (already_had_merchant_approval) is that confirmation.
        campaign.status = CampaignStatus.PENDING_APPROVAL
        await db.flush()
        await audit.record(
            actor_type="merchant",
            actor_id=auth.user_id,
            action="campaign_pending_approval",
            decision=campaign.status.value,
            policy_result=reason,
            input_data={"campaign_id": str(campaign_id), "budget": campaign.budget, "notes": body.notes},
        )
        return CampaignResponse.model_validate(campaign)

    # Cleared the policy gate (or the merchant just gave the confirming
    # approval) — actually launch it, not just mark it "approved" and leave
    # it sitting there.
    from app.core import utcnow
    campaign.status = CampaignStatus.RUNNING
    campaign.started_at = utcnow()
    await db.flush()
    await audit.record(
        actor_type="merchant",
        actor_id=auth.user_id,
        action="campaign_launched",
        decision=campaign.status.value,
        policy_result=reason,
        input_data={"campaign_id": str(campaign_id), "budget": campaign.budget, "notes": body.notes},
    )

    return CampaignResponse.model_validate(campaign)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Get a specific campaign"""
    from sqlalchemy import select
    
    query = (
        select(Campaign)
        .where(
            Campaign.id == campaign_id,
            Campaign.merchant_id == uuid.UUID(auth.merchant_id)
        )
    )
    result = await db.execute(query)
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return CampaignResponse.model_validate(campaign)
