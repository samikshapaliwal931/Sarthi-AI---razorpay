# Sarthi AI — Product & Project Goal Manual

## 1. Purpose of This Manual

This document is the source of truth for understanding **what Sarthi is, why we are building it, what the user experience should accomplish, and what the system must ultimately deliver**.

An AI coding agent, architect, or developer should read this document before making significant changes to the project.

The most important rule is:

> **Do not optimize individual features while losing the overall Sarthi goal. Every implementation decision must support the product described here.**

This is a product-goal manual, not a complete low-level API specification. Technical implementation may evolve, but the product intent, boundaries, workflows, and principles below should remain intact unless explicitly changed.

---

# 2. What Is Sarthi?

**Sarthi** is an AI-powered revenue and commerce intelligence layer that sits on top of an existing merchant's e-commerce infrastructure.

Sarthi helps a merchant:

1. **Increase revenue** through AI-assisted shopping, recommendations, cross-sells, upsells, and recovery.
2. **Become AI-buyable** so external AI agents can discover products and transact with the merchant.
3. **Use AI safely** by placing deterministic policies and merchant controls between AI decisions and money-moving actions.
4. **Understand AI impact** by tracking what the AI recommended, what happened, and how much revenue was influenced.

Sarthi is **not intended to replace the merchant's existing store, inventory system, order system, or payment gateway**.

It is an intelligence and agentic commerce layer around them.

---

# 3. The Core Problem

Modern merchants already have:

- A storefront
- Product catalog
- Inventory
- Orders
- Customers
- Payment infrastructure

But these systems generally do not provide an intelligent agent that can:

- Understand a shopper's natural-language intent
- Find appropriate products
- Explain recommendations
- Cross-sell and upsell intelligently
- Recover lost revenue
- Propose growth actions
- Allow external AI shopping agents to interact with the store
- Safely perform commerce actions under merchant-defined rules
- Explain why an AI-driven action happened

Sarthi exists to solve this gap.

---

# 4. The Core Product Promise

The product should ultimately demonstrate this simple idea:

> **A merchant can connect their existing commerce infrastructure to Sarthi, give Sarthi access to the right business data, define what AI is allowed to do, and then let AI assist or conduct commerce while deterministic software controls every sensitive action.**

The key philosophy is:

> **LLMs propose. Software decides.**

The AI should never be the final authority over money-moving actions.

---

# 5. The Three Major Sarthi Surfaces

Sarthi consists of three connected product surfaces.

## 5.1 Sarthi Assist

Sarthi Assist is the shopper-facing conversational commerce assistant.

It appears as a chat experience on a merchant's existing storefront.

A shopper can:

- Ask what product is suitable
- Describe what they need naturally
- Search the merchant's catalog conversationally
- Ask product questions
- Receive recommendations
- See complementary products
- Add products to a cart
- Review a proposed order
- Proceed through checkout
- Receive explanations for recommendations

Example:

Shopper:

> "I need running shoes under ₹5,000 for daily use."

Sarthi should:

1. Understand the intent.
2. Retrieve appropriate products.
3. Check current product information.
4. Rank suitable candidates.
5. Explain why the recommendations fit.
6. Allow the shopper to choose.
7. Build/update the cart.
8. Propose checkout.
9. Pass the proposed action through the policy system.
10. Complete payment only through the authorized payment integration.
11. Record the action in the audit trail.

Sarthi Assist should feel like a knowledgeable sales assistant, not a generic chatbot.

---

# 6. Sarthi Open Storefront

Sarthi Open Storefront makes the merchant's store understandable and usable by external AI buyers.

The idea is:

> **A merchant should not only be able to sell to humans through a website; their products should also be discoverable and purchasable by AI agents.**

External AI agents should be able to:

- Discover the merchant
- Search products
- Retrieve product information
- Check availability
- Create/manage carts
- Initiate checkout
- Complete an authorized transaction
- Check order status

The AI Buyer interface must use structured, predictable commerce operations rather than requiring an external agent to scrape the merchant website.

This surface is therefore an **agent-readable commerce interface**.

---

# 7. Sarthi Growth Copilot

Growth Copilot is the merchant-facing intelligence layer.

It analyzes available commerce information and identifies opportunities such as:

- Abandoned-cart recovery
- Cross-sell opportunities
- Upsell opportunities
- Product combinations
- Slow-moving products
- Low-stock situations
- Pricing opportunities
- Campaign opportunities

The AI should produce a proposed action rather than silently changing business behavior.

