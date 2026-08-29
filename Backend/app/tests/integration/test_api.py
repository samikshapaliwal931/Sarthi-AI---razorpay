from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sarthi"


@pytest.mark.asyncio
async def test_ready_endpoint(client: AsyncClient):
    response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "store_name" in data


@pytest.mark.asyncio
async def test_get_merchant_settings(client: AsyncClient):
    response = await client.get("/api/v1/merchant/settings")
    assert response.status_code == 200
    data = response.json()
    assert "max_discount_percent" in data
    assert "max_campaign_budget" in data


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_and_get_product(client: AsyncClient):
    create_response = await client.post("/api/v1/products", json={
        "name": "Test Running Shoe",
        "category": "Running Shoes",
        "base_price": 4999.0,
        "brand": "TestBrand",
    })
    assert create_response.status_code == 201
    product = create_response.json()
    assert product["name"] == "Test Running Shoe"
    assert product["base_price"] == 4999.0

    get_response = await client.get(f"/api/v1/products/{product['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test Running Shoe"


@pytest.mark.asyncio
async def test_list_policies(client: AsyncClient):
    response = await client.get("/api/v1/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_and_evaluate_policy(client: AsyncClient):
    create_response = await client.post("/api/v1/policies", json={
        "name": "Test Discount Policy",
        "policy_type": "discount_limit",
        "rules": {"max_discount_percent": 10, "action_types": ["apply_discount"]},
    })
    assert create_response.status_code == 201

    eval_response = await client.post("/api/v1/policies/evaluate", json={
        "action_type": "apply_discount",
        "input_data": {"discount_percent": 15},
    })
    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["decision"] == "block"


@pytest.mark.asyncio
async def test_get_audit_log(client: AsyncClient):
    response = await client.get("/api/v1/audit")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_dashboard(client: AsyncClient):
    response = await client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "revenue_metrics" in data
    assert "active_opportunities" in data
    assert "pending_approvals" in data


@pytest.mark.asyncio
async def test_get_opportunities(client: AsyncClient):
    response = await client.get("/api/v1/opportunities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthorized_access():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/products")
        assert response.status_code == 401
