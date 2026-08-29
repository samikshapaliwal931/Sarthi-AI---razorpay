from __future__ import annotations

import hashlib
import hmac
import uuid
from typing import Any

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import decrypt_secret, generate_uuid, utcnow
from app.models import (
    Merchant,
    Order,
    OrderStatus,
    Payment,
    PaymentAttempt,
    PaymentStatus,
    WebhookEvent,
    WebhookEventStatus,
)
from app.repositories import OrderRepository, PaymentRepository, WebhookEventRepository

logger = structlog.get_logger()

RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"


class RazorpayClient:
    def __init__(self, key_id: str, key_secret: str) -> None:
        self.key_id = key_id
        self.key_secret = key_secret
        self._client = httpx.AsyncClient(
            auth=(key_id, key_secret),
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def create_order(self, amount: float, currency: str = "INR", receipt: str | None = None) -> dict[str, Any]:
        amount_paise = int(round(amount * 100))
        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt or f"rcpt_{uuid.uuid4().hex[:10]}",
        }
        response = await self._client.post(f"{RAZORPAY_BASE_URL}/orders", json=payload)
        response.raise_for_status()
        return response.json()

    async def fetch_order(self, order_id: str) -> dict[str, Any]:
        response = await self._client.get(f"{RAZORPAY_BASE_URL}/orders/{order_id}")
        response.raise_for_status()
        return response.json()

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        response = await self._client.get(f"{RAZORPAY_BASE_URL}/payments/{payment_id}")
        response.raise_for_status()
        return response.json()

    async def refund_payment(self, payment_id: str, amount: float | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if amount is not None:
            payload["amount"] = int(round(amount * 100))
        response = await self._client.post(f"{RAZORPAY_BASE_URL}/payments/{payment_id}/refund", json=payload)
        response.raise_for_status()
        return response.json()


def verify_webhook_signature(body: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class RazorpayService:
    def __init__(self, session: AsyncSession, merchant_id: uuid.UUID) -> None:
        self.session = session
        self.merchant_id = merchant_id
        self.order_repo = OrderRepository(session, merchant_id)
        self.payment_repo = PaymentRepository(session, merchant_id)
        self.webhook_repo = WebhookEventRepository(session, merchant_id)
        self._client: RazorpayClient | None = None
        self._credentials: tuple[str, str, str] | None = None

    async def _get_credentials(self) -> tuple[str, str, str]:
        """Resolve (key_id, key_secret, webhook_secret) for this merchant.

        Prefers credentials the merchant connected via /integrations/razorpay/connect,
        falling back to the platform-wide credentials in settings (single-tenant demo mode).
        """
        if self._credentials is not None:
            return self._credentials

        from sqlalchemy import select

        stmt = select(Merchant).where(Merchant.id == self.merchant_id)
        result = await self.session.execute(stmt)
        merchant = result.scalar_one_or_none()

        key_id = settings.razorpay_key_id
        key_secret = settings.razorpay_key_secret
        webhook_secret = settings.razorpay_webhook_secret

        if merchant and merchant.razorpay_key_id and merchant.razorpay_key_secret_encrypted:
            key_id = merchant.razorpay_key_id
            key_secret = decrypt_secret(merchant.razorpay_key_secret_encrypted)
            if merchant.razorpay_webhook_secret_encrypted:
                webhook_secret = decrypt_secret(merchant.razorpay_webhook_secret_encrypted)

        self._credentials = (key_id, key_secret, webhook_secret)
        return self._credentials

    async def _get_client(self) -> RazorpayClient:
        if self._client is None:
            key_id, key_secret, _ = await self._get_credentials()
            self._client = RazorpayClient(key_id=key_id, key_secret=key_secret)
        return self._client

    async def is_test_mode(self) -> bool:
        """True when no real Razorpay credentials are configured (demo mode)."""
        key_id, _, _ = await self._get_credentials()
        kid = (key_id or "").strip()
        return not kid or "xxx" in kid

    async def create_checkout_order(self, order: Order) -> dict[str, Any]:
        key_id, _, _ = await self._get_credentials()
        if await self.is_test_mode():
            # Demo mode: generate a deterministic fake Razorpay order id.
            rzp_order_id = f"order_demo_{order.id.hex[:14]}"
            order.razorpay_order_id = rzp_order_id
            order.status = OrderStatus.CONFIRMED
            await self.session.flush()

            payment = Payment(
                order_id=order.id,
                merchant_id=self.merchant_id,
                razorpay_payment_id=None,
                status=PaymentStatus.PENDING,
                amount=order.total,
                currency=order.currency,
            )
            self.session.add(payment)
            await self.session.flush()

            logger.info("razorpay_demo_order_created", order_id=str(order.id), rzp_order_id=rzp_order_id)
            return {
                "razorpay_order_id": rzp_order_id,
                "amount": order.total,
                "currency": order.currency,
                "key_id": "rzp_test_demo",
                "order_id": str(order.id),
                "test_mode": True,
            }

        client = await self._get_client()
        try:
            rzp_order = await client.create_order(
                amount=order.total,
                currency=order.currency,
                receipt=order.order_number,
            )
        except httpx.HTTPStatusError as e:
            logger.error("razorpay_order_creation_failed", order_id=str(order.id), status=e.response.status_code)
            raise ValueError("Razorpay rejected the order request — check connected credentials") from e
        except httpx.HTTPError as e:
            logger.error("razorpay_order_creation_failed", order_id=str(order.id), error=str(e))
            raise ValueError("Could not reach Razorpay to create the order") from e

        order.razorpay_order_id = rzp_order["id"]
        order.status = OrderStatus.CONFIRMED
        await self.session.flush()

        payment = Payment(
            order_id=order.id,
            merchant_id=self.merchant_id,
            status=PaymentStatus.PENDING,
            amount=order.total,
            currency=order.currency,
        )
        self.session.add(payment)
        await self.session.flush()

        logger.info(
            "razorpay_order_created",
            order_id=str(order.id),
            rzp_order_id=rzp_order["id"],
        )

        return {
            "razorpay_order_id": rzp_order["id"],
            "amount": order.total,
            "currency": order.currency,
            "key_id": key_id,
            "order_id": str(order.id),
        }

    async def simulate_payment_success(self, order_id: str, method: str = "upi") -> dict[str, Any]:
        """Mark an order as paid in demo mode (simulates a successful capture).

        Only used in test mode. In production, payment state comes exclusively
        from Razorpay webhooks / server-side signature verification.
        """
        from sqlalchemy import select
        stmt = select(Order).where(Order.id == order_id, Order.merchant_id == self.merchant_id)
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("Order not found")

        rzp_payment_id = f"pay_demo_{uuid.uuid4().hex[:12]}"

        # Reuse the pending payment if present, else create a captured one.
        payments = await self.payment_repo.get_by_order(order.id)
        pending = next((p for p in payments if p.status == PaymentStatus.PENDING), None)
        if pending:
            pending.razorpay_payment_id = rzp_payment_id
            pending.status = PaymentStatus.CAPTURED
            pending.method = method
        else:
            self.session.add(Payment(
                order_id=order.id,
                merchant_id=self.merchant_id,
                razorpay_payment_id=rzp_payment_id,
                status=PaymentStatus.CAPTURED,
                amount=order.total,
                currency=order.currency,
                method=method,
            ))

        order.status = OrderStatus.PAID
        await self.session.flush()
        logger.info("razorpay_demo_payment_captured", order_id=str(order.id), payment_id=rzp_payment_id)
        return {
            "status": "captured",
            "order_id": str(order.id),
            "payment_id": rzp_payment_id,
            "amount": order.total,
        }

    async def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        signature: str,
    ) -> bool:
        _, key_secret, _ = await self._get_credentials()
        data = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected = hmac.new(
            key_secret.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def process_webhook(self, body: str, signature: str) -> dict[str, Any]:
        _, _, webhook_secret = await self._get_credentials()
        if not verify_webhook_signature(body, signature, webhook_secret):
            logger.warning("webhook_signature_invalid")
            raise ValueError("Invalid webhook signature")

        import json
        payload = json.loads(body)
        event_id = payload.get("id") or payload.get("event_id", "")
        event_type = payload.get("event", "unknown")

        existing = await self.webhook_repo.get_by_razorpay_event_id(event_id)
        if existing:
            logger.info("webhook_duplicate", event_id=event_id)
            return {"status": "duplicate", "event_id": event_id}

        webhook_event = WebhookEvent(
            merchant_id=self.merchant_id,
            razorpay_event_id=event_id,
            event_type=event_type,
            payload=payload,
            status=WebhookEventStatus.RECEIVED,
        )
        self.session.add(webhook_event)
        await self.session.flush()

        try:
            webhook_event.status = WebhookEventStatus.VALIDATED
            await self._process_event(webhook_event)
            webhook_event.status = WebhookEventStatus.PROCESSED
            webhook_event.processed_at = utcnow()
        except Exception as e:
            webhook_event.status = WebhookEventStatus.FAILED
            webhook_event.last_error = str(e)
            webhook_event.retry_count += 1
            logger.error("webhook_processing_failed", event_id=event_id, error=str(e))

        await self.session.flush()
        return {"status": webhook_event.status.value, "event_id": event_id}

    async def _process_event(self, event: WebhookEvent) -> None:
        event_type = event.event_type
        payload = event.payload

        if "payment.captured" in event_type:
            await self._handle_payment_captured(payload)
        elif "payment.failed" in event_type:
            await self._handle_payment_failed(payload)
        elif "order.paid" in event_type:
            await self._handle_order_paid(payload)
        else:
            event.status = WebhookEventStatus.IGNORED
            logger.info("webhook_ignored", event_type=event_type)

    async def _handle_payment_captured(self, payload: dict[str, Any]) -> None:
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        rzp_payment_id = payment_entity.get("id")
        if not rzp_payment_id:
            return

        payment = await self.payment_repo.get_by_razorpay_payment_id(rzp_payment_id)
        if payment:
            return

        order_id = payment_entity.get("order_id")
        if not order_id:
            return

        from sqlalchemy import select
        stmt = select(Order).where(
            Order.merchant_id == self.merchant_id,
            Order.razorpay_order_id == order_id,
        )
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            return

        # Complete the pending payment row created at checkout rather than
        # leaving it orphaned and inserting a second row for the same order.
        existing_payments = await self.payment_repo.get_by_order(order.id)
        pending = next((p for p in existing_payments if p.status == PaymentStatus.PENDING), None)

        amount = payment_entity.get("amount", 0) / 100
        currency = payment_entity.get("currency", "INR")
        method = payment_entity.get("method")

        if pending:
            pending.razorpay_payment_id = rzp_payment_id
            pending.status = PaymentStatus.CAPTURED
            pending.amount = amount
            pending.currency = currency
            pending.method = method
        else:
            payment = Payment(
                order_id=order.id,
                merchant_id=self.merchant_id,
                razorpay_payment_id=rzp_payment_id,
                status=PaymentStatus.CAPTURED,
                amount=amount,
                currency=currency,
                method=method,
            )
            self.session.add(payment)

        order.status = OrderStatus.PAID
        await self.session.flush()

        logger.info("payment_captured", rzp_payment_id=rzp_payment_id, order_id=str(order.id))

    async def _handle_payment_failed(self, payload: dict[str, Any]) -> None:
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        rzp_payment_id = payment_entity.get("id")
        if not rzp_payment_id:
            return

        payment = await self.payment_repo.get_by_razorpay_payment_id(rzp_payment_id)
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.error_code = payment_entity.get("error_code")
            payment.error_description = payment_entity.get("error_description")
        else:
            order_id = payment_entity.get("order_id")
            if not order_id:
                return

            from sqlalchemy import select
            stmt = select(Order).where(
                Order.merchant_id == self.merchant_id,
                Order.razorpay_order_id == order_id,
            )
            result = await self.session.execute(stmt)
            order = result.scalar_one_or_none()
            if not order:
                return

            payment = Payment(
                order_id=order.id,
                merchant_id=self.merchant_id,
                razorpay_payment_id=rzp_payment_id,
                status=PaymentStatus.FAILED,
                amount=payment_entity.get("amount", 0) / 100,
                currency=payment_entity.get("currency", "INR"),
                error_code=payment_entity.get("error_code"),
                error_description=payment_entity.get("error_description"),
            )
            self.session.add(payment)
            order.status = OrderStatus.FAILED

        await self.session.flush()
        logger.info("payment_failed", rzp_payment_id=rzp_payment_id)

    async def _handle_order_paid(self, payload: dict[str, Any]) -> None:
        order_entity = payload.get("payload", {}).get("order", {}).get("entity", {})
        rzp_order_id = order_entity.get("id")
        if not rzp_order_id:
            return

        from sqlalchemy import select
        stmt = select(Order).where(
            Order.merchant_id == self.merchant_id,
            Order.razorpay_order_id == rzp_order_id,
        )
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if order and order.status != OrderStatus.PAID:
            order.status = OrderStatus.PAID
            await self.session.flush()
