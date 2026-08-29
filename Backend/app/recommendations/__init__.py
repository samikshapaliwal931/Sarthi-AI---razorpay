from __future__ import annotations

import math
import uuid
from typing import Any

import structlog
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import (
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Recommendation,
    RecommendationEvent,
    RecommendationStatus,
)
from app.repositories import ProductRepository, InventoryRepository

logger = structlog.get_logger()


class RecommendationEngine:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.product_repo = ProductRepository(session, merchant_id)
        self.inventory_repo = InventoryRepository(session, merchant_id)
        self.weights = settings.recommendation_weights

    async def get_recommendations(
        self,
        session_id: str,
        product_id: uuid.UUID | None = None,
        customer_id: uuid.UUID | None = None,
        context: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        candidates = await self._generate_candidates(product_id, context)

        if not candidates:
            all_products, _ = await self.product_repo.search(in_stock_only=True, limit=limit * 3)
            candidates = [
                {"product_id": p.id, "product": p, "score": 0.5, "type": "popularity"}
                for p in all_products
            ]

        scored = await self._score_candidates(candidates, product_id, context)
        scored.sort(key=lambda x: x["score"], reverse=True)

        seen_products = set()
        if product_id:
            seen_products.add(product_id)

        results = []
        for item in scored:
            pid = item["product_id"]
            if pid in seen_products:
                continue
            seen_products.add(pid)

            product = item.get("product")
            if not product:
                products = await self.product_repo.get_by_ids([pid])
                if not products:
                    continue
                product = products[0]
                item["product"] = product

            if not product.is_active:
                continue

            inv = await self.inventory_repo.get_by_product(pid)
            if not inv or not inv.is_in_stock:
                continue

            results.append(item)
            if len(results) >= limit:
                break

        recs = []
        for item in results:
            rec = Recommendation(
                merchant_id=self.merchant_id,
                customer_id=customer_id,
                session_id=session_id,
                product_id=item["product_id"],
                recommendation_type=item.get("type", "hybrid"),
                score=item["score"],
                score_components=item.get("components"),
                context=context,
                status=RecommendationStatus.SHOWN,
            )
            self.session.add(rec)
            recs.append({
                "recommendation": rec,
                "product": item["product"],
                "score": item["score"],
                "components": item.get("components"),
                "type": item.get("type", "hybrid"),
            })

        await self.session.flush()
        return recs

    async def get_cross_sell(
        self,
        session_id: str,
        cart_product_ids: list[uuid.UUID],
        customer_id: uuid.UUID | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        if not cart_product_ids:
            return []

        cooccurrence = await self._get_cooccurrence(cart_product_ids)
        category_related = await self._get_category_related(cart_product_ids)

        candidates = {}
        for pid, score in cooccurrence.items():
            if pid not in cart_product_ids:
                candidates[pid] = {"score": score * 0.6, "type": "frequently_bought_together"}

        for pid, score in category_related.items():
            if pid not in cart_product_ids and pid not in candidates:
                candidates[pid] = {"score": score * 0.4, "type": "category_related"}

        if not candidates:
            return []

        product_ids = list(candidates.keys())[:limit * 2]
        products = await self.product_repo.get_by_ids(product_ids)
        product_map = {p.id: p for p in products}

        inventory_map = await self.inventory_repo.bulk_get_by_products(product_ids)

        results = []
        for pid, info in sorted(candidates.items(), key=lambda x: x[1]["score"], reverse=True):
            product = product_map.get(pid)
            if not product or not product.is_active:
                continue
            inv = inventory_map.get(pid)
            if not inv or not inv.is_in_stock:
                continue

            rec = Recommendation(
                merchant_id=self.merchant_id,
                customer_id=customer_id,
                session_id=session_id,
                product_id=pid,
                recommendation_type=info["type"],
                score=info["score"],
                status=RecommendationStatus.SHOWN,
            )
            self.session.add(rec)
            results.append({
                "recommendation": rec,
                "product": product,
                "score": info["score"],
                "type": info["type"],
            })
            if len(results) >= limit:
                break

        await self.session.flush()
        return results

    async def _generate_candidates(
        self,
        product_id: uuid.UUID | None,
        context: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

        if product_id:
            cooc = await self._get_cooccurrence([product_id])
            for pid, score in cooc.items():
                if pid != product_id:
                    candidates.append({
                        "product_id": pid,
                        "score": score,
                        "type": "frequently_bought_together",
                    })

            cat_related = await self._get_category_related([product_id])
            for pid, score in cat_related.items():
                if pid != product_id and pid not in [c["product_id"] for c in candidates]:
                    candidates.append({
                        "product_id": pid,
                        "score": score,
                        "type": "category_related",
                    })

        category = (context or {}).get("category")
        if category:
            products, _ = await self.product_repo.search(
                category=category, in_stock_only=True, limit=20
            )
            for p in products:
                if not any(c["product_id"] == p.id for c in candidates):
                    candidates.append({
                        "product_id": p.id,
                        "product": p,
                        "score": 0.5,
                        "type": "category",
                    })

        return candidates

    async def _score_candidates(
        self,
        candidates: list[dict[str, Any]],
        source_product_id: uuid.UUID | None,
        context: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        product_ids = [c["product_id"] for c in candidates]
        inventory_map = await self.inventory_repo.bulk_get_by_products(product_ids)

        popularity_scores = await self._get_popularity_scores(product_ids)

        for candidate in candidates:
            pid = candidate["product_id"]
            components = {}

            components["purchase_affinity"] = candidate.get("score", 0) * self.weights.get("purchase_affinity", 0.2)

            pop = popularity_scores.get(pid, 0)
            components["popularity"] = pop * self.weights.get("popularity", 0.15)

            inv = inventory_map.get(pid)
            if inv:
                stock_ratio = min(1.0, inv.available / max(1, inv.low_stock_threshold * 5))
                components["inventory_signal"] = stock_ratio * self.weights.get("inventory_signal", 0.1)
            else:
                components["inventory_signal"] = 0

            components["margin_signal"] = 0.5 * self.weights.get("margin_signal", 0.15)
            components["contextual_relevance"] = 0.5 * self.weights.get("contextual_relevance", 0.1)
            components["semantic_similarity"] = 0.5 * self.weights.get("semantic_similarity", 0.25)

            candidate["score"] = sum(components.values())
            candidate["components"] = components

        return candidates

    async def _get_cooccurrence(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
        if not product_ids:
            return {}

        stmt = (
            select(
                OrderItem.product_id,
                func.count(OrderItem.id).label("co_count"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.merchant_id == self.merchant_id,
                Order.status == OrderStatus.PAID,
                OrderItem.order_id.in_(
                    select(OrderItem.order_id).where(
                        OrderItem.product_id.in_(product_ids),
                        OrderItem.merchant_id == self.merchant_id,
                    )
                ),
                ~OrderItem.product_id.in_(product_ids),
            )
            .group_by(OrderItem.product_id)
            .order_by(func.count(OrderItem.id).desc())
            .limit(50)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return {}

        max_count = max(r.co_count for r in rows)
        return {r.product_id: r.co_count / max_count for r in rows}

    async def _get_category_related(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
        products = await self.product_repo.get_by_ids(product_ids)
        if not products:
            return {}

        categories = {p.category for p in products if p.category}
        if not categories:
            return {}

        stmt = (
            select(Product.id)
            .where(
                Product.merchant_id == self.merchant_id,
                Product.is_active == True,
                Product.category.in_(categories),
                ~Product.id.in_(product_ids),
            )
            .limit(30)
        )
        result = await self.session.execute(stmt)
        related_ids = [r[0] for r in result.all()]

        return {pid: 0.6 for pid in related_ids}

    async def _get_popularity_scores(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
        if not product_ids:
            return {}

        stmt = (
            select(
                OrderItem.product_id,
                func.count(OrderItem.id).label("purchase_count"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.merchant_id == self.merchant_id,
                Order.status == OrderStatus.PAID,
                OrderItem.product_id.in_(product_ids),
            )
            .group_by(OrderItem.product_id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return {pid: 0.0 for pid in product_ids}

        max_count = max(r.purchase_count for r in rows)
        scores = {r.product_id: r.purchase_count / max_count for r in rows}

        for pid in product_ids:
            scores.setdefault(pid, 0.0)

        return scores
