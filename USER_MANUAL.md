# Sarthi AI - User Manual

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Idea](#core-idea)
3. [Architecture](#architecture)
4. [Backend Documentation](#backend-documentation)
5. [Frontend Documentation](#frontend-documentation)
6. [Integration Guide](#integration-guide)
7. [API Reference](#api-reference)
8. [Deployment](#deployment)

---

## Project Overview

**Sarthi** is an AI-powered revenue intelligence platform for e-commerce merchants. It acts as an "intelligence layer" on top of existing merchant infrastructure (Shopify, WooCommerce, custom stores) to:

- **Discover Revenue Opportunities**: Analyze catalog, orders, and customer behavior to find growth opportunities
- **Provide AI Suggestions**: Offer cross-sell, upsell, and recovery recommendations
- **Enable AI Buyers**: Allow external AI agents to transact with merchant stores
- **Govern Actions**: Policy engine ensures AI actions stay within merchant-defined limits
- **Measure Impact**: Track attribution and revenue impact of AI-driven decisions

### Target Users
- E-commerce merchants using platforms like Shopify, WooCommerce, or custom solutions
- Store owners looking to increase revenue through AI-driven insights
- Businesses wanting to enable AI agents to purchase from their stores

---

## Core Idea

### The Problem
Merchants have existing e-commerce infrastructure (catalog, inventory, payments) but lack:
- Intelligent revenue optimization
- AI-driven customer engagement
- Ability to transact with AI buyers
- Automated recovery of lost revenue

### The Solution
Sarthi plugs into existing merchant systems as an intelligence layer:

```
MERCHANT'S EXISTING STORE
│
├── Product Catalog (Shopify/WooCommerce/Custom)
├── Inventory System
├── Payment Gateway (Razorpay)
└── Order Management
         │
         ▼
    SARTHI AI LAYER
│
├── Catalog Sync (imports merchant data)
├── AI Agents (Intent, Retrieval, Growth, Conversation)
├── Recommendation Engine (cross-sell, upsell)
├── Policy Engine (governs AI actions)
├── Approval Workflow (human oversight)
├── Attribution Tracking (measures AI impact)
└── AI Buyer API (enables AI transactions)
         │
         ▼
    REVENUE GROWTH
```

### Key Principles
1. **LLMs Propose, Software Decides**: AI suggests actions, deterministic code executes them
2. **Read Broadly, Write Narrowly**: Sarthi reads merchant data but only writes within policy limits
3. **Multi-Tenant**: Each merchant's data is isolated
4. **Audit Trail**: Every action is logged and attributable
5. **Policy-First**: Merchants control what AI can do

---

## Architecture

### Technology Stack

**Backend (Python/FastAPI)**
- FastAPI for REST API
- PostgreSQL + pgvector for data and embeddings
- Redis for caching
- SQLAlchemy for ORM
- OpenAI/Anthropic for LLM integration

**Frontend (React/TanStack)**
- React with TypeScript
- TanStack Router for routing
- TailwindCSS for styling
- shadcn/ui components
- Lucide icons

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  Dashboard | Analytics | Integrations | Campaigns | Settings │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Layer   │  │  Services    │  │  Agents      │      │
│  │  /api/v1/*   │  │  Business    │  │  AI Logic    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Repositories │  │ Integrations│  │  Razorpay    │      │
│  │  Data Access │  │  Sync/Widget │  │  Payments    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL + pgvector                           │
│  Merchants | Products | Orders | Recommendations | Embeddings│
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Documentation

### API Endpoints

#### Authentication (`/api/v1/auth`)
- **POST /register** - Register new merchant
- **POST /login** - Login and get JWT token
- **POST /logout** - Logout

#### Merchant (`/api/v1/merchant`)
- **GET /merchant** - Get merchant profile
- **GET /merchant/settings** - Get merchant settings (discount limits, policy flags)
- **PUT /merchant/settings** - Update merchant settings

#### Products (`/api/v1/products`)
- **GET /products** - Search products with filters (query, category, price, brand, stock)
- **POST /products** - Create new product
- **GET /products/categories** - Get all product categories
- **GET /products/{id}** - Get product details
- **GET /products/{id}/inventory** - Get product inventory
- **PUT /products/{id}/inventory** - Update product inventory

#### Orders (`/api/v1/orders`)
- **GET /orders** - List orders with pagination
- **GET /orders/{id}** - Get order details
- **PUT /orders/{id}/status** - Update order status

#### Customers (`/api/v1/customers`)
- **GET /customers** - List customers
- **GET /customers/{id}** - Get customer details

#### Payments (`/api/v1/payments`)
- **GET /payments** - List payments
- **POST /payments/webhook** - Razorpay webhook handler

#### Recommendations (`/api/v1/recommendations`)
- **GET /recommendations** - List all recommendations
- **POST /recommendations** - Get personalized recommendations
- **POST /recommendations/events** - Record recommendation events (shown, clicked, accepted)

#### Opportunities (`/api/v1/opportunities`)
- **GET /opportunities** - List revenue opportunities
- **POST /opportunities/{id}/approve** - Approve opportunity action
- **POST /opportunities/{id}/reject** - Reject opportunity action

#### Policies (`/api/v1/policies`)
- **GET /policies** - List active policies
- **POST /policies** - Create new policy

#### Analytics (`/api/v1/analytics`)
- **GET /analytics/revenue** - Revenue analytics
- **GET /analytics/conversion** - Conversion metrics
- **GET /analytics/attribution** - AI attribution data

#### AI Chat (`/api/v1/ai`)
- **POST /ai/chat** - Chat with Sarthi AI assistant

#### Storefront (`/api/v1/storefront`)
- **POST /storefront/search** - Public product search
- **GET /storefront/products/{id}** - Public product details
- **GET /storefront/products/{id}/availability** - Check stock availability
- **POST /storefront/cart/{session}/add** - Add item to cart
- **GET /storefront/cart/{session}** - Get cart
- **POST /storefront/checkout** - Create checkout session
- **POST /storefront/recommendations** - Get storefront recommendations

#### Integrations (`/api/v1/integrations`)
- **POST /integrations/catalog/sync** - Sync product catalog (JSON/CSV/API/Database)
- **POST /integrations/widget/generate** - Generate embed code for widget
- **GET /integrations/widget/js** - Get widget JavaScript file
- **GET /integrations/widget/no-code/{platform}** - Get no-code platform snippet
- **GET /integrations** - List all integrations
- **POST /integrations/razorpay/connect** - Connect Razorpay account
- **DELETE /integrations/{id}** - Delete integration

#### AI Buyer API (`/api/v1/ai-buyer`)
- **POST /ai-buyer/search** - AI buyer: Search catalog
- **GET /ai-buyer/products/{id}** - AI buyer: Get product details
- **GET /ai-buyer/catalog** - AI buyer: Get full catalog
- **POST /ai-buyer/cart/create** - AI buyer: Create cart
- **POST /ai-buyer/cart/{id}/add** - AI buyer: Add to cart
- **GET /ai-buyer/cart/{id}** - AI buyer: Get cart
- **POST /ai-buyer/checkout** - AI buyer: Create checkout
- **GET /ai-buyer/order/{id}** - AI buyer: Get order status
- **POST /ai-buyer/recommendations** - AI buyer: Get recommendations

#### Agent Activity (`/api/v1/agent-activity`)
- **GET /agent-activity** - List AI agent activities
- **GET /agent-activity/{id}** - Get activity details

#### Campaigns (`/api/v1/campaigns`)
- **GET /campaigns** - List campaigns
- **POST /campaigns** - Create campaign
- **GET /campaigns/{id}** - Get campaign details

#### Experiments (`/api/v1/experiments`)
- **GET /experiments** - List A/B experiments
- **POST /experiments** - Create experiment

### Backend Services

#### ProductService
Manages product catalog operations:
- Create, update, delete products
- Search with filters
- Category management
- Inventory tracking

#### OrderService
Handles order lifecycle:
- Create orders from carts
- Update order status
- Revenue statistics

#### CartService
Shopping cart management:
- Create/get carts by session
- Add/remove items
- Calculate totals

#### GrowthAnalystService
Revenue opportunity analysis:
- Analyze abandoned carts
- Identify cross-sell opportunities
- Detect pricing optimization chances

#### RecommendationEngine
Product recommendation logic:
- Collaborative filtering
- Content-based filtering
- Hybrid scoring
- Cross-sell/upsell logic

### AI Agents

#### IntentAgent
Extracts user intent from messages:
- Search intent
- Cross-sell intent
- Product inquiry
- General queries

#### RetrievalAgent
Retrieves relevant data:
- Product search with inventory
- Product details
- Catalog summary

#### GrowthAgent
Analyzes growth opportunities:
- Revenue opportunities
- Campaign suggestions
- Performance insights

#### ConversationAgent
Main chat orchestrator:
- Routes to appropriate agent
- Formats responses
- Maintains conversation context

---

## Frontend Documentation

### Pages/Routes

#### Dashboard (`/`)
**Purpose**: Main overview of store performance and AI activity

**Features**:
- Revenue metrics (total, growth rate)
- AI attribution (revenue influenced by AI)
- Active opportunities count
- Recent recommendations
- Quick actions

**Key Metrics Displayed**:
- Total Revenue
- AI-Attributed Revenue
- Conversion Rate
- Active Opportunities
- Recent Orders

#### Analytics (`/analytics`)
**Purpose**: Detailed analytics and performance insights

**Features**:
- Revenue trends over time
- Conversion funnel
- Attribution breakdown
- Customer segments
- Product performance

**Charts**:
- Revenue line chart
- Conversion bar chart
- Attribution pie chart
- Category performance

#### Opportunities (`/opportunities`)
**Purpose**: View and act on revenue opportunities

**Features**:
- List of AI-discovered opportunities
- Opportunity types (abandoned cart, cross-sell, pricing)
- Expected impact and confidence scores
- Approve/reject actions
- Opportunity details panel

**Opportunity Types**:
- **Abandoned Cart Recovery**: Recover lost sales
- **Cross-Sell**: Suggest complementary products
- **Pricing Optimization**: Adjust prices for better conversion
- **Low Stock Alert**: Replenish inventory

#### Campaigns (`/campaigns`)
**Purpose**: Manage marketing campaigns

**Features**:
- Create new campaigns
- Campaign variants (A/B testing)
- Performance tracking
- Budget management

#### Integrations (`/integrations`)
**Purpose**: Connect external systems

**Features**:
- **Catalog Sync**: Import products from Shopify, WooCommerce, or JSON/CSV
- **Widget Generation**: Get embed code for AI chat widget
- **Razorpay**: Connect payment gateway
- **Email**: Configure transactional emails
- **WhatsApp**: Set up WhatsApp Business
- **Analytics**: Connect web analytics

**Integration Actions**:
- Sync products (JSON/CSV/API)
- Generate widget code (HTML/React/Vue)
- Connect Razorpay
- Configure email settings

#### Settings (`/settings`)
**Purpose**: Configure merchant settings and policies

**Features**:
- **Policy Settings**:
  - Max discount percentage
  - Max campaign budget
  - Approval required above amount
  - Enable/disable cross-sell, upsell, recovery
- **Store Settings**: Store name, URL, contact info
- **API Keys**: Manage API keys for integrations

#### Storefront Demo (`/storefront`)
**Purpose**: Demo storefront for testing AI buyer capabilities

**Features**:
- Product browsing
- Add to cart
- Checkout with Razorpay
- AI recommendations

### Frontend Components

#### AppShell
Main layout wrapper with navigation and header

#### PageHeader
Standard page header with title and description

#### Panel
Content container with title and styled content

#### Stagger
Animated grid layout for cards

#### StatusBadge
Status indicator (positive/warning/negative)

---

## Integration Guide

### For Merchants

#### Step 1: Register
1. Go to `/register`
2. Enter store details (name, email, password)
3. Complete onboarding

#### Step 2: Sync Catalog
1. Navigate to `/integrations`
2. Click "Sync products" on Storefront catalog
3. Choose sync method:
   - **JSON/CSV**: Upload file with product data
   - **Shopify API**: Enter API credentials
   - **WooCommerce**: Enter store URL and API keys
4. Review sync results

#### Step 3: Configure Policies
1. Go to `/settings`
2. Set discount limits
3. Configure approval thresholds
4. Enable/disable features (cross-sell, upsell, recovery)

#### Step 4: Connect Payments
1. In `/integrations`, click "Connect Razorpay"
2. Enter Razorpay key ID and secret
3. Configure webhook URL

#### Step 5: Add Widget to Website
1. In `/integrations`, click "Generate widget"
2. Customize widget appearance (position, colors)
3. Copy embed code
4. Add to website HTML before `</body>` tag

#### Step 6: Monitor Performance
1. Check `/dashboard` for overview
2. Review `/opportunities` for AI suggestions
3. Analyze `/analytics` for detailed insights

### For AI Buyers

#### Using the AI Buyer API

**Authentication**: Use merchant API key as query parameter

**Search Products**:
```bash
POST /api/v1/ai-buyer/search?api_key=YOUR_KEY
{
  "query": "running shoes",
  "category": "Footwear",
  "min_price": 1000,
  "max_price": 5000,
  "limit": 10
}
```

**Get Full Catalog**:
```bash
GET /api/v1/ai-buyer/catalog?api_key=YOUR_KEY
```

**Create Cart**:
```bash
POST /api/v1/ai-buyer/cart/create?api_key=YOUR_KEY
```

**Add to Cart**:
```bash
POST /api/v1/ai-buyer/cart/{cart_id}/add?api_key=YOUR_KEY
{
  "product_id": "uuid",
  "quantity": 2
}
```

**Checkout**:
```bash
POST /api/v1/ai-buyer/checkout?api_key=YOUR_KEY
{
  "items": [
    {"product_id": "uuid", "quantity": 1}
  ],
  "customer_email": "customer@example.com"
}
```

---

## API Reference

### Authentication
All protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

### Response Format
Success responses:
```json
{
  "data": { ... },
  "message": "Success"
}
```

Error responses:
```json
{
  "detail": "Error message"
}
```

### Rate Limiting
- Authenticated requests: 1000/hour
- AI Buyer API: 500/hour per merchant

### Webhooks
**Razorpay Webhook**: `/api/v1/payments/webhook`
- Handles payment events
- Updates order status
- Records payment attempts

---

## Deployment

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- Redis 6+

### Backend Setup

```bash
cd Backend
pip install -r requirements.txt
cp .env.example .env
# Configure .env with database URLs, API keys
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd Frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:8080`

### Environment Variables

**Backend (.env)**:
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/sarthi
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
SECRET_KEY=your-secret-key
```

**Frontend**:
```
VITE_API_URL=http://localhost:8000
```

### Production Deployment

**Backend**:
- Use Gunicorn with Uvicorn workers
- Configure PostgreSQL connection pooling
- Enable Redis for caching
- Set up SSL/TLS

**Frontend**:
- Build with `npm run build`
- Serve with Nginx or similar
- Configure API proxy

---

## Key Features Explained

### 1. AI Revenue Discovery
Sarthi analyzes your catalog, orders, and customer behavior to find revenue opportunities:
- **Abandoned Cart Recovery**: Identify carts not converted and send recovery campaigns
- **Cross-Sell Opportunities**: Find products frequently bought together
- **Pricing Optimization**: Suggest price adjustments based on demand
- **Low Stock Alerts**: Warn about products running low

### 2. Policy Engine
Merchants control AI actions through policies:
- **Discount Limits**: AI cannot offer discounts above X%
- **Budget Caps**: Campaign spending limited to Y per day
- **Approval Workflow**: Actions above Z amount require approval
- **Feature Toggles**: Enable/disable cross-sell, upsell, recovery

### 3. Attribution Tracking
Measure AI impact:
- **Revenue Attribution**: Track revenue influenced by AI suggestions
- **Conversion Tracking**: Monitor conversion rates with/without AI
- **Funnel Analysis**: Understand where AI helps most

### 4. AI Buyer API
Enable external AI agents to transact:
- **Catalog Access**: AI can search and browse products
- **Cart Management**: AI can create and manage carts
- **Checkout**: AI can initiate checkout via Razorpay
- **Policy Compliance**: All actions governed by merchant policies

### 5. Widget Integration
Add AI chat to merchant website:
- **Embed Code**: Simple HTML snippet
- **Customizable**: Position, colors, welcome message
- **Context-Aware**: Knows merchant catalog and inventory
- **Recommendations**: Suggests products based on conversation

---

## Security

### Data Protection
- Customer identifiers pseudonymised before reaching LLMs
- Raw card data never stored
- All write actions logged in audit trail
- Multi-tenant data isolation

### API Security
- JWT authentication for merchant APIs
- API key authentication for AI Buyer API
- Rate limiting per merchant
- CORS configuration

### Payment Security
- Razorpay handles all card data
- Sarthi never sees raw card numbers
- Webhook signatures verified
- Test mode for development

---

## Troubleshooting

### Backend Issues
**Problem**: Backend not starting
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Check pgvector extension is installed

**Problem**: AI responses failing
- Verify OPENAI_API_KEY or ANTHROPIC_API_KEY
- Check API quota limits
- Review logs for specific errors

### Frontend Issues
**Problem**: Frontend not loading
- Check backend is running on port 8000
- Verify VITE_API_URL
- Check browser console for errors

**Problem**: Integrations not working
- Verify backend is running
- Check API credentials
- Review network tab for failed requests

### Widget Issues
**Problem**: Widget not appearing
- Check embed code is correctly placed
- Verify script URL is accessible
- Check browser console for errors

---

## Support

For issues or questions:
- Check API docs at `http://localhost:8000/docs`
- Review logs in backend terminal
- Check browser console for frontend errors
- Verify database connection and data

---

## Glossary

- **Merchant**: Business using Sarthi to optimize revenue
- **Catalog**: Product inventory managed by merchant
- **Opportunity**: AI-suggested action to increase revenue
- **Recommendation**: Product suggestion for customers
- **Attribution**: Revenue influenced by AI actions
- **Policy**: Rules governing AI behavior
- **AI Buyer**: External AI agent transacting with store
- **Widget**: Chat widget embedded on merchant website
- **Cross-Sell**: Suggesting complementary products
- **Upsell**: Suggesting higher-value alternatives
- **Recovery**: Re-engaging lost customers (abandoned carts)

---

## Version History

- **v1.0**: Initial release with core features
  - Catalog sync
  - AI chat
  - Recommendations
  - Policy engine
  - Razorpay integration
  - AI Buyer API
  - Widget generation

---

## License

Proprietary - All rights reserved
