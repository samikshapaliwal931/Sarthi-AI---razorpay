You are the principal backend architect and AI systems engineer for this project.

Build the backend for "Sarthi", an AI Revenue Agent for ecommerce merchants.

This is being built for the Razorpay AI Buildathon Track 01:
AI Growth & Agentic Commerce.

The product objective is:

"Grow the merchant's revenue and make the merchant transactable by AI buyers."

The backend must be production-grade, modular, testable, observable and secure.

Do NOT create a toy chatbot.

The system must implement:

DISCOVER
→ EXPLAIN
→ PROPOSE
→ GOVERN
→ APPROVE
→ EXECUTE
→ MEASURE
→ LEARN

CORE PRINCIPLE:

LLMs propose.
Deterministic software decides.
Policy engines authorize.
Execution services perform actions.
Audit systems record everything.
Evaluation systems measure outcomes.

Never allow an LLM to directly execute money-moving or merchant-impacting operations.

==================================================
TECHNOLOGY
==================================================

Python 3.12+

FastAPI

PostgreSQL

pgvector

Redis

Background worker architecture

Pydantic

SQLAlchemy

Alembic

OpenTelemetry

Pytest

HTTPX

Razorpay APIs

Razorpay Webhooks

MCP-compatible tool layer where useful

AI provider abstraction supporting multiple model providers

Do not tightly couple business logic to one LLM provider.

Use structured JSON outputs / typed schemas for all AI decisions.

==================================================
ARCHITECTURE
==================================================

Use a modular monolith first.

Do NOT create unnecessary microservices.

Organize by domain:

app/
  api/
  core/
  config/
  auth/
  database/
  models/
  schemas/
  repositories/
  services/
  agents/
  tools/
  policies/
  workflows/
  recommendations/
  analytics/
  attribution/
  recovery/
  campaigns/
  experiments/
  integrations/
  razorpay/
  webhooks/
  evaluation/
  learning/
  observability/
  audit/
  demo/
  tests/

Keep domain boundaries clean so components can later become services.

==================================================
TENANCY
==================================================

The platform is multi-tenant.

Every merchant must be isolated.

Every relevant database table must contain merchant_id or be safely tenant-scoped.

Never trust merchant_id supplied by the client.

Derive tenant identity from authenticated context.

Prevent cross-merchant data access.

Implement repository-level tenant filtering.

Add tests specifically for tenant isolation.

==================================================
DOMAIN MODEL
==================================================

Create database models for:

Merchant
MerchantSettings
MerchantIntegration
Product
ProductVariant
Inventory
Customer
Order
OrderItem
Cart
CartItem
Payment
PaymentAttempt
AbandonedCart
Opportunity
OpportunityEvidence
Recommendation
RecommendationEvent
Campaign
CampaignVariant
Experiment
ExperimentAssignment
Agent
AgentRun
AgentDecision
AgentAction
Policy
PolicyEvaluation
Approval
AuditEvent
RevenueAttribution
RecoveryCase
WebhookEvent
ModelEvaluation
ModelFeedback
LearningEvent

Use UUID identifiers.

Use timestamps everywhere.

Use immutable audit records.

==================================================
RAZORPAY INTEGRATION
==================================================

Implement Razorpay Test Mode integration.

Never expose Razorpay secrets to frontend.

Secrets must be stored using environment/secret management.

Implement:

Create order
Fetch order
Fetch payment
Verify payment signature
Payment status
Payment failure handling
Refund simulation/controlled refund workflow where required
Webhook processing

Implement webhook signature verification.

Implement webhook idempotency.

Store Razorpay event IDs.

Never process the same webhook twice.

Do not assume webhook ordering.

Create a durable webhook_events table.

Use event processing status:

RECEIVED
VALIDATED
PROCESSED
FAILED
IGNORED

Support retry.

The backend must use Razorpay webhooks as the authoritative asynchronous event mechanism and API verification when immediate user-facing verification is required.

==================================================
EVENT PIPELINE
==================================================

Create an internal event system.

Events:

product.created
product.updated
inventory.updated

order.created
order.paid
order.failed

payment.authorized
payment.captured
payment.failed

cart.created
cart.updated
cart.abandoned

recommendation.shown
recommendation.clicked
recommendation.accepted
recommendation.rejected

campaign.created
campaign.approved
campaign.executed

agent.run.started
agent.run.completed
agent.action.proposed
agent.action.blocked
agent.action.approved
agent.action.executed

