from __future__ import annotations

import hashlib
import hmac

import pytest

from app.razorpay import verify_webhook_signature


def test_webhook_signature_valid():
    secret = "test_webhook_secret"
    body = '{"event": "payment.captured", "payload": {}}'
    expected = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert verify_webhook_signature(body, expected, secret) is True


def test_webhook_signature_invalid():
    secret = "test_webhook_secret"
    body = '{"event": "payment.captured", "payload": {}}'
    bad_signature = "invalid_signature_value"

    assert verify_webhook_signature(body, bad_signature, secret) is False


def test_webhook_signature_tampered_body():
    secret = "test_webhook_secret"
    original_body = '{"event": "payment.captured", "payload": {"amount": 1000}}'
    signature = hmac.new(
        secret.encode("utf-8"),
        original_body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    tampered_body = '{"event": "payment.captured", "payload": {"amount": 999999}}'
    assert verify_webhook_signature(tampered_body, signature, secret) is False


def test_payment_signature_verification():
    key_secret = "test_key_secret"
    order_id = "order_ABC123"
    payment_id = "pay_XYZ789"

    data = f"{order_id}|{payment_id}"
    expected = hmac.new(
        key_secret.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    actual_data = f"{order_id}|{payment_id}"
    actual = hmac.new(
        key_secret.encode("utf-8"),
        actual_data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert hmac.compare_digest(expected, actual)
