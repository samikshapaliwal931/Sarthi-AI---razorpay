from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_dict, utcnow
from app.models import AuditEvent

logger = structlog.get_logger()


class AuditService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id

    async def record(
        self,
        actor_type: str,
        actor_id: str,
        action: str,
        decision: str | None = None,
        policy_result: str | None = None,
        agent_run_id: uuid.UUID | None = None,
        approval_id: uuid.UUID | None = None,
        execution_result: str | None = None,
        error: str | None = None,
        correlation_id: str | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            merchant_id=self.merchant_id,
            actor_type=actor_type,
            actor_id=actor_id,
            agent_run_id=agent_run_id,
            action=action,
            input_hash=hash_dict(input_data) if input_data else None,
            decision=decision,
            policy_result=policy_result,
            approval_id=approval_id,
            execution_result=execution_result,
            error=error,
            correlation_id=correlation_id,
        )
        self.session.add(event)
        await self.session.flush()

        logger.info(
            "audit_event_recorded",
            action=action,
            actor_type=actor_type,
            merchant_id=str(self.merchant_id),
        )
        return event
