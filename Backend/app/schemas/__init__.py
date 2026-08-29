from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime | None = None


# ─── Auth ────────────────────────────────────────────────────────────────────


class RegisterRequest(BaseSchema):
    name: str
    email: str
    password: str
    store_name: str


class LoginRequest(BaseSchema):
    email: str
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    merchant_id: uuid.UUID
    user_id: uuid.UUID
    ai_buyer_api_key: str | None = None


# ─── Merchant ────────────────────────────────────────────────────────────────


class MerchantResponse(TimestampSchema):
    id: uuid.UUID
    name: str
    email: str
    store_name: str
    store_url: str | None
    status: str


class MerchantSettingsResponse(BaseSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    max_discount_percent: float
    max_campaign_budget: float
    max_daily_spend: float
    max_actions_per_hour: int
    approval_required_above_amount: float
    auto_approve_below_amount: float
    enable_cross_sell: bool
    enable_upsell: bool
    enable_recovery: bool


class MerchantSettingsUpdate(BaseSchema):
    max_discount_percent: float | None = None
    max_campaign_budget: float | None = None
    max_daily_spend: float | None = None
    max_actions_per_hour: int | None = None
    approval_required_above_amount: float | None = None
    auto_approve_below_amount: float | None = None
    enable_cross_sell: bool | None = None
    enable_upsell: bool | None = None
    enable_recovery: bool | None = None


# ─── Products ────────────────────────────────────────────────────────────────


class ProductCreate(BaseSchema):
    name: str
    description: str | None = None
    category: str
    subcategory: str | None = None
    brand: str | None = None
    base_price: float
    sale_price: float | None = None
    currency: str = "INR"
    images: list[str] | None = None
    attributes: dict[str, Any] | None = None
    tags: list[str] | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class ProductResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    description: str | None
    category: str
    subcategory: str | None
    brand: str | None
    base_price: float
    sale_price: float | None
    currency: str
    images: list[str] | None
    attributes: dict[str, Any] | None
    tags: list[str] | None
    is_active: bool


class ProductSearchRequest(BaseSchema):
    query: str | None = None
    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    brand: str | None = None
    in_stock_only: bool = True
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ProductSearchResponse(BaseSchema):
    products: list[ProductResponse]
    total: int
    limit: int
    offset: int


# ─── Inventory ───────────────────────────────────────────────────────────────


class InventoryResponse(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    merchant_id: uuid.UUID
    quantity: int
    reserved: int
    available: int
    is_in_stock: bool
    is_low_stock: bool
    low_stock_threshold: int


class InventoryUpdate(BaseSchema):
    quantity: int | None = None
    reserved: int | None = None
    low_stock_threshold: int | None = None


# ─── Customers ───────────────────────────────────────────────────────────────


class CustomerCreate(BaseSchema):
    email: str | None = None
    phone: str | None = None
    name: str | None = None
    segment: str | None = None


class CustomerResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    email: str | None
    phone: str | None
    name: str | None
    segment: str | None
    lifetime_value: float
    order_count: int
    last_order_at: datetime | None


# ─── Orders ──────────────────────────────────────────────────────────────────


class OrderItemCreate(BaseSchema):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(ge=1)


class OrderCreate(BaseSchema):
    customer_id: uuid.UUID | None = None
    items: list[OrderItemCreate]


class OrderItemResponse(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: int
    unit_price: float
    total_price: float


class OrderResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID | None
    order_number: str
    status: str
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str
    razorpay_order_id: str | None
    items: list[OrderItemResponse] = []


# ─── Cart ────────────────────────────────────────────────────────────────────


class CartItemCreate(BaseSchema):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1)


class CartItemResponse(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: int
    unit_price: float


class CartResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID | None
    session_id: str
    status: str
    subtotal: float
    currency: str
    items: list[CartItemResponse] = []


class CartAddItem(BaseSchema):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1)


class CartUpdateItem(BaseSchema):
    quantity: int = Field(ge=1)


# ─── Payments ────────────────────────────────────────────────────────────────


class CheckoutRequest(BaseSchema):
    cart_id: uuid.UUID | None = None
    order_id: uuid.UUID | None = None
    customer_email: str | None = None
    customer_phone: str | None = None


class CheckoutResponse(BaseSchema):
    razorpay_order_id: str
    amount: float
    currency: str
    key_id: str
    order_id: uuid.UUID


class PaymentResponse(TimestampSchema):
    id: uuid.UUID
    order_id: uuid.UUID
    merchant_id: uuid.UUID
    razorpay_payment_id: str | None
    status: str
    amount: float
    currency: str
    method: str | None


class WebhookPayload(BaseSchema):
    entity: str
    account_id: str | None = None
    event: str
    contains: list[str] = []
    payload: dict[str, Any] = {}


# ─── Recommendations ────────────────────────────────────────────────────────


class RecommendationRequest(BaseSchema):
    session_id: str
    customer_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    context: dict[str, Any] | None = None
    limit: int = Field(default=5, ge=1, le=20)


class RecommendationResponse(BaseSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    product: ProductResponse | None = None
    recommendation_type: str
    score: float
    score_components: dict[str, float] | None
    reason: str | None = None


class RecommendationListResponse(BaseSchema):
    recommendations: list[RecommendationResponse]
    session_id: str
    cross_sell: list[RecommendationResponse] = []


# ─── Opportunities ───────────────────────────────────────────────────────────


class OpportunityEvidenceResponse(BaseSchema):
    id: uuid.UUID
    evidence_type: str
    metric_name: str
    metric_value: float
    baseline_value: float | None
    description: str | None


class OpportunityResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    type: str
    status: str
    title: str
    description: str | None
    expected_impact: float
    confidence: float
    risk: str
    recommended_action: str | None
    required_approval: bool
    evidence: list[OpportunityEvidenceResponse] = []


# ─── Campaigns ───────────────────────────────────────────────────────────────


class CampaignCreate(BaseSchema):
    name: str
    campaign_type: str
    opportunity_id: uuid.UUID | None = None
    config: dict[str, Any] | None = None
    budget: float = 0.0


class CampaignDecisionRequest(BaseSchema):
    action: str  # "approve" | "reject"
    notes: str | None = None


class CampaignResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    campaign_type: str
    status: str
    budget: float
    actual_spend: float
    revenue_generated: float
    started_at: datetime | None
    ended_at: datetime | None


# ─── Experiments ─────────────────────────────────────────────────────────────


class ExperimentCreate(BaseSchema):
    name: str
    description: str | None = None
    experiment_type: str
    config: dict[str, Any] | None = None


class ExperimentResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    description: str | None
    experiment_type: str
    status: str
    config: dict[str, Any] | None
    metrics: dict[str, Any] | None
    started_at: datetime | None
    ended_at: datetime | None


# ─── Policies ────────────────────────────────────────────────────────────────


class PolicyCreate(BaseSchema):
    name: str
    policy_type: str
    rules: dict[str, Any]


class PolicyResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    policy_type: str
    rules: dict[str, Any]
    is_active: bool
    priority: int


class PolicyUpdate(BaseSchema):
    name: str | None = None
    rules: dict[str, Any] | None = None
    is_active: bool | None = None
    priority: int | None = None


class PolicyEvaluationRequest(BaseSchema):
    action_type: str
    input_data: dict[str, Any]


class PolicyEvaluationResponse(BaseSchema):
    decision: str
    reason: str | None = None
    policy_id: uuid.UUID | None = None
    evaluations: list[dict[str, Any]] = []


# ─── Approvals ───────────────────────────────────────────────────────────────


class ApprovalResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    agent_action_id: uuid.UUID | None
    status: str
    actor_type: str
    actor_id: str
    decision: str | None
    reason: str | None
    correlation_id: str | None


class ApprovalAction(BaseSchema):
    decision: str
    reason: str | None = None


# ─── Agent ───────────────────────────────────────────────────────────────────


class AgentRunResponse(BaseSchema):
    id: uuid.UUID
    agent_id: uuid.UUID
    agent_name: str
    merchant_id: uuid.UUID
    status: str
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    error: str | None
    tokens_used: int
    model_used: str | None
    duration_ms: int | None
    correlation_id: str | None
    started_at: datetime
    completed_at: datetime | None


# ─── Audit ───────────────────────────────────────────────────────────────────


class AuditEventResponse(BaseSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    actor_type: str
    actor_id: str
    action: str
    decision: str | None
    policy_result: str | None
    correlation_id: str | None
    created_at: datetime


# ─── Analytics ───────────────────────────────────────────────────────────────


class RevenueMetricsResponse(BaseSchema):
    total_revenue: float
    ai_attributed_revenue: float
    recovered_revenue: float
    average_order_value: float
    conversion_rate: float
    cart_abandonment_rate: float
    recommendation_ctr: float
    total_orders: int
    period: str


class DashboardResponse(BaseSchema):
    revenue_metrics: RevenueMetricsResponse
    active_opportunities: int
    pending_approvals: int
    active_campaigns: int
    recent_audit_events: list[AuditEventResponse] = []


# ─── Recovery ────────────────────────────────────────────────────────────────


class RecoveryCaseResponse(TimestampSchema):
    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID | None
    order_id: uuid.UUID | None
    cart_id: uuid.UUID | None
    case_type: str
    status: str
    potential_value: float
    recovered_value: float
    intervention_type: str | None


# ─── AI / Chat ───────────────────────────────────────────────────────────────


class ChatMessage(BaseSchema):
    role: str
    content: str


class ChatRequest(BaseSchema):
    messages: list[ChatMessage]
    session_id: str | None = None
    context: dict[str, Any] | None = None


class ChatResponse(BaseSchema):
    message: str
    data: dict[str, Any] | None = None
    actions: list[dict[str, Any]] = []
    correlation_id: str


# ─── Open Storefront (Agent-facing) ─────────────────────────────────────────


class StorefrontProductResponse(BaseSchema):
    id: uuid.UUID
    name: str
    description: str | None
    category: str
    price: float
    currency: str
    in_stock: bool
    images: list[str] | None


class StorefrontSearchRequest(BaseSchema):
    query: str | None = None
    category: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    limit: int = Field(default=20, ge=1, le=100)


class StorefrontCheckoutRequest(BaseSchema):
    items: list[CartItemCreate]
    customer_email: str | None = None


class StorefrontCheckoutResponse(BaseSchema):
    razorpay_order_id: str
    amount: float
    currency: str
    key_id: str
    order_id: uuid.UUID | None = None
    test_mode: bool = False


class PaginatedResponse(BaseSchema):
    items: list[Any]
    total: int
    limit: int
    offset: int


# ─── Integrations ───────────────────────────────────────────────────────────────


class CatalogSyncRequest(BaseSchema):
    sync_type: str = Field(description="json, api, or database")
    products_data: list[dict[str, Any]] | None = None
    api_config: dict[str, Any] | None = None
    db_config: dict[str, Any] | None = None


class CatalogSyncResponse(BaseSchema):
    sync_type: str
    products_created: int
    products_updated: int
    products_skipped: int
    errors: int
    status: str


class WidgetConfigRequest(BaseSchema):
    position: str | None = None
    theme: str | None = None
    primary_color: str | None = None
    welcome_message: str | None = None
    enable_recommendations: bool | None = None
    enable_cart_sync: bool | None = None
    auto_open: bool | None = None
    mobile_position: str | None = None


class WidgetEmbedResponse(BaseSchema):
    merchant_id: uuid.UUID
    script_url: str
    html_snippet: str
    react_snippet: str
    vue_snippet: str
    config: dict[str, Any]


class IntegrationResponse(TimestampSchema):
    id: uuid.UUID
    provider: str
    integration_type: str
    config: dict[str, Any] | None
    is_active: bool


class IntegrationListResponse(BaseSchema):
    integrations: list[IntegrationResponse]


class RecoveryInterventionRequest(BaseSchema):
    intervention_type: str = "reminder_message"


class OpportunityDecisionRequest(BaseSchema):
    action: str  # "approve" | "reject"
    notes: str | None = None


class VerifyPaymentRequest(BaseSchema):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class RazorpayConnectRequest(BaseSchema):
    key_id: str
    key_secret: str
    webhook_secret: str | None = None


class AIBuyerApiKeyResponse(BaseSchema):
    api_key: str
    warning: str = "Store this key now — it will not be shown again."


# ─── AI Buyer API ───────────────────────────────────────────────────────────────


class AIBuyerCartItemCreate(BaseSchema):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: int = Field(default=1, ge=1, le=10)


class AIBuyerCheckoutRequest(BaseSchema):
    items: list[AIBuyerCartItemCreate]
    session_id: str | None = None
    customer_email: str | None = None


class AIBuyerCheckoutResponse(BaseSchema):
    order_id: uuid.UUID
    order_number: str
    razorpay_order_id: str
    amount: float
    currency: str
    key_id: str
    checkout_url: str | None = None


class AIBuyerCartResponse(BaseSchema):
    cart_id: uuid.UUID
    session_id: str
    items: list[dict[str, Any]]
    subtotal: float
    currency: str
