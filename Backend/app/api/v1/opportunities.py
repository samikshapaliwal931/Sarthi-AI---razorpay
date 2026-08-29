from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import AuditService
from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.services.growth import GrowthAnalystService
from app.repositories import OpportunityRepository
from app.schemas import OpportunityResponse, OpportunityEvidenceResponse, OpportunityDecisionRequest
from app.models import OpportunityStatus

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _to_response(opp: Any) -> OpportunityResponse:
    return OpportunityResponse(
        id=opp.id,
        merchant_id=opp.merchant_id,
        type=opp.type.value,
        status=opp.status.value,
        title=opp.title,
        description=opp.description,
        expected_impact=opp.expected_impact,
        confidence=opp.confidence,
        risk=opp.risk,
        recommended_action=opp.recommended_action,
        required_approval=opp.required_approval,
        evidence=[
            OpportunityEvidenceResponse(
                id=e.id,
                evidence_type=e.evidence_type,
                metric_name=e.metric_name,
                metric_value=e.metric_value,
                baseline_value=e.baseline_value,
                description=e.description,
            )
            for e in opp.evidence
        ],
        created_at=opp.created_at,
        updated_at=opp.updated_at,
    )


@router.get("", response_model=list[OpportunityResponse])
async def list_opportunities(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[OpportunityResponse]:
    repo = OpportunityRepository(db, uuid.UUID(auth.merchant_id))
    opps = await repo.get_all(limit=50)

    results = []
    for opp in opps:
        opp_with_evidence = await repo.get_with_evidence(opp.id)
        if opp_with_evidence:
            results.append(_to_response(opp_with_evidence))
    return results


@router.post("/analyze", response_model=list[OpportunityResponse])
async def run_analysis(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[OpportunityResponse]:
    analyst = GrowthAnalystService(db, uuid.UUID(auth.merchant_id))
    opps = await analyst.analyze_opportunities()

    results = []
    for opp in opps:
        opp_with_evidence = await OpportunityRepository(db, uuid.UUID(auth.merchant_id)).get_with_evidence(opp.id)
        if opp_with_evidence:
            results.append(_to_response(opp_with_evidence))
    return results


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> OpportunityResponse:
    repo = OpportunityRepository(db, uuid.UUID(auth.merchant_id))
    opp = await repo.get_with_evidence(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return _to_response(opp)


@router.post("/{opportunity_id}/decision", response_model=OpportunityResponse)
async def decide_opportunity(
    opportunity_id: uuid.UUID,
    body: OpportunityDecisionRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> OpportunityResponse:
    """Merchant approves or rejects a proposed growth opportunity.

    This is the human-in-the-loop decision on an AI-*proposed* action (product
    manual §7): it does not itself move money. Any downstream action the
    opportunity implies (a campaign, a discount, a recovery message) must still
    pass through the deterministic policy gate (`POST /policies/evaluate`)
    before execution.
    """
    repo = OpportunityRepository(db, uuid.UUID(auth.merchant_id))
    opp = await repo.get_with_evidence(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    if opp.status not in (OpportunityStatus.DISCOVERED, OpportunityStatus.VALIDATED, OpportunityStatus.PROPOSED):
        raise HTTPException(status_code=400, detail=f"Opportunity already {opp.status.value}")

    if body.action == "approve":
        opp.status = OpportunityStatus.APPROVED
    elif body.action == "reject":
        opp.status = OpportunityStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    await db.flush()
    await db.refresh(opp)

    audit = AuditService(db, uuid.UUID(auth.merchant_id))
    await audit.record(
        actor_type="merchant",
        actor_id=auth.user_id,
        action=f"opportunity_{body.action}d",
        decision=opp.status.value,
        input_data={"opportunity_id": str(opportunity_id), "notes": body.notes},
    )

    return _to_response(opp)
