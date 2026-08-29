from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.policies import PolicyEngine, ApprovalService
from app.repositories import PolicyRepository, ApprovalRepository, AuditEventRepository
from app.schemas import (
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    ApprovalResponse,
    ApprovalAction,
    AuditEventResponse,
)
from app.audit import AuditService

router = APIRouter(tags=["policies"])


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[PolicyResponse]:
    repo = PolicyRepository(db, uuid.UUID(auth.merchant_id))
    policies = await repo.get_all(limit=100)
    return [PolicyResponse.model_validate(p) for p in policies]


@router.post("/policies", response_model=PolicyResponse, status_code=201)
async def create_policy(
    body: PolicyCreate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> PolicyResponse:
    from app.models import Policy
    policy = Policy(
        merchant_id=uuid.UUID(auth.merchant_id),
        name=body.name,
        policy_type=body.policy_type,
        rules=body.rules,
    )
    repo = PolicyRepository(db, uuid.UUID(auth.merchant_id))
    policy = await repo.create(policy)

    audit = AuditService(db, uuid.UUID(auth.merchant_id))
    await audit.record(
        actor_type="merchant",
        actor_id=auth.user_id,
        action="policy_created",
        input_data=body.model_dump(),
    )

    return PolicyResponse.model_validate(policy)


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> PolicyResponse:
    repo = PolicyRepository(db, uuid.UUID(auth.merchant_id))
    policy = await repo.get_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyResponse.model_validate(policy)


@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    body: PolicyUpdate,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> PolicyResponse:
    repo = PolicyRepository(db, uuid.UUID(auth.merchant_id))
    policy = await repo.get_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    updates = body.model_dump(exclude_unset=True)
    policy = await repo.update(policy, **updates)

    audit = AuditService(db, uuid.UUID(auth.merchant_id))
    await audit.record(
        actor_type="merchant",
        actor_id=auth.user_id,
        action="policy_updated",
        input_data={"policy_id": str(policy_id), **updates},
    )

    return PolicyResponse.model_validate(policy)


@router.post("/policies/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_policy(
    body: PolicyEvaluationRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> PolicyEvaluationResponse:
    engine = PolicyEngine(db, uuid.UUID(auth.merchant_id))
    decision, reason, evaluations = await engine.evaluate(
        action_type=body.action_type,
        input_data=body.input_data,
    )

    audit = AuditService(db, uuid.UUID(auth.merchant_id))
    await audit.record(
        actor_type="system",
        actor_id="policy_engine",
        action="policy_evaluation",
        decision=decision.value,
        policy_result=reason,
        input_data=body.model_dump(),
    )

    return PolicyEvaluationResponse(
        decision=decision.value,
        reason=reason,
        evaluations=[
            {
                "policy_id": str(e.policy_id),
                "decision": e.decision.value,
                "reason": e.reason,
            }
            for e in evaluations
        ],
    )

@router.get("/approvals", response_model=list[ApprovalResponse])
async def list_approvals(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[ApprovalResponse]:
    repo = ApprovalRepository(db, uuid.UUID(auth.merchant_id))
    approvals = await repo.get_pending()
    return [ApprovalResponse.model_validate(a) for a in approvals]


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
async def approve_action(
    approval_id: uuid.UUID,
    body: ApprovalAction,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    service = ApprovalService(db, uuid.UUID(auth.merchant_id))
    try:
        approval = await service.approve(approval_id, auth.user_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    audit = AuditService(db, uuid.UUID(auth.merchant_id))
    await audit.record(
        actor_type="merchant",
        actor_id=auth.user_id,
        action="approval_granted",
        decision="approved",
        approval_id=approval_id,
    )

    return ApprovalResponse.model_validate(approval)


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_action(
    approval_id: uuid.UUID,
    body: ApprovalAction,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    service = ApprovalService(db, uuid.UUID(auth.merchant_id))
    try:
        approval = await service.reject(approval_id, auth.user_id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    audit = AuditService(db, uuid.UUID(auth.merchant_id))
    await audit.record(
        actor_type="merchant",
        actor_id=auth.user_id,
        action="approval_rejected",
        decision="rejected",
        approval_id=approval_id,
    )

    return ApprovalResponse.model_validate(approval)


@router.get("/audit", response_model=list[AuditEventResponse])
async def get_audit_log(
    limit: int = 50,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[AuditEventResponse]:
    repo = AuditEventRepository(db, uuid.UUID(auth.merchant_id))
    events = await repo.get_recent(limit=limit)
    return [AuditEventResponse.model_validate(e) for e in events]