Example:

> "Customers who purchase Product A frequently purchase Product B. A bundled offer could increase conversion. Estimated impact: X."

The merchant can then:

- Approve
- Reject
- Edit

Any action that can affect money or commercial behavior must still pass through the relevant deterministic controls.

---

# 8. How the Three Surfaces Fit Together

These are not three unrelated applications.

They are three interfaces to the same underlying commerce intelligence platform.

```text
                    SARTHI
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
 Sarthi Assist   Open Storefront   Growth Copilot
        |              |              |
        +--------------+--------------+
                       |
              Shared Intelligence
                       |
        +--------------+--------------+
        |              |              |
     Retrieval     Recommendations   Agents
        |              |              |
        +--------------+--------------+
                       |
                 Policy Layer
                       |
                Commerce Actions
                       |
             Merchant Infrastructure
                       |
        +--------------+--------------+
        |              |              |
     Catalog       Inventory       Payments
     Orders        Customers       Store
```

The important architectural concept is **shared controls and shared business truth**.

---

# 9. Merchant's Existing Infrastructure

Sarthi assumes the merchant already has commerce infrastructure.

Depending on the merchant, this can include:

- Shopify
- WooCommerce
- Custom storefront
- Product database
- Inventory system
- Order management system
- Razorpay or another payment integration

Sarthi should integrate with these systems rather than unnecessarily rebuilding them.

The merchant's existing systems remain the authoritative source for live transactional information.

---

# 10. Data: What Sarthi Needs

The AI must have access to relevant merchant information.

Typical information includes:

## Product information

- Product name
- Description
- Category
- Brand
- Price
- Attributes
- Variants
- Images/references
- Product relationships

## Inventory information

- Current stock
- Variant availability
- Availability status

## Commerce information

- Orders
- Order items
- Cart activity
- Conversion information
- Customer behavior where legally and operationally appropriate

## Business information

- Store policies
- Return policy
- Shipping information
- Product FAQs
- Size guides
- Merchant-defined selling rules

---

# 11. Retrieval and RAG

Sarthi can use retrieval and RAG for information that benefits from semantic search.

Examples:

- Product descriptions
- FAQs
- Size guides
- Store policies
- Product documentation
- Unstructured product information

A conceptual flow is:

```text
Merchant Data
     |
     v
Ingestion
     |
     v
Chunking / Normalization
     |
     v
Embeddings
     |
     v
Vector Store
     |
     v
Relevant Context
     |
     v
LLM
```

However:

> **RAG is a component of Sarthi, not the definition of Sarthi.**

Sarthi is an agentic commerce system.

Live transactional information should come from authoritative tools/services when required.

For example:

- Current price → live commerce/catalog source
- Current inventory → live inventory source
- Cart state → cart service
- Order state → order service
- Payment state → payment gateway/webhook
- Merchant permissions → policy system

Do not make a vector database the authoritative source for rapidly changing transactional state.

---

# 12. AI Agent Model

Sarthi should be treated as an agentic system rather than a simple chatbot.

A typical interaction is:

```text
User
  ↓
Conversation
  ↓
Intent Understanding
  ↓
Retrieve Information
  ↓
Reason / Recommend
  ↓
Propose Action
  ↓
Policy Gate
  ↓
Authorized Tool
  ↓
External Commerce System
  ↓
Result
  ↓
Explain Result
  ↓
Audit
```

The LLM can reason and propose.

The application controls what tools exist and what those tools are allowed to do.

---

# 13. The Most Important Safety Principle

Never allow:

```text
LLM → Payment Gateway
```

The intended architecture is:

```text
LLM
 ↓
Proposed Action
 ↓
Deterministic Policy Gate
 ↓
Authorized Commerce Service
 ↓
Payment Gateway
```

The AI must not be able to bypass the policy system.

---

# 14. Policy Gate

The Policy Gate is one of the most important parts of Sarthi.

It provides deterministic control over sensitive AI actions.

Examples of policies include:

- Maximum transaction amount
- Confirmation threshold
- Maximum discount
- Maximum campaign budget
- Allowed product/category actions
- Daily AI spending limit
- Feature enable/disable controls
- Approval requirements

The policy engine should be deterministic, testable, and independent from LLM reasoning.

---

# 15. Payment Safety

Commerce actions must be designed to avoid duplicate or unintended transactions.

Important concepts include:

- Idempotency
- Duplicate-order detection
- Transaction limits
- Explicit confirmation where required
- Payment state handling
- Webhook verification
- Retry handling
- Audit logging

