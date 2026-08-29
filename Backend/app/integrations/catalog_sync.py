from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Product, Inventory, ProductVariant, MerchantIntegration
from app.repositories import ProductRepository, InventoryRepository
from app.schemas import ProductCreate


class CatalogSyncService:
    """Service for syncing merchant catalogs from external sources"""
    
    def __init__(self, db: AsyncSession, merchant_id: uuid.UUID):
        self.db = db
        self.merchant_id = merchant_id
        self.product_repo = ProductRepository(db, merchant_id)
        self.inventory_repo = InventoryRepository(db, merchant_id)
    
    async def sync_from_json(self, products_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Sync catalog from JSON/CSV format"""
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
        
        for product_data in products_data:
            try:
                # Map external fields to internal schema
                product_create = self._map_external_product(product_data)
                
                # Check if product exists by external ID
                existing = await self._find_by_external_id(product_data.get("id"))
                
                if existing:
                    # Update existing product
                    await self.product_repo.update(existing, **product_create.model_dump(exclude_unset=True))
                    stats["updated"] += 1
                else:
                    # Create new product
                    product = await self.product_repo.create(**product_create.model_dump())
                    # Create inventory record
                    await self._create_inventory(product, product_data)
                    stats["created"] += 1
                    
            except Exception as e:
                stats["errors"] += 1
                continue
                
        return stats
    
    async def sync_from_api(self, api_config: dict[str, Any]) -> dict[str, Any]:
        """Sync catalog from external API (Shopify, WooCommerce, etc.)"""
        import httpx
        
        provider = api_config.get("provider")
        endpoint = api_config.get("endpoint")
        api_key = api_config.get("api_key")
        
        if not all([provider, endpoint, api_key]):
            raise ValueError("Missing required API configuration")
        
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        try:
            async with httpx.AsyncClient() as client:
                headers = self._get_api_headers(provider, api_key)
                response = await client.get(endpoint, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                products_data = self._parse_api_response(provider, response.json())
                stats = await self.sync_from_json(products_data)
                
        except Exception as e:
            stats["errors"] += 1
            raise
            
        return stats
    
    async def sync_from_database(self, db_config: dict[str, Any]) -> dict[str, Any]:
        """Sync catalog from external database (MySQL, PostgreSQL, etc.)"""
        # Placeholder for database sync
        # Would use SQLAlchemy to connect to external DB
        return {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "message": "Database sync not implemented"}
    
    def _map_external_product(self, external_data: dict[str, Any]) -> ProductCreate:
        """Map external product fields to internal schema"""
        return ProductCreate(
            name=external_data.get("name") or external_data.get("title", ""),
            description=external_data.get("description"),
            category=external_data.get("category") or external_data.get("type", "uncategorized"),
            subcategory=external_data.get("subcategory"),
            brand=external_data.get("brand"),
            base_price=float(external_data.get("price") or external_data.get("base_price", 0)),
            sale_price=float(external_data.get("sale_price")) if external_data.get("sale_price") else None,
            currency=external_data.get("currency", "INR"),
            images=external_data.get("images", []),
            attributes=external_data.get("attributes", {}),
            tags=external_data.get("tags", []),
            metadata_={"external_id": external_data.get("id"), "source": external_data.get("source")}
        )
    
    async def _find_by_external_id(self, external_id: str | None) -> Product | None:
        """Find product by external ID from metadata"""
        if not external_id:
            return None
            
        stmt = select(Product).where(
            Product.merchant_id == self.merchant_id,
            Product.metadata_["external_id"].astext == str(external_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _create_inventory(self, product: Product, external_data: dict[str, Any]) -> Inventory:
        """Create inventory record for product"""
        inventory = Inventory(
            product_id=product.id,
            merchant_id=self.merchant_id,
            quantity=int(external_data.get("stock") or external_data.get("inventory", 0)),
            low_stock_threshold=int(external_data.get("low_stock_threshold", 5))
        )
        self.db.add(inventory)
        await self.db.flush()
        return inventory
    
    def _get_api_headers(self, provider: str, api_key: str) -> dict[str, str]:
        """Get API headers based on provider"""
        headers = {"Content-Type": "application/json"}
        
        if provider == "shopify":
            headers["X-Shopify-Access-Token"] = api_key
        elif provider == "woocommerce":
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            headers["Authorization"] = f"Bearer {api_key}"
            
        return headers
    
    def _parse_api_response(self, provider: str, response_data: Any) -> list[dict[str, Any]]:
        """Parse API response based on provider"""
        if provider == "shopify":
            return [self._parse_shopify_product(p) for p in response_data.get("products", [])]
        elif provider == "woocommerce":
            return [self._parse_woocommerce_product(p) for p in response_data]
        else:
            return response_data if isinstance(response_data, list) else [response_data]
    
    def _parse_shopify_product(self, product: dict[str, Any]) -> dict[str, Any]:
        """Parse Shopify product format"""
        return {
            "id": str(product.get("id")),
            "name": product.get("title"),
            "description": product.get("body_html"),
            "category": product.get("product_type", "uncategorized"),
            "price": product.get("variants", [{}])[0].get("price"),
            "images": [img.get("src") for img in product.get("images", [])],
            "stock": product.get("variants", [{}])[0].get("inventory_quantity", 0),
            "source": "shopify"
        }
    
    def _parse_woocommerce_product(self, product: dict[str, Any]) -> dict[str, Any]:
        """Parse WooCommerce product format"""
        return {
            "id": str(product.get("id")),
            "name": product.get("name"),
            "description": product.get("description"),
            "category": product.get("categories", [{}])[0].get("name", "uncategorized"),
            "price": product.get("price"),
            "images": [img.get("src") for img in product.get("images", [])],
            "stock": product.get("stock_quantity", 0),
            "source": "woocommerce"
        }
    
    async def record_sync_result(self, integration_type:(str), stats: dict[str, Any]) -> None:
        """Record sync result in merchant_integrations table"""
        integration = MerchantIntegration(
            merchant_id=self.merchant_id,
            provider="catalog_sync",
            integration_type=integration_type,
            config={
                "last_sync": datetime.now(timezone.utc).isoformat(),
                "stats": stats
            },
            is_active=True
        )
        self.db.add(integration)
        await self.db.flush()
