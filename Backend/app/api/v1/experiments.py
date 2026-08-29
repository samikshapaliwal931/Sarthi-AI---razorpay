from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.models import Experiment
from app.schemas import ExperimentResponse

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentResponse]:
    """Get all experiments for the merchant"""
    from sqlalchemy import select
    
    query = (
        select(Experiment)
        .where(Experiment.merchant_id == uuid.UUID(auth.merchant_id))
        .order_by(Experiment.created_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    experiments = result.scalars().all()
    
    return [ExperimentResponse.model_validate(e) for e in experiments]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> ExperimentResponse:
    """Get a specific experiment"""
    from sqlalchemy import select
    
    query = (
        select(Experiment)
        .where(
            Experiment.id == experiment_id,
            Experiment.merchant_id == uuid.UUID(auth.merchant_id)
        )
    )
    result = await db.execute(query)
    experiment = result.scalar_one_or_none()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return ExperimentResponse.model_validate(experiment)