Every event must contain:

event_id
merchant_id
event_type
timestamp
correlation_id
causation_id
payload
schema_version

==================================================
AI ARCHITECTURE
==================================================

Do NOT build one giant autonomous agent.

Use specialized intelligence components.

Recommended components:

1. Intent Agent

Understands customer/merchant natural language.

2. Retrieval Agent

Finds relevant products/data.

3. Recommendation Engine

Ranks products and cross-sell candidates.

4. Growth Analyst

Finds revenue opportunities.

5. Revenue Recovery Analyst

Detects recoverable revenue.

6. Campaign Planner

Converts opportunities into proposed campaigns.

7. Policy Engine

Deterministic. NOT an LLM.

8. Action Executor

Deterministic. NOT an LLM.

9. Attribution Engine

Measures whether an AI action caused measurable revenue.

10. Evaluation Agent

Evaluates recommendation quality and agent decisions.

11. Learning Engine

Updates ranking parameters and recommendation strategies from measured outcomes.

The agents should communicate using typed schemas, not free-form text.

==================================================
IMPORTANT:
DO NOT OVERUSE LLMs
==================================================

Use deterministic algorithms whenever possible.

Examples:

Product filtering:
SQL

Price filtering:
SQL

Inventory eligibility:
SQL

Product similarity:
pgvector

Frequently bought together:
co-occurrence statistics

Recommendation ranking:
hybrid scoring

Revenue calculation:
deterministic SQL

Policy enforcement:
deterministic rules

Attribution:
deterministic event logic

Only use an LLM where semantic reasoning is genuinely useful.

==================================================
RECOMMENDATION ENGINE
==================================================

Implement a hybrid recommender.

Candidate generation:

1. Frequently bought together
2. Category relationship
3. Product embedding similarity
4. Merchant-defined relationships
5. Popularity
6. Inventory availability
7. Price compatibility

Then calculate:

recommendation_score =

semantic_similarity
+ purchase_affinity
+ popularity
+ margin_signal
+ inventory_signal
+ contextual_relevance
- repetition_penalty

All weights must be configurable.

Do NOT allow the LLM to directly choose arbitrary products without retrieval and validation.

==================================================
CUSTOMER SHOPPING FLOW
==================================================

Customer:

"I need running shoes under ₹3000."

Pipeline:

Intent extraction

→ structured requirements

→ candidate retrieval

→ product validation

→ ranking

→ recommendation explanation

→ product response

Customer:

"Add the second one."

Resolve product from current context.

Validate product.

Create/update cart.

Customer:

"Add socks too."

Run cross-sell recommendation.

Validate stock.

Update cart.

Customer:

"Checkout."

Create Razorpay order.

Return safe checkout payload.

Payment occurs through Razorpay.

Verify payment.

Webhook confirms final state.

==================================================
GROWTH ANALYST
==================================================

Run scheduled analysis.

Analyze:

sales
inventory
AOV
conversion
cart abandonment
payment failures
product relationships
customer cohorts
revenue trends

Generate opportunities.

Examples:

CROSS_SELL

BUNDLE

UPSELL

ABANDONED_CART

PAYMENT_RECOVERY

INVENTORY

PRICE_EXPERIMENT

REPEAT_PURCHASE

Each opportunity must contain:

opportunity_id
merchant_id
type
title
description
evidence[]
expected_impact
confidence
risk
recommended_action
required_approval
policy_requirements

Never generate an opportunity without evidence.

==================================================
REVENUE IMPACT ESTIMATION
==================================================

Do not invent revenue numbers.

Create deterministic estimation models.

For example:

expected_incremental_revenue =

eligible_population
× baseline_conversion
× expected_lift
× incremental_aov

Store:

baseline
assumptions
confidence interval
historical evidence

Display the assumptions in the frontend.

==================================================
POLICY ENGINE
==================================================

This is one of the most important components.

Create a deterministic policy engine.

Policies:

maximum_discount_percent
maximum_campaign_budget
maximum_daily_spend
maximum_actions_per_hour
allowed_campaign_types
approval_required_above_amount
allowed_product_categories
refund_permissions
customer_contact_permissions

Policy evaluation returns:

ALLOW
BLOCK
REQUIRES_APPROVAL

Never allow an LLM to override policy.

Example:

AI proposes 15% discount.

Merchant limit = 10%.

Policy engine returns:

BLOCK

Reason:
"discount exceeds merchant maximum"