A retry must not accidentally create another payment.

---

# 16. Auditability

Every important AI-driven commerce action should be explainable after the fact.

The system should be able to answer:

- What did the user ask?
- What did the AI understand?
- What information was retrieved?
- What did the AI recommend?
- Why was it recommended?
- What action did the AI propose?
- Which policy was evaluated?
- Was it allowed?
- Was confirmation required?
- What happened after execution?
- What payment/order resulted?
- What was the final outcome?

The goal is not merely "logs exist."

The goal is:

> **A merchant can reconstruct the reasoning and execution path of a money-relevant AI action.**

---

# 17. Attribution

Sarthi must distinguish between:

- Normal/manual commerce
- AI-influenced commerce
- AI-assisted purchases
- AI-generated recommendations
- AI-driven growth actions

The merchant should be able to understand whether Sarthi actually produced business value.

Important measurements include:

- AI-attributed revenue
- Conversion rate
- Average order value
- Recommendation impressions
- Recommendation clicks
- Recommendation acceptance
- Cross-sell conversion
- Upsell conversion
- Recovery conversion
- Campaign performance

Do not claim AI impact merely because an AI interaction occurred.

Attribution should be based on measurable events.

---

# 18. Merchant Experience

The merchant should be able to:

1. Register.
2. Connect their commerce data.
3. Sync/import their catalog.
4. Connect payments.
5. Configure AI policies.
6. Install the Sarthi widget.
7. Enable relevant Sarthi capabilities.
8. Monitor AI activity.
9. Review opportunities.
10. Approve/reject growth actions.
11. Review revenue impact.
12. Inspect the audit trail.

The onboarding should make it clear what Sarthi can access and what it can do.

---

# 19. Shopper Experience

The shopper should experience Sarthi as a natural shopping assistant.

The interaction should generally be:

```text
Need
 ↓
Understand
 ↓
Search
 ↓
Recommend
 ↓
Explain
 ↓
Choose
 ↓
Cart
 ↓
Checkout
 ↓
Payment
 ↓
Confirmation
```

Avoid making the shopper understand internal agent architecture.

The complexity should stay behind the interface.

---

# 20. External AI Buyer Experience

An external AI agent should be able to perform structured commerce operations.

Conceptually:

```text
Discover
   ↓
Search
   ↓
Inspect
   ↓
Compare
   ↓
Create Cart
   ↓
Add Items
   ↓
Checkout
   ↓
Policy / Authorization
   ↓
Payment
   ↓
Order
```

The interface must be predictable enough for machines to use reliably.

---

# 21. What Sarthi Is NOT

Sarthi is not:

- Merely a chatbot.
- Merely a RAG application.
- Merely a recommendation engine.
- Merely a payment wrapper.
- Merely an analytics dashboard.
- A replacement for Shopify/WooCommerce.
- A replacement for the merchant's inventory system.
- An autonomous AI that can spend money without constraints.

It is the combination of:

> **AI agents + commerce intelligence + retrieval + recommendations + agent-readable commerce + deterministic governance + payment orchestration + attribution.**

---

# 22. Non-Negotiable Design Principles

## Principle 1 — LLMs Propose, Software Decides

Never allow model output to directly determine a sensitive side effect.

## Principle 2 — Live Data Wins

For transactional information, use authoritative live systems.

## Principle 3 — RAG Is Supporting Infrastructure

Use RAG where semantic retrieval helps, but do not confuse RAG with the entire product.

## Principle 4 — Policy Before Money

Every money-relevant AI action must pass through deterministic controls.

## Principle 5 — Explainability

Important recommendations and actions need understandable reasons.

## Principle 6 — Audit Everything Important

Commerce actions must be reconstructable.

## Principle 7 — Multi-Tenant Isolation

Merchant data must never leak across tenants.

## Principle 8 — Idempotent Commerce

Retries must be safe.

## Principle 9 — Human Control

Merchants must be able to configure limits and approve sensitive actions.

## Principle 10 — Do Not Build Unnecessary Replacements

Integrate with existing merchant infrastructure wherever practical.

---

# 23. The Golden End-to-End Example

This is the canonical example an AI developer should understand.

A shopper says:

> "I need running shoes for daily running under ₹5,000."

Sarthi:

### Step 1 — Understand

Intent agent identifies:

- Product category: running shoes
- Use case: daily running
- Budget: ₹5,000

### Step 2 — Retrieve

Sarthi searches authoritative catalog/product information and, where useful, semantic product knowledge.

