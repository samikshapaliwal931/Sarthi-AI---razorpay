from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.models import Agent, AgentRun
from app.schemas import AgentRunResponse

router = APIRouter(prefix="/agent-activity", tags=["agent-activity"])


@router.get("", response_model=list[AgentRunResponse])
async def list_agent_runs(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get all agent runs for the current merchant"""
    query = (
        select(AgentRun, Agent.name)
        .join(Agent, Agent.id == AgentRun.agent_id)
        .where(AgentRun.merchant_id == auth.merchant_id)
        .order_by(AgentRun.started_at.desc())
        .limit(50)
    )
    result = await db.execute(query)
    return [
        AgentRunResponse(
            id=run.id,
            agent_id=run.agent_id,
            agent_name=agent_name,
            merchant_id=run.merchant_id,
            status=run.status.value,
            input_data=run.input_data,
            output_data=run.output_data,
            error=run.error,
            tokens_used=run.tokens_used,
            model_used=run.model_used,
            duration_ms=run.duration_ms,
            correlation_id=run.correlation_id,
            started_at=run.started_at,
            completed_at=run.completed_at,
        )
        for run, agent_name in result.all()
    ]
