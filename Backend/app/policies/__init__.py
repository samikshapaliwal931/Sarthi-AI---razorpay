from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Policy,
    PolicyDecision,
    PolicyEvaluation,
)
from app.repositories import PolicyRepository, PolicyEvaluationRepository

logger = structlog.get_logger()


class PolicyEngine:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.policy_repo = PolicyRepository(session, merchant_id)
        self.eval_repo = PolicyEvaluationRepository(session, merchant_id)

    async def evaluate(
        self,
        action_type: str,
        input_data: dict[str, Any],
        correlation_id: str | None = None,
    ) -> tuple[PolicyDecision, str | None, list[PolicyEvaluation]]:
        policies = await self.policy_repo.get_active_policies()

        evaluations: list[PolicyEvaluation] = []
        final_decision = PolicyDecision.ALLOW
        block_reason: str | None = None

        for policy in policies:
            decision, reason = self._evaluate_policy(policy, action_type, input_data)

            evaluation = PolicyEvaluation(
                policy_id=policy.id,
                merchant_id=self.merchant_id,
                action_type=action_type,
                input_data=input_data,
                decision=decision,
                reason=reason,
                correlation_id=correlation_id,
            )
            self.session.add(evaluation)
            evaluations.append(evaluation)

            if decision == PolicyDecision.BLOCK:
                final_decision = PolicyDecision.BLOCK
                block_reason = reason
                break
            elif decision == PolicyDecision.REQUIRES_APPROVAL:
                if final_decision != PolicyDecision.BLOCK:
                    final_decision = PolicyDecision.REQUIRES_APPROVAL

        await self.session.flush()

        logger.info(
            "policy_evaluated",
            action_type=action_type,
            decision=final_decision.value,
            policies_checked=len(policies),
        )

        return final_decision, block_reason, evaluations

    def _evaluate_policy(
        self,
        policy: Policy,
        action_type: str,
        input_data: dict[str, Any],
    ) -> tuple[PolicyDecision, str | None]:
        rules = policy.rules

        if rules.get("action_types") and action_type not in rules["action_types"]:
            return PolicyDecision.ALLOW, None

        if policy.policy_type == "discount_limit":
            return self._check_discount_limit(rules, input_data)
        elif policy.policy_type == "budget_limit":
            return self._check_budget_limit(rules, input_data)
        elif policy.policy_type == "approval_threshold":
            return self._check_approval_threshold(rules, input_data)
        elif policy.policy_type == "rate_limit":
            return self._check_rate_limit(rules, input_data)
        elif policy.policy_type == "category_restriction":
            return self._check_category_restriction(rules, input_data)
        elif policy.policy_type == "action_frequency":
            return self._check_action_frequency(rules, input_data)

        return PolicyDecision.ALLOW, None

    def _check_discount_limit(
        self, rules: dict, input_data: dict
    ) -> tuple[PolicyDecision, str | None]:
        max_discount = rules.get("max_discount_percent", 100)
        requested_discount = input_data.get("discount_percent", 0)

        if requested_discount > max_discount:
            return (
                PolicyDecision.BLOCK,
                f"Discount {requested_discount}% exceeds maximum allowed {max_discount}%",
            )
        return PolicyDecision.ALLOW, None

    def _check_budget_limit(
        self, rules: dict, input_data: dict
    ) -> tuple[PolicyDecision, str | None]:
        max_budget = rules.get("max_budget", float("inf"))
        requested_budget = input_data.get("budget", 0)

        if requested_budget > max_budget:
            return (
                PolicyDecision.BLOCK,
                f"Budget ₹{requested_budget} exceeds maximum allowed ₹{max_budget}",
            )
        return PolicyDecision.ALLOW, None

    def _check_approval_threshold(
        self, rules: dict, input_data: dict
    ) -> tuple[PolicyDecision, str | None]:
        threshold = rules.get("approval_above_amount", float("inf"))
        amount = input_data.get("amount", 0)

        if amount > threshold:
            return (
                PolicyDecision.REQUIRES_APPROVAL,
                f"Amount ₹{amount} exceeds approval threshold ₹{threshold}",
            )
        return PolicyDecision.ALLOW, None

    def _check_rate_limit(
        self, rules: dict, input_data: dict
    ) -> tuple[PolicyDecision, str | None]:
        max_per_hour = rules.get("max_actions_per_hour", float("inf"))
        current_count = input_data.get("current_hourly_count", 0)

        if current_count >= max_per_hour:
            return (
                PolicyDecision.BLOCK,
                f"Rate limit exceeded: {current_count}/{max_per_hour} actions this hour",
            )
        return PolicyDecision.ALLOW, None

    def _check_category_restriction(
        self, rules: dict, input_data: dict
    ) -> tuple[PolicyDecision, str | None]:
        allowed = rules.get("allowed_categories", [])
        category = input_data.get("category", "")

        if allowed and category not in allowed:
            return (
                PolicyDecision.BLOCK,
                f"Category '{category}' is not allowed for this action",
            )
        return PolicyDecision.ALLOW, None

    def _check_action_frequency(
        self, rules: dict, input_data: dict
    ) -> tuple[PolicyDecision, str | None]:
        max_per_hour = rules.get("max_per_hour", float("inf"))
        current = input_data.get("actions_this_hour", 0)

        if current >= max_per_hour:
            return (
                PolicyDecision.BLOCK,
                f"Action frequency limit: {current}/{max_per_hour} this hour",
            )
        return PolicyDecision.ALLOW, None


class ApprovalService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.approval_repo: Any = None

    async def create_approval(
        self,
        agent_action_id: uuid.UUID | None = None,
        actor_type: str = "system",
        actor_id: str = "sarthi",
        action_hash: str | None = None,
        correlation_id: str | None = None,
    ) -> Any:
        from app.models import Approval, ApprovalStatus
        approval = Approval(
            merchant_id=self.merchant_id,
            agent_action_id=agent_action_id,
            status=ApprovalStatus.PENDING,
            actor_type=actor_type,
            actor_id=actor_id,
            action_hash=action_hash,
            correlation_id=correlation_id,
        )
        self.session.add(approval)
        await self.session.flush()
        return approval

    async def approve(self, approval_id: uuid.UUID, actor_id: str, reason: str | None = None) -> Any:
        from app.models import Approval, ApprovalStatus
        from app.repositories import ApprovalRepository
        repo = ApprovalRepository(self.session, self.merchant_id)
        approval = await repo.get_by_id(approval_id)
        if not approval:
            raise ValueError("Approval not found")
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval is not pending, current status: {approval.status}")

        from app.core import utcnow
        approval.status = ApprovalStatus.APPROVED
        approval.decision = "approved"
        approval.actor_id = actor_id
        approval.reason = reason
        approval.decided_at = utcnow()
        await self.session.flush()
        return approval

    async def reject(self, approval_id: uuid.UUID, actor_id: str, reason: str | None = None) -> Any:
        from app.models import Approval, ApprovalStatus
        from app.repositories import ApprovalRepository
        repo = ApprovalRepository(self.session, self.merchant_id)
        approval = await repo.get_by_id(approval_id)
        if not approval:
            raise ValueError("Approval not found")
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval is not pending, current status: {approval.status}")

        from app.core import utcnow
        approval.status = ApprovalStatus.REJECTED
        approval.decision = "rejected"
        approval.actor_id = actor_id
        approval.reason = reason
        approval.decided_at = utcnow()
        await self.session.flush()
        return approval