### Step 3 — Rank

Recommendation logic ranks suitable products.

### Step 4 — Explain

Sarthi tells the shopper why the selected products fit.

### Step 5 — Cross-sell

If appropriate, Sarthi may propose a relevant complementary product.

It must respect merchant-defined limits.

### Step 6 — Cart

The shopper chooses a product and Sarthi updates the cart.

### Step 7 — Checkout Proposal

Sarthi proposes the order.

### Step 8 — Policy Gate

The deterministic policy system evaluates the proposed action.

For example:

```text
Amount: ₹4,200
Auto-approve limit: ₹5,000
Category allowed: YES
Duplicate order: NO
Daily AI limit: NOT EXCEEDED
Confirmation required: NO
```

### Step 9 — Execute

The authorized commerce/payment service creates the appropriate transaction.

### Step 10 — Verify

Payment/webhook state is processed.

### Step 11 — Audit

The system records the complete action trail.

### Step 12 — Explain

The shopper receives the final order/payment result.

This single workflow demonstrates the central Sarthi thesis:

> **AI can participate in commerce without becoming an uncontrolled authority over commerce.**

---

# 24. What the AI Developer Must Preserve

When modifying Sarthi, the AI developer should always ask:

### Product question

"Does this change help Sarthi increase merchant revenue, enable AI commerce, improve governance, or measure impact?"

### Architecture question

"Does this change preserve separation between AI reasoning and deterministic execution?"

### Data question

"Am I using the correct authoritative source for this information?"

### Security question

"Can an AI model bypass a permission, policy, tenant boundary, or payment control?"

### UX question

"Does this make the merchant/shopper experience clearer or more useful?"

### Reliability question

"What happens if this operation is retried, duplicated, delayed, or fails?"

### Audit question

"Can we later explain what happened?"

If the answer is no, reconsider the implementation.

---

# 25. Definition of Success

Sarthi is successful when a demo or production deployment can clearly demonstrate all of the following:

### Merchant

The merchant connects existing commerce infrastructure.

### Intelligence

Sarthi understands commerce data and shopper intent.

### Recommendation

Sarthi produces useful, explainable recommendations.

### Conversation

A shopper can interact naturally with the store.

### Commerce

The shopper can actually proceed through checkout.

### AI Buyer

An external AI agent can interact with the merchant's structured commerce interface.

### Governance

Sensitive AI actions are controlled by deterministic policies.

### Payment

Money-moving actions are safely executed through the payment infrastructure.

### Attribution

The merchant can measure the business effect.

### Audit

The merchant can inspect why an important AI action happened.

If these pieces work together, **that is Sarthi**.

---

# 26. Final Mental Model

Whenever an AI agent works on this repository, it should retain this mental model:

```text
                         SARTHI
                           |
        ┌──────────────────┼──────────────────┐
        |                  |                  |
        v                  v                  v
   SHOPPER AI         AI BUYER API       GROWTH AI
        |                  |                  |
        └──────────────────┼──────────────────┘
                           |
                    AI / AGENT LAYER
                           |
             ┌─────────────┴─────────────┐
             |                           |
        RETRIEVAL                  RECOMMENDATION
             |                           |
             └─────────────┬─────────────┘
                           |
                    PROPOSED ACTION
                           |
                    POLICY GATE
                           |
                    AUTHORIZED TOOL
                           |
              ┌────────────┼────────────┐
              |            |            |
           CATALOG      ORDERS       PAYMENT
              |            |            |
              └────────────┼────────────┘
                           |
                     AUDIT + ATTRIBUTION
                           |
                    MERCHANT CONTROL
```

**The goal is not to build an LLM with a product database.**

**The goal is to build a governed agentic commerce layer that lets merchants safely participate in the AI-driven buying ecosystem and measurably grow revenue.**

---

# 27. Instruction to Future AI Agents

Before changing Sarthi, read this document completely.

Do not reduce Sarthi to "a RAG chatbot."

Do not allow the LLM to directly perform sensitive side effects.

Do not replace live transactional data with stale semantic retrieval.

Do not add features merely because they are technically interesting.

Every major implementation should map back to one or more of these outcomes:

1. **Help shoppers buy better.**
2. **Help merchants sell more.**
3. **Make merchants AI-buyable.**
4. **Keep AI actions bounded and governed.**
5. **Make AI commerce explainable and auditable.**
6. **Measure whether Sarthi actually creates value.**

That is the purpose of the Sarthi project.
