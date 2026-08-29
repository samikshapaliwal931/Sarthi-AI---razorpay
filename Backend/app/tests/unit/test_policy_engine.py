from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import hash_password
from app.models import Merchant, MerchantSettings, Policy, PolicyDecision
from app.policies import PolicyEngine


@pytest.mark.asyncio
async def test_policy_blocks_excessive_discount(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"p1_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    policy = Policy(
        merchant_id=merchant.id,
        name="Max Discount",
        policy_type="discount_limit",
        rules={"max_discount_percent": 10, "action_types": ["apply_discount"]},
        priority=100,
    )
    db_session.add(policy)
    await db_session.flush()

    engine = PolicyEngine(db_session, merchant.id)

    decision, reason, evals = await engine.evaluate(
        action_type="apply_discount",
        input_data={"discount_percent": 15},
    )

    assert decision == PolicyDecision.BLOCK
    assert reason is not None
    assert "15%" in reason
    assert "10%" in reason


@pytest.mark.asyncio
async def test_policy_allows_valid_discount(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"p2_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    policy = Policy(
        merchant_id=merchant.id,
        name="Max Discount",
        policy_type="discount_limit",
        rules={"max_discount_percent": 10, "action_types": ["apply_discount"]},
        priority=100,
    )
    db_session.add(policy)
    await db_session.flush()

    engine = PolicyEngine(db_session, merchant.id)

    decision, reason, evals = await engine.evaluate(
        action_type="apply_discount",
        input_data={"discount_percent": 5},
    )

    assert decision == PolicyDecision.ALLOW


@pytest.mark.asyncio
async def test_policy_requires_approval_for_high_amount(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"p3_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    policy = Policy(
        merchant_id=merchant.id,
        name="High Value Approval",
        policy_type="approval_threshold",
        rules={"approval_above_amount": 5000, "action_types": ["create_campaign"]},
        priority=80,
    )
    db_session.add(policy)
    await db_session.flush()

    engine = PolicyEngine(db_session, merchant.id)

    decision, reason, evals = await engine.evaluate(
        action_type="create_campaign",
        input_data={"amount": 10000},
    )

    assert decision == PolicyDecision.REQUIRES_APPROVAL


@pytest.mark.asyncio
async def test_policy_blocks_over_budget(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"p4_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    policy = Policy(
        merchant_id=merchant.id,
        name="Budget Cap",
        policy_type="budget_limit",
        rules={"max_budget": 50000, "action_types": ["create_campaign"]},
        priority=90,
    )
    db_session.add(policy)
    await db_session.flush()

    engine = PolicyEngine(db_session, merchant.id)

    decision, reason, evals = await engine.evaluate(
        action_type="create_campaign",
        input_data={"budget": 100000},
    )

    assert decision == PolicyDecision.BLOCK
    assert "exceeds maximum" in reason


@pytest.mark.asyncio
async def test_policy_blocks_rate_limit(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"p5_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    policy = Policy(
        merchant_id=merchant.id,
        name="Rate Limit",
        policy_type="action_frequency",
        rules={"max_per_hour": 5},
        priority=70,
    )
    db_session.add(policy)
    await db_session.flush()

    engine = PolicyEngine(db_session, merchant.id)

    decision, reason, evals = await engine.evaluate(
        action_type="any_action",
        input_data={"actions_this_hour": 6},
    )

    assert decision == PolicyDecision.BLOCK


@pytest.mark.asyncio
async def test_policy_evaluation_creates_audit_records(db_session: AsyncSession):
    merchant = Merchant(
        name="Test", email=f"p6_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"), store_name="Test",
    )
    db_session.add(merchant)
    await db_session.flush()

    policy = Policy(
        merchant_id=merchant.id,
        name="Discount",
        policy_type="discount_limit",
        rules={"max_discount_percent": 10, "action_types": ["apply_discount"]},
        priority=100,
    )
    db_session.add(policy)
    await db_session.flush()

    engine = PolicyEngine(db_session, merchant.id)
    decision, reason, evals = await engine.evaluate(
        action_type="apply_discount",
        input_data={"discount_percent": 20},
    )

    assert len(evals) == 1
    assert evals[0].decision == PolicyDecision.BLOCK
    assert evals[0].merchant_id == merchant.id
