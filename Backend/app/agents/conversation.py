from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import model_router
from app.models import Agent, AgentRun, AgentRunStatus, AgentDecision, AgentAction
from app.core import generate_uuid, utcnow, hash_dict

logger = structlog.get_logger()


class IntentAgent:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id

    async def extract_intent(self, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        prompt = f"""You are Sarthi, an AI commerce assistant. Analyze the user's message and extract structured intent.

User message: "{message}"

Context: {context or {}}

Extract the intent and return JSON with:
- intent_type: one of [search, cross_sell, add_to_cart, checkout, product_inquiry, general, growth_analysis, opportunity_query]
- entities: dict with extracted entities like category, price_range, product_name, quantity
- action: what action to take
- confidence: 0-1

Return ONLY valid JSON."""

        provider = model_router.get_provider()
        result = await provider.generate_structured(
            prompt,
            model=model_router.get_small_model(),
            temperature=0.1,
            max_tokens=500,
        )
        return result


class RetrievalAgent:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id

    async def retrieve_products(
        self,
        query: str | None = None,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        limit: int = 10,
        in_stock_only: bool = True,
    ) -> list[dict[str, Any]]:
        from app.services import ProductService
        from app.repositories import InventoryRepository
        
        product_service = ProductService(self.session, self.merchant_id)
        inventory_repo = InventoryRepository(self.session, self.merchant_id)

        products, total = await product_service.search_products(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            limit=limit,
        )

        result = []
        for p in products:
            inv = await inventory_repo.get_by_product(p.id)
            product_data = {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "subcategory": p.subcategory,
                "brand": p.brand,
                "price": p.sale_price or p.base_price,
                "currency": p.currency,
                "images": p.images,
                "tags": p.tags,
                "attributes": p.attributes,
                "in_stock": inv.is_in_stock if inv else True,
                "available_quantity": inv.available if inv else 0,
                "low_stock": inv.is_low_stock if inv else False,
            }
            result.append(product_data)

        return result
    
    async def get_product_details(self, product_id: uuid.UUID) -> dict[str, Any] | None:
        """Get detailed product information with inventory"""
        from app.services import ProductService
        from app.repositories import InventoryRepository
        
        product_service = ProductService(self.session, self.merchant_id)
        inventory_repo = InventoryRepository(self.session, self.merchant_id)
        
        product = await product_service.get_product(product_id)
        if not product:
            return None
        
        inv = await inventory_repo.get_by_product(product_id)
        
        return {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "subcategory": product.subcategory,
            "brand": product.brand,
            "price": product.sale_price or product.base_price,
            "currency": product.currency,
            "images": product.images,
            "tags": product.tags,
            "attributes": product.attributes,
            "in_stock": inv.is_in_stock if inv else True,
            "available_quantity": inv.available if inv else 0,
            "low_stock": inv.is_low_stock if inv else False,
        }
    
    async def get_catalog_summary(self) -> dict[str, Any]:
        """Get summary of merchant's catalog for AI context"""
        from app.services import ProductService
        from app.repositories import InventoryRepository
        from sqlalchemy import select, func
        from app.models import Product
        
        product_service = ProductService(self.session, self.merchant_id)
        
        # Get category counts
        stmt = select(Product.category, func.count(Product.id)).where(
            Product.merchant_id == self.merchant_id,
            Product.is_active == True
        ).group_by(Product.category)
        result = await self.session.execute(stmt)
        category_counts = {row[0]: row[1] for row in result.all()}
        
        # Get price range
        stmt = select(
            func.min(Product.base_price),
            func.max(Product.base_price),
            func.avg(Product.base_price)
        ).where(
            Product.merchant_id == self.merchant_id,
            Product.is_active == True
        )
        result = await self.session.execute(stmt)
        price_stats = result.one()
        
        # Get total products
        total_products = await product_service.get_total_count()
        
        return {
            "total_products": total_products,
            "categories": category_counts,
            "price_range": {
                "min": float(price_stats[0]) if price_stats[0] else 0,
                "max": float(price_stats[1]) if price_stats[1] else 0,
                "avg": float(price_stats[2]) if price_stats[2] else 0,
            },
            "category_list": list(category_counts.keys()),
        }


class GrowthAgent:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id

    async def analyze_and_propose(self) -> list[dict[str, Any]]:
        from app.services.growth import GrowthAnalystService
        analyst = GrowthAnalystService(self.session, self.merchant_id)
        opportunities = await analyst.analyze_opportunities()

        return [
            {
                "id": str(o.id),
                "type": o.type.value,
                "title": o.title,
                "description": o.description,
                "expected_impact": o.expected_impact,
                "confidence": o.confidence,
                "risk": o.risk,
                "recommended_action": o.recommended_action,
            }
            for o in opportunities
        ]


class ConversationAgent:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.intent_agent = IntentAgent(session, merchant_id)
        self.retrieval_agent = RetrievalAgent(session, merchant_id)

    async def handle_message(
        self,
        messages: list[dict[str, str]],
        session_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        last_message = messages[-1]["content"] if messages else ""

        # Get catalog context for better AI responses
        catalog_summary = await self.retrieval_agent.get_catalog_summary()

        intent = await self.intent_agent.extract_intent(last_message, context)
        intent_type = intent.get("intent_type", "general")
        entities = intent.get("entities", {})

        result: dict[str, Any] = {
            "intent": intent,
            "data": None,
            "actions": [],
            "message": "",
            "catalog_context": catalog_summary,
        }

        if intent_type == "search":
            search_query = (
                entities.get("product_name")
                or entities.get("query")
                or entities.get("category")
                or entities.get("search_term")
            )
            products = await self.retrieval_agent.retrieve_products(
                query=search_query,
                category=entities.get("category"),
                min_price=entities.get("min_price"),
                max_price=entities.get("max_price") or entities.get("price_max") or entities.get("budget"),
                in_stock_only=True,
            )
            result["data"] = {"products": products}
            result["message"] = self._format_product_results(products, catalog_summary)

        elif intent_type == "cross_sell":
            from app.recommendations import RecommendationEngine
            engine = RecommendationEngine(self.session, self.merchant_id)
            cart_ids = context.get("cart_product_ids", []) if context else []
            recs = await engine.get_cross_sell(session_id, cart_ids)
            result["data"] = {"recommendations": [
                {
                    "product_id": str(r["product"].id),
                    "name": r["product"].name,
                    "price": r["product"].sale_price or r["product"].base_price,
                    "score": r["score"],
                    "type": r["type"]
                }
                for r in recs
            ]}
            result["message"] = f"Based on your cart and our catalog of {catalog_summary['total_products']} products, you might also like these items."

        elif intent_type == "product_inquiry":
            product_id = entities.get("product_id")
            if product_id:
                product_details = await self.retrieval_agent.get_product_details(uuid.UUID(product_id))
                if product_details:
                    result["data"] = {"product": product_details}
                    result["message"] = self._format_product_details(product_details)
                else:
                    result["message"] = "I couldn't find that product in your catalog."
            else:
                # Search for product by name
                products = await self.retrieval_agent.retrieve_products(
                    query=last_message,
                    limit=1,
                    in_stock_only=True,
                )
                if products:
                    result["data"] = {"product": products[0]}
                    result["message"] = self._format_product_details(products[0])
                else:
                    result["message"] = "I couldn't find a matching product in your catalog."

        elif intent_type in ("growth_analysis", "opportunity_query"):
            agent = GrowthAgent(self.session, self.merchant_id)
            opps = await agent.analyze_and_propose()
            result["data"] = {"opportunities": opps}
            result["message"] = self._format_opportunities(opps, catalog_summary)

        elif intent_type == "catalog_info":
            result["data"] = {"catalog": catalog_summary}
            result["message"] = self._format_catalog_summary(catalog_summary)

        elif intent_type == "general":
            result["message"] = f"I understand you're asking about: {last_message}. I have access to your catalog of {catalog_summary['total_products']} products across {len(catalog_summary['categories'])} categories. How can I help you grow your revenue today?"

        else:
            result["message"] = f"I'll help you with that. Intent detected: {intent_type}. I can search your catalog, provide recommendations, and analyze revenue opportunities."

        return result

    def _format_product_results(self, products: list[dict], catalog_summary: dict[str, Any] | None = None) -> str:
        if not products:
            return "I couldn't find any matching products in your catalog. Try broadening your search."

        total_in_catalog = catalog_summary['total_products'] if catalog_summary else 0
        lines = [f"Found {len(products)} products from your catalog of {total_in_catalog}:\n"]
        for i, p in enumerate(products[:5], 1):
            stock_status = "✓ In stock" if p.get('in_stock') else "✗ Out of stock"
            lines.append(
                f"{i}. {p['name']} - ₹{p['price']:,.0f} ({p['category']})\n"
                f"   {stock_status} | {p.get('available_quantity', 0)} available"
            )
        if len(products) > 5:
            lines.append(f"\n... and {len(products) - 5} more products")
        return "\n".join(lines)

    def _format_product_details(self, product: dict[str, Any]) -> str:
        lines = [
            f"**{product['name']}**",
            f"Category: {product['category']}" + (f" > {product['subcategory']}" if product.get('subcategory') else ""),
            f"Price: ₹{product['price']:,.0f}",
            f"Stock: {product['available_quantity']} available" + (" (Low stock!)" if product.get('low_stock') else ""),
        ]
        if product.get('brand'):
            lines.append(f"Brand: {product['brand']}")
        if product.get('description'):
            lines.append(f"\n{product['description']}")
        if product.get('tags'):
            lines.append(f"\nTags: {', '.join(product['tags'])}")
        return "\n".join(lines)

    def _format_opportunities(self, opps: list[dict], catalog_summary: dict[str, Any] | None = None) -> str:
        if not opps:
            return "No significant revenue opportunities detected at the moment. Your catalog looks healthy!"

        total_products = catalog_summary['total_products'] if catalog_summary else 0
        lines = [f"Found {len(opps)} revenue opportunities across your catalog of {total_products} products:\n"]
        for i, o in enumerate(opps, 1):
            lines.append(
                f"{i}. [{o['type'].upper()}] {o['title']}\n"
                f"   Expected impact: ₹{o['expected_impact']:,.0f} | Confidence: {o['confidence']:.0%} | Risk: {o['risk']}"
            )
        return "\n".join(lines)

    def _format_catalog_summary(self, catalog_summary: dict[str, Any]) -> str:
        lines = [
            f"**Your Catalog Summary**",
            f"Total products: {catalog_summary['total_products']}",
            f"Categories: {len(catalog_summary['categories'])}",
            f"Price range: ₹{catalog_summary['price_range']['min']:,.0f} - ₹{catalog_summary['price_range']['max']:,.0f}",
            f"Average price: ₹{catalog_summary['price_range']['avg']:,.0f}",
            "\n**Categories:**",
        ]
        for category, count in sorted(catalog_summary['categories'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {category}: {count} products")
        return "\n".join(lines)
