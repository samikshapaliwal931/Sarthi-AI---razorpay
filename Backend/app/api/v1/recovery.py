import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import get_current_auth, AuthContext
from app.audit import AuditService
from app.models import RecoveryCase, RecoveryCaseStatus
from app.schemas import RecoveryCaseResponse, RecoveryInterventionRequest

router = APIRouter(prefix="/recovery", tags=["recovery"])


def _to_response(case: RecoveryCase) -> RecoveryCaseResponse:
    return RecoveryCaseResponse(
        id=str(case.id),
        merchant_id=str(case.merchant_id),
        customer_id=str(case.customer_id) if case.customer_id else None,
        order_id=str(case.order_id) if case.order_id else None,
        cart_id=str(case.cart_id) if case.cart_id else None,
        case_type=case.case_type,
        status=case.status.value,
        potential_value=float(case.potential_value),
        recovered_value=float(case.recovered_value),
        intervention_type=case.intervention_type,
        created_at=case.created_at.isoformat(),
        updated_at=case.updated_at.isoformat() if case.updated_at else None,
    )


@router.post("/detect", response_model=list[RecoveryCaseResponse])
async def detect_recovery_cases(
    db: AsyncSession = Depends(get_db),
    current_user: AuthContext = Depends(get_current_auth),
):
    """Scan abandoned carts and failed payments for new (deduped) recovery cases."""
    from app.agents import record_agent_run
    from app.services.growth import RecoveryService

    merchant_id = uuid.UUID(current_user.merchant_id)
    service = RecoveryService(db, merchant_id)
    new_cases = await service.detect_cases()

    await record_agent_run(
        db, merchant_id,
        agent_type="recovery_agent",
        agent_name="Recovery Agent",
        output_data={
            "cases_found": len(new_cases),
            "total_potential_value": sum(c.potential_value for c in new_cases),
        },
    )

    return [_to_response(c) for c in new_cases]


@router.post("/{case_id}/send-intervention", response_model=RecoveryCaseResponse)
async def send_intervention(
    case_id: uuid.UUID,
    body: RecoveryInterventionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthContext = Depends(get_current_auth),
):
    """Send the bounded recovery action (reminder / retry prompt) for one case."""
    from app.services.growth import RecoveryService

    merchant_id = uuid.UUID(current_user.merchant_id)
    service = RecoveryService(db, merchant_id)
    try:
        case = await service.send_intervention(case_id, body.intervention_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    audit = AuditService(db, merchant_id)
    await audit.record(
        actor_type="merchant",
        actor_id=current_user.user_id,
        action="recovery_intervention_sent",
        decision="sent",
        input_data={"case_id": str(case_id), "intervention_type": body.intervention_type},
    )

    return _to_response(case)


@router.get("", response_model=list[RecoveryCaseResponse])
async def list_recovery_cases(
    db: AsyncSession = Depends(get_db),
    current_user: AuthContext = Depends(get_current_auth),
):
    """List all recovery cases for the current merchant"""
    query = (
        select(RecoveryCase)
        .where(RecoveryCase.merchant_id == current_user.merchant_id)
        .order_by(RecoveryCase.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    cases = result.scalars().all()

    return [_to_response(case) for case in cases]


@router.get("/{case_id}", response_model=RecoveryCaseResponse)
async def get_recovery_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AuthContext = Depends(get_current_auth),
):
    """Get a specific recovery case by ID"""
    query = select(RecoveryCase).where(
        RecoveryCase.id == case_id,
        RecoveryCase.merchant_id == current_user.merchant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    return _to_response(case)
