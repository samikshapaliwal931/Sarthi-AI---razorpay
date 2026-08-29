from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.config import settings
from app.database import Base


class GUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ─── Enums ───────────────────────────────────────────────────────────────────


class MerchantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class OrderStatus(str, enum.Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class CartStatus(str, enum.Enum):
    ACTIVE = "active"
    ABANDONED = "abandoned"
    CONVERTED = "converted"
    EXPIRED = "expired"


class OpportunityType(str, enum.Enum):
    CROSS_SELL = "cross_sell"
    BUNDLE = "bundle"
    UPSELL = "upsell"
    ABANDONED_CART = "abandoned_cart"
    PAYMENT_RECOVERY = "payment_recovery"
    INVENTORY = "inventory"
    PRICE_EXPERIMENT = "price_experiment"
    REPEAT_PURCHASE = "repeat_purchase"


class OpportunityStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"


class RecommendationStatus(str, enum.Enum):
    GENERATED = "generated"
    SHOWN = "shown"
    CLICKED = "clicked"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AgentRunStatus(str, enum.Enum):
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(str, enum.Enum):
    CREATE_CAMPAIGN = "create_campaign"
    SEND_RECOVERY_MESSAGE = "send_recovery_message"
    CREATE_RZP_ORDER = "create_rzp_order"
    UPDATE_CART = "update_cart"
    APPLY_DISCOUNT = "apply_discount"
    START_EXPERIMENT = "start_experiment"
    UPDATE_PRICING = "update_pricing"
    UPDATE_INVENTORY = "update_inventory"


class ActionStatus(str, enum.Enum):
    PROPOSED = "proposed"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"


class PolicyDecision(str, enum.Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRES_APPROVAL = "requires_approval"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class WebhookEventStatus(str, enum.Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class AttributionType(str, enum.Enum):
    DIRECT = "direct"
    ASSISTED = "assisted"
    RECOVERY = "recovery"
    CAMPAIGN = "campaign"
    UPSELL = "upsell"
    CROSS_SELL = "cross_sell"


class RecoveryCaseStatus(str, enum.Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    INTERVENTION_PROPOSED = "intervention_proposed"
    INTERVENTION_SENT = "intervention_sent"
    RECOVERED = "recovered"
    EXPIRED = "expired"
    FAILED = "failed"


# ─── Models ──────────────────────────────────────────────────────────────────


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    store_name: Mapped[str] = mapped_column(String(255), nullable=False)
    store_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[MerchantStatus] = mapped_column(
        Enum(MerchantStatus), default=MerchantStatus.ACTIVE, nullable=False
    )
    razorpay_key_id: Mapped[str | None] = mapped_column(String(255))
    razorpay_key_secret_encrypted: Mapped[str | None] = mapped_column(String(512))
    razorpay_webhook_secret_encrypted: Mapped[str | None] = mapped_column(String(512))
    ai_buyer_api_key_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    settings: Mapped[MerchantSettings | None] = relationship(back_populates="merchant", uselist=False)
    products: Mapped[list[Product]] = relationship(back_populates="merchant")
    customers: Mapped[list[Customer]] = relationship(back_populates="merchant")
    orders: Mapped[list[Order]] = relationship(back_populates="merchant")
    policies: Mapped[list[Policy]] = relationship(back_populates="merchant")


class MerchantSettings(Base):
    __tablename__ = "merchant_settings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), unique=True, nullable=False
    )
    max_discount_percent: Mapped[float] = mapped_column(Float, default=10.0)
    max_campaign_budget: Mapped[float] = mapped_column(Float, default=50000.0)
    max_daily_spend: Mapped[float] = mapped_column(Float, default=10000.0)
    max_actions_per_hour: Mapped[int] = mapped_column(Integer, default=10)
    approval_required_above_amount: Mapped[float] = mapped_column(Float, default=5000.0)
    allowed_campaign_types: Mapped[list[str] | None] = mapped_column(JSON)
    auto_approve_below_amount: Mapped[float] = mapped_column(Float, default=1000.0)
    enable_cross_sell: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_upsell: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_recovery: Mapped[bool] = mapped_column(Boolean, default=True)
    recommendation_weights: Mapped[dict[str, float] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    merchant: Mapped[Merchant] = relationship(back_populates="settings")


class MerchantIntegration(Base):
    __tablename__ = "merchant_integrations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    integration_type: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("merchant_id", "provider", "integration_type", name="uq_merchant_integration"),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(200))
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    sale_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    images: Mapped[list[str] | None] = mapped_column(JSON)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    merchant: Mapped[Merchant] = relationship(back_populates="products")
    variants: Mapped[list[ProductVariant]] = relationship(back_populates="product")
    inventory: Mapped[Inventory | None] = relationship(back_populates="product", uselist=False)

    __table_args__ = (
        Index("ix_products_merchant_category", "merchant_id", "category"),
        Index("ix_products_merchant_active", "merchant_id", "is_active"),
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    product: Mapped[Product] = relationship(back_populates="variants")

    __table_args__ = (
        UniqueConstraint("product_id", "sku", name="uq_variant_sku"),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), unique=True, nullable=False
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)
    warehouse: Mapped[str] = mapped_column(String(100), default="default")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    product: Mapped[Product] = relationship(back_populates="inventory")

    @property
    def available(self) -> int:
        return max(0, self.quantity - self.reserved)

    @property
    def is_in_stock(self) -> bool:
        return self.available > 0

    @property
    def is_low_stock(self) -> bool:
        return self.available <= self.low_stock_threshold


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    name: Mapped[str | None] = mapped_column(String(255))
    segment: Mapped[str | None] = mapped_column(String(50))
    lifetime_value: Mapped[float] = mapped_column(Float, default=0.0)
    order_count: Mapped[int] = mapped_column(Integer, default=0)
    last_order_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    merchant: Mapped[Merchant] = relationship(back_populates="customers")
    orders: Mapped[list[Order]] = relationship(back_populates="customer")
    carts: Mapped[list[Cart]] = relationship(back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id"), index=True
    )
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False
    )
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), index=True)
    recommendation_event_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("recommendation_events.id")
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    merchant: Mapped[Merchant] = relationship(back_populates="orders")
    customer: Mapped[Customer | None] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order")
    payments: Mapped[list[Payment]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("product_variants.id")
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    order: Mapped[Order] = relationship(back_populates="items")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id"), index=True
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[CartStatus] = mapped_column(
        Enum(CartStatus), default=CartStatus.ACTIVE, nullable=False
    )
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    recommendation_event_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("recommendation_events.id")
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    customer: Mapped[Customer | None] = relationship(back_populates="carts")
    items: Mapped[list[CartItem]] = relationship(back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    cart_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("carts.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("product_variants.id")
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    cart: Mapped[Cart] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", "variant_id", name="uq_cart_item"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), index=True)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    method: Mapped[str | None] = mapped_column(String(50))
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_description: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    order: Mapped[Order] = relationship(back_populates="payments")
    attempts: Mapped[list[PaymentAttempt]] = relationship(back_populates="payment")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    payment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("payments.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), nullable=False
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100))
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    payment: Mapped[Payment] = relationship(back_populates="attempts")


class AbandonedCart(Base):
    __tablename__ = "abandoned_carts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    cart_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("carts.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id")
    )
    cart_value: Mapped[float] = mapped_column(Float, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    abandoned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    recovery_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    recovered: Mapped[bool] = mapped_column(Boolean, default=False)
    recovered_order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    type: Mapped[OpportunityType] = mapped_column(Enum(OpportunityType), nullable=False)
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus), default=OpportunityStatus.DISCOVERED, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    expected_impact: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk: Mapped[str] = mapped_column(String(50), default="low")
    recommended_action: Mapped[str | None] = mapped_column(Text)
    required_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    policy_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    evidence: Mapped[list[OpportunityEvidence]] = relationship(back_populates="opportunity")

    __table_args__ = (
        Index("ix_opportunities_merchant_type", "merchant_id", "type"),
    )


class OpportunityEvidence(Base):
    __tablename__ = "opportunity_evidence"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)
    data_source: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    opportunity: Mapped[Opportunity] = relationship(back_populates="evidence")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id")
    )
    session_id: Mapped[str | None] = mapped_column(String(100), index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False
    )
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_components: Mapped[dict[str, float] | None] = mapped_column(JSON)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus), default=RecommendationStatus.GENERATED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("recommendations.id"), nullable=False
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id")
    )
    session_id: Mapped[str | None] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id")
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_rec_events_merchant_type", "merchant_id", "event_type"),
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("opportunities.id")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    budget: Mapped[float] = mapped_column(Float, default=0.0)
    actual_spend: Mapped[float] = mapped_column(Float, default=0.0)
    revenue_generated: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    variants: Mapped[list[CampaignVariant]] = relationship(back_populates="campaign")