Record the policy evaluation.

==================================================
APPROVAL ENGINE
==================================================

Merchant-impacting actions may require approval.

Statuses:

PROPOSED
PENDING_APPROVAL
APPROVED
REJECTED
BLOCKED
EXECUTING
EXECUTED
FAILED

Every approval must record:

actor
timestamp
decision
reason
policy evaluation
action hash
correlation_id

==================================================
ACTION EXECUTOR
==================================================

Only deterministic code can execute actions.

Examples:

create_campaign
send_recovery_message
create_rzr_order
update_cart
apply_allowed_discount
start_experiment

Before execution:

validate schema
validate merchant
validate policy
validate inventory
validate current state
validate idempotency key

Then execute.

==================================================
AUDIT SYSTEM
==================================================

Every important AI and money-related action must generate an immutable audit event.

Store:

timestamp
merchant_id
actor_type
actor_id
agent_run_id
action
input_hash
decision
policy_result
approval_id
execution_result
error
correlation_id

Do not store unnecessary sensitive customer data.

==================================================
SELF-IMPROVEMENT
==================================================

IMPORTANT:

The system must NOT rewrite its own source code.

It must improve its decision policies and ranking through measurable feedback.

Implement a closed-loop learning architecture.

FLOW:

Recommendation

→ impression

→ click

→ add_to_cart

→ purchase

→ revenue

→ attribution

→ evaluation

→ learning event

→ model/ranking update candidate

→ offline evaluation

→ promotion only if evaluation passes

Use:

A/B testing

bandit-style exploration

weighted ranking

historical conversion

product affinity

contextual features

merchant-specific learning

==================================================
BANDIT SYSTEM
==================================================

For recommendations, implement a lightweight contextual bandit or epsilon-greedy strategy.

Example:

90% exploit best-performing recommendation

10% explore alternatives

Track:

impressions
clicks
ATC
purchase
revenue

Use merchant-level and product-level statistics.

Never experiment with unsafe financial actions.

Experiments must remain inside merchant-configured policy limits.

==================================================
EVALUATION ENGINE
==================================================

Create offline evaluation datasets.

Metrics:

recommendation precision
click-through rate
add-to-cart rate
conversion rate
attach rate
revenue per session
incremental revenue
false recommendation rate

For Growth Agent:

opportunity acceptance rate
opportunity execution rate
predicted vs actual impact
blocked-action rate
failed-action rate

For Recovery:

recovery rate
recovered revenue
intervention cost

Create evaluation runs.

Before promoting a new ranking strategy:

compare against baseline.

Only promote if predefined thresholds are met.

==================================================
MODEL ROUTER
==================================================

Create an AI provider abstraction.

Example interface:

LLMProvider

methods:

generate_structured()
embed()
classify()
rerank()

Allow providers to be switched through configuration.

Use cheaper/smaller models for:

classification
intent extraction
simple summaries
metadata extraction

Use stronger models only for:

complex merchant analysis
ambiguous recommendations
campaign reasoning
multi-step planning

Do not call expensive models for every request.

==================================================
EMBEDDINGS
==================================================

Use pgvector.

Embed:

product title
description
category
attributes
use cases

Use vector retrieval for semantic product search.

Combine vector similarity with deterministic filters.

Never recommend:

out-of-stock products
invalid variants
disallowed products
products outside requested budget

==================================================
MCP / AGENT INTERFACE
==================================================

Expose a clean tool layer.

Tools:

search_products
get_product
get_inventory
get_customer_context
get_cart
add_to_cart
remove_from_cart
create_checkout
get_order
get_payment_status
find_growth_opportunities
get_revenue_metrics
propose_campaign
evaluate_policy
get_recommendations

Tools must have strict typed schemas.

Read tools and write tools must be clearly separated.

Write tools require policy validation.

==================================================
AI BUYER / OPEN STOREFRONT
==================================================

Create an external agent-facing API.

Capabilities:

catalog discovery
product search
product details
availability
cart
checkout session
order status

The interface should be designed so another AI agent can transact with the merchant.

Do not expose internal merchant analytics.

Only expose explicitly allowed commerce capabilities.

==================================================
ATTRIBUTION
==================================================

This is critical.

When Sarthi recommends a product, create:

recommendation_event_id

Attach it to the session/cart/order.

If the customer purchases:

attribute the order/revenue to the recommendation.

Support attribution types:

DIRECT
ASSISTED
RECOVERY
CAMPAIGN
UPSELL
CROSS_SELL

Do not claim revenue impact without attribution evidence.

==================================================
OBSERVABILITY
==================================================

Implement:

structured logging
correlation IDs
agent run IDs
latency
token usage
model usage
tool calls
errors
policy blocks
execution results

Add OpenTelemetry-compatible instrumentation.

Track:

AI latency
retrieval latency
database latency
Razorpay latency
agent execution time

==================================================
SECURITY
==================================================

Never expose:

Razorpay API secrets
AI provider secrets
webhook secrets

Use environment variables.

Validate all external inputs.

Use authentication.

Implement authorization.

Tenant isolation.

Rate limiting.

Idempotency.

Webhook signature verification.

SQL injection protection through ORM/parameterized queries.

Do not allow arbitrary tool invocation.

==================================================
DEMO MODE
==================================================

Create a complete synthetic merchant.

Merchant:

Stride Athletics

Seed:

150 products
5000 customers
12000 orders
1000 abandoned carts
payment failures
inventory levels
product relationships
recommendation history
revenue history

The demo must reproduce a compelling revenue story.

Example:

Before Sarthi:

AOV ₹2,780

After recommendation:

AOV ₹3,120

Recovered revenue:

₹21,700

AI-attributed revenue:

₹63,420

These are synthetic demo numbers and must be clearly marked as demo data.

==================================================
DEMO SCENARIOS
==================================================

Create automated demo scenarios.

SCENARIO 1

Merchant asks:

"What is my biggest revenue opportunity?"

Sarthi identifies abandoned carts.

SCENARIO 2

Merchant asks:

"Find cross-sell opportunities."

Sarthi identifies shoes + socks.

SCENARIO 3

Merchant approves campaign.

Policy engine validates.

Campaign executes.

SCENARIO 4

Customer asks:

"I need running shoes under ₹3000."

AI recommends products.

AI cross-sells socks.

Customer adds to cart.

Razorpay order created.

SCENARIO 5

Payment fails.

System handles failure gracefully.

No duplicate order.

Customer can retry.

SCENARIO 6

AI attempts an invalid discount.

Policy blocks it.

Audit trail records the block.

==================================================
TESTING
==================================================

Write tests for:

tenant isolation
recommendation ranking
inventory validation
price filtering
policy enforcement
approval workflow
Razorpay signature validation
webhook idempotency
duplicate payment events
payment failure
cart consistency
attribution
agent tool authorization
learning promotion
A/B experiment assignment

Create integration tests.

Create end-to-end tests for:

customer → product → cart → checkout

merchant → opportunity → approval → execution

payment → webhook → attribution

==================================================
API
==================================================

Create versioned REST APIs:

/api/v1/auth
/api/v1/merchant
/api/v1/products
/api/v1/customers
/api/v1/orders
/api/v1/carts
/api/v1/payments
/api/v1/recommendations
/api/v1/opportunities
/api/v1/campaigns
/api/v1/recovery
/api/v1/experiments
/api/v1/analytics
/api/v1/agents
/api/v1/audit
/api/v1/policies
/api/v1/integrations
/api/v1/ai

Generate OpenAPI documentation.

Keep frontend DTOs stable.

==================================================
FRONTEND CONTRACT
==================================================

The frontend will be generated separately in Lovable.

Create clean API contracts for:

Dashboard
AI Copilot
Opportunities
Products
Orders
Customers
Recovery
Campaigns
Experiments
Agent Activity
Audit
Policies
Shopper Chat
Cart
Checkout

Return structured JSON.

Never return UI-specific HTML from backend.

==================================================
QUALITY BAR
==================================================

Do not create fake endpoints that always return success.

Do not hard-code business results.

Do not put business logic in route handlers.

Do not allow LLMs to perform unrestricted actions.

Do not create unnecessary microservices.

Do not create unnecessary agents.

Prefer deterministic algorithms where possible.

Every important AI output must be traceable to evidence.

Every money-related action must be:

EXPLAINABLE
BOUNDED
GATED
AUDITABLE
IDEMPOTENT

Build this as if the backend will eventually serve thousands of merchants.

Start with architecture and schema.

Then implement domain models.

Then repositories/services.

Then Razorpay integration.

Then recommendation engine.

Then agents.

Then policy/approval.

Then attribution.

Then learning/evaluation.

Then API.

Then tests.

Do not skip foundational layers.