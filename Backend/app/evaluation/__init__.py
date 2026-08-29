from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    LearningEvent,
    ModelEvaluation,
    ModelFeedback,
    Recommendation,
    RecommendationEvent,
    RecommendationStatus,
    RevenueAttribution,
)
from app.repositories import LearningEventRepository, ModelEvaluationRepository

logger = structlog.get_logger()


class EvaluationService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.eval_repo = ModelEvaluationRepository(session, merchant_id)

    async def run_evaluation(self, evaluation_type: str = "recommendation") -> dict[str, Any]:
        metrics = await self._calculate_metrics()

        evaluation = ModelEvaluation(
            merchant_id=self.merchant_id,
            evaluation_type=evaluation_type,
            model_name="hybrid_recommender_v1",
            metrics=metrics,
        )
        self.session.add(evaluation)
        await self.session.flush()

        logger.info(
            "evaluation_completed",
            type=evaluation_type,
            merchant_id=str(self.merchant_id),
            metrics=metrics,
        )

        return metrics

    async def _calculate_metrics(self) -> dict[str, Any]:
        total_recs = await self._count_recommendations()
        shown = await self._count_recommendations_by_status(RecommendationStatus.SHOWN)
        clicked = await self._count_recommendations_by_status(RecommendationStatus.CLICKED)
        accepted = await self._count_recommendations_by_status(RecommendationStatus.ACCEPTED)

        ctr = clicked / max(1, shown)
        atr = accepted / max(1, shown)

        from app.repositories import RevenueAttributionRepository
        attr_repo = RevenueAttributionRepository(self.session, self.merchant_id)
        attributed_revenue = await attr_repo.get_total_attributed()

        return {
            "total_recommendations": total_recs,
            "impressions": shown,
            "clicks": clicked,
            "accepted": accepted,
            "click_through_rate": round(ctr, 4),
            "acceptance_rate": round(atr, 4),
            "attributed_revenue": attributed_revenue,
        }

    async def _count_recommendations(self) -> int:
        stmt = select(func.count(Recommendation.id)).where(
            Recommendation.merchant_id == self.merchant_id
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def _count_recommendations_by_status(self, status: RecommendationStatus) -> int:
        stmt = select(func.count(Recommendation.id)).where(
            Recommendation.merchant_id == self.merchant_id,
            Recommendation.status == status,
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())


class LearningService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.learning_repo = LearningEventRepository(session, merchant_id)

    async def record_learning_event(
        self,
        event_type: str,
        source_id: str | None = None,
        parameters_before: dict[str, Any] | None = None,
        parameters_after: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
        promoted: bool = False,
    ) -> LearningEvent:
        event = LearningEvent(
            merchant_id=self.merchant_id,
            event_type=event_type,
            source_id=source_id,
            parameters_before=parameters_before,
            parameters_after=parameters_after,
            metrics=metrics,
            promoted=promoted,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def update_ranking_weights(
        self,
        new_weights: dict[str, float],
        evaluation_metrics: dict[str, Any],
    ) -> LearningEvent:
        from app.config import settings
        old_weights = settings.recommendation_weights.copy()

        should_promote = (
            evaluation_metrics.get("click_through_rate", 0) > 0.05
            and evaluation_metrics.get("attributed_revenue", 0) > 0
        )

        event = await self.record_learning_event(
            event_type="weight_update",
            parameters_before=old_weights,
            parameters_after=new_weights,
            metrics=evaluation_metrics,
            promoted=should_promote,
        )

        logger.info(
            "ranking_weights_evaluated",
            promoted=should_promote,
            merchant_id=str(self.merchant_id),
        )

        return event

    async def get_learning_history(self, limit: int = 20) -> list[LearningEvent]:
        events = await self.learning_repo.get_all(limit=limit)
        return list(events)