class CampaignVariant(Base):
    __tablename__ = "campaign_variants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    campaign_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("campaigns.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    campaign: Mapped[Campaign] = relationship(back_populates="variants")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    experiment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    assignments: Mapped[list[ExperimentAssignment]] = relationship(back_populates="experiment")


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    experiment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("experiments.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id")
    )
    session_id: Mapped[str | None] = mapped_column(String(100))
    variant: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    experiment: Mapped[Experiment] = relationship(back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("experiment_id", "session_id", name="uq_experiment_session"),
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    runs: Mapped[list[AgentRun]] = relationship(back_populates="agent")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    agent_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agents.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus), default=AgentRunStatus.STARTED, nullable=False
    )
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[str | None] = mapped_column(String(100))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    correlation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    agent: Mapped[Agent] = relationship(back_populates="runs")
    decisions: Mapped[list[AgentDecision]] = relationship(back_populates="run")
    actions: Mapped[list[AgentAction]] = relationship(back_populates="run")


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Float)
    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    run: Mapped[AgentRun] = relationship(back_populates="decisions")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    action_type: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus), default=ActionStatus.PROPOSED, nullable=False
    )
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    policy_result: Mapped[PolicyDecision | None] = mapped_column(Enum(PolicyDecision))
    approval_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("approvals.id")
    )
    error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    run: Mapped[AgentRun] = relationship(back_populates="actions")


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    merchant: Mapped[Merchant] = relationship(back_populates="policies")
    evaluations: Mapped[list[PolicyEvaluation]] = relationship(back_populates="policy")


