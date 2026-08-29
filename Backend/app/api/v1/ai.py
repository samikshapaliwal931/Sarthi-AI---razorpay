from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth, get_optional_auth
from app.core import generate_uuid
from app.database import get_db
from app.agents.conversation import ConversationAgent
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    auth: AuthContext | None = Depends(get_optional_auth),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    if auth:
        merchant_id = uuid.UUID(auth.merchant_id)
    else:
        from app.models import Merchant
        from sqlalchemy import select
        stmt = select(Merchant).order_by(Merchant.created_at.asc()).limit(1)
        result = await db.execute(stmt)
        merchant = result.scalar_one_or_none()
        if not merchant:
            return ChatResponse(
                message="No merchant configured. Please set up a merchant first.",
                correlation_id=str(generate_uuid()),
            )
        merchant_id = merchant.id

    import time

    from app.agents import record_agent_run

    session_id = body.session_id or str(generate_uuid())
    correlation_id = str(generate_uuid())

    agent = ConversationAgent(db, merchant_id)
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    last_message = messages[-1]["content"] if messages else ""
    t0 = time.monotonic()

    try:
        result = await agent.handle_message(messages, session_id, body.context)
    except Exception as e:
        # If AI provider is not configured or fails, return a mock response
        error_msg = str(e)
        if "API key" in error_msg or "authentication" in error_msg.lower():
            await record_agent_run(
                db, merchant_id,
                agent_type="conversation",
                agent_name="Conversation Agent",
                status="failed",
                input_data={"message": last_message},
                error=error_msg,
                correlation_id=correlation_id,
                duration_ms=int((time.monotonic() - t0) * 1000),
            )
            return ChatResponse(
                message="I'm Sarthi, your AI revenue agent. I can help you discover revenue opportunities, analyze your catalog, and optimize your store's performance. What would you like to explore?",
                data={"demo_mode": True},
                actions=[],
                correlation_id=correlation_id,
            )
        raise

    await record_agent_run(
        db, merchant_id,
        agent_type="conversation",
        agent_name="Conversation Agent",
        input_data={"message": last_message, "intent": result.get("intent", {}).get("intent_type")},
        output_data={"message": result.get("message"), "has_data": result.get("data") is not None},
        correlation_id=correlation_id,
        duration_ms=int((time.monotonic() - t0) * 1000),
    )

    return ChatResponse(
        message=result.get("message", "I'm here to help."),
        data=result.get("data"),
        actions=result.get("actions", []),
        correlation_id=correlation_id,
    )
