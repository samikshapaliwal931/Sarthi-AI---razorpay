from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, get_current_auth
from app.database import get_db
from app.recommendations import RecommendationEngine
from app.schemas import RecommendationRequest, RecommendationResponse, RecommendationListResponse, ProductResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """Get all recommendations for the merchant"""
    from app.repositories import RecommendationRepository
    
    repo = RecommendationRepository(db, uuid.UUID(auth.merchant_id))
    recs = await repo.get_all(limit=50)
    
    return [
        RecommendationResponse(
            id=rec.id,
            product_id=rec.product_id,
            recommendation_type=rec.recommendation_type,
            score=rec.score,
            score_components=rec.score_components,
        )
        for rec in recs
    ]


@router.post("", response_model=RecommendationListResponse)
async def get_recommendations(
    body: RecommendationRequest,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> RecommendationListResponse:
    engine = RecommendationEngine(db, uuid.UUID(auth.merchant_id))
    recs = await engine.get_recommendations(
        session_id=body.session_id,
        product_id=body.product_id,
        customer_id=body.customer_id,
        context=body.context,
        limit=body.limit,
    )

    recommendations = []
    for rec in recs:
        product = rec["product"]
        recommendations.append(RecommendationResponse(
            id=rec["recommendation"].id,
            product_id=product.id,
            product=ProductResponse.model_validate(product),
            recommendation_type=rec["type"],
            score=rec["score"],
            score_components=rec.get("components"),
        ))

    cross_sell = []
    if recs:
        cart_ids = [r["product_id"] for r in recs[:2]]
        cs_recs = await engine.get_cross_sell(
            body.session_id,
            cart_ids,
            body.customer_id,
            limit=3,
        )
        for rec in cs_recs:
            product = rec["product"]
            cross_sell.append(RecommendationResponse(
                id=rec["recommendation"].id,
                product_id=product.id,
                product=ProductResponse.model_validate(product),
                recommendation_type=rec["type"],
                score=rec["score"],
            ))

    return RecommendationListResponse(
        recommendations=recommendations,
        session_id=body.session_id,
        cross_sell=cross_sell,
    )


@router.post("/events", status_code=201)
async def record_recommendation_event(
    recommendation_id: uuid.UUID,
    event_type: str,
    auth: AuthContext = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    from app.models import RecommendationEvent, RecommendationStatus, Recommendation
    from app.repositories import RecommendationRepository

    rec_repo = RecommendationRepository(db, uuid.UUID(auth.merchant_id))
    rec = await rec_repo.get_by_id(recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    status_map = {
        "shown": RecommendationStatus.SHOWN,
        "clicked": RecommendationStatus.CLICKED,
        "accepted": RecommendationStatus.ACCEPTED,
        "rejected": RecommendationStatus.REJECTED,
    }
    if event_type in status_map:
        await rec_repo.update(rec, status=status_map[event_type])

    event = RecommendationEvent(
        merchant_id=uuid.UUID(auth.merchant_id),
        recommendation_id=recommendation_id,
        event_type=event_type,
        product_id=rec.product_id,
    )
    db.add(event)
    await db.flush()

    return {"status": "recorded", "event_type": event_type}