class PolicyEvaluation(Base):
    __tablename__ = "policy_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    policy_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("policies.id"), nullable=False, index=True
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    decision: Mapped[PolicyDecision] = mapped_column(Enum(PolicyDecision), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    agent_action_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("agent_actions.id")
    )
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    policy: Mapped[Policy] = relationship(back_populates="evaluations")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    agent_action_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("agent_actions.id")
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str | None] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(Text)
    policy_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("policy_evaluations.id")
    )
    action_hash: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("agent_runs.id")
    )
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    input_hash: Mapped[str | None] = mapped_column(String(64))
    decision: Mapped[str | None] = mapped_column(String(100))
    policy_result: Mapped[str | None] = mapped_column(String(50))
    approval_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("approvals.id")
    )
    execution_result: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    correlation_id: Mapped[str | None] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_audit_merchant_action", "merchant_id", "action"),
    )


class RevenueAttribution(Base):
    __tablename__ = "revenue_attributions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False, index=True
    )
    recommendation_event_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("recommendation_events.id")
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("campaigns.id")
    )
    attribution_type: Mapped[AttributionType] = mapped_column(
        Enum(AttributionType), nullable=False
    )
    attributed_amount: Mapped[float] = mapped_column(Float, nullable=False)
    total_order_amount: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("customers.id")
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id")
    )
    cart_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("carts.id")
    )
    case_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RecoveryCaseStatus] = mapped_column(
        Enum(RecoveryCaseStatus), default=RecoveryCaseStatus.DETECTED, nullable=False
    )
    potential_value: Mapped[float] = mapped_column(Float, default=0.0)
    recovered_value: Mapped[float] = mapped_column(Float, default=0.0)
    intervention_type: Mapped[str | None] = mapped_column(String(100))
    intervention_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    razorpay_event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(WebhookEventStatus), default=WebhookEventStatus.RECEIVED, nullable=False
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    evaluation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    dataset_info: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ModelFeedback(Base):
    __tablename__ = "model_feedback"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    model_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("model_evaluations.id")
    )
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_new_uuid)
    merchant_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("merchants.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(100))
    parameters_before: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    parameters_after: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
