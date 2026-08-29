# Sarthi Frontend - AI Revenue Agent Dashboard

Production-grade React frontend for Sarthi, an AI-powered revenue optimization platform for ecommerce merchants.

## 🎯 Overview

Sarthi is an autonomous revenue optimization layer that continuously analyzes catalog, inventory, customer and payment signals to discover revenue opportunities, proposes explainable actions, and executes only within merchant-defined policies.

This frontend provides:

- **Merchant Dashboard** - Revenue metrics, AI insights, opportunity management
- **AI Copilot** - Conversational interface for querying business intelligence
- **Product Management** - Catalog browsing with AI recommendations
- **Order & Customer Management** - Complete commerce operations
- **Policy Center** - Configure AI agent boundaries and approval workflows
- **Audit Trail** - Transparent record of all AI decisions and actions
- **Shopper Storefront** - Customer-facing conversational shopping experience

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- (Optional) Backend server with PostgreSQL and Redis for full functionality

### Installation

```bash
cd Frontend
npm install
```

### Development Mode (Mock Data)

The frontend runs with realistic mock data by default, perfect for development and demos:

```bash
npm run dev
```

Open [http://localhost:8080](http://localhost:8080)

**Demo Credentials:**

- Email: `demo@strideathletics.com`
- Password: `demo123456`

### Production Mode (Real Backend)

To connect to the real backend:

1. **Start the backend** (requires Docker for PostgreSQL/Redis):

```bash
cd Backend
source .venv/bin/activate
# Start database
docker compose up -d db redis
# Seed demo data
python -m app.demo.seed
# Start API server
uvicorn app.main:app --reload --port 8000
```

2. **Update frontend configuration**:

```bash
# Edit .env file
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

3. **Restart frontend**:

```bash
npm run dev
```

## 📁 Project Structure

```
Frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── app-shell.tsx   # Main layout with navigation
│   │   ├── charts.tsx      # Data visualization components
│   │   ├── metrics.tsx     # Metric cards and displays
│   │   ├── opportunity.tsx # Opportunity cards
│   │   └── shop-shell.tsx  # Storefront layout
│   ├── routes/             # File-based routing (TanStack Router)
│   │   ├── __root.tsx      # Root layout
│   │   ├── index.tsx       # Landing page
│   │   ├── login.tsx       # Authentication
│   │   ├── dashboard.tsx   # Main dashboard
│   │   ├── opportunities/  # Opportunity management
│   │   ├── products/       # Product catalog
│   │   ├── orders.tsx      # Order management
│   │   ├── customers.tsx   # Customer management
│   │   ├── ai-copilot.tsx  # AI chat interface
│   │   ├── policies.tsx    # Policy configuration
│   │   ├── audit.tsx       # Audit trail
│   │   ├── shop/           # Shopper storefront
│   │   └── ...
│   ├── services/           # API service layer
│   │   ├── client.ts       # HTTP client with auth
│   │   ├── sarthi.ts       # API service functions
│   │   └── fixtures.ts     # Mock data
│   ├── lib/                # Utilities and types
│   │   ├── types.ts        # TypeScript type definitions
│   │   ├── utils.ts        # Helper functions
│   │   └── shop-cart.ts    # Shopping cart state
│   └── hooks/              # Custom React hooks
├── .env                    # Environment configuration
├── package.json
└── vite.config.ts
```

## 🎨 Key Features

### 1. Dashboard

- Real-time revenue metrics with AI attribution
- Opportunity pipeline visualization
- Agent activity timeline
- Revenue trend charts

### 2. AI Opportunities

- Discover → Explain → Propose → Govern → Approve → Execute flow
- Evidence-based recommendations
- Confidence intervals and risk assessment
- One-click approval/rejection

### 3. AI Copilot

- Natural language queries about business metrics
- Structured responses with data visualizations
- Contextual recommendations
- Conversation history

### 4. Product Management

- Catalog browsing with search and filters
- AI recommendation scores
- Inventory status tracking
- Cross-sell opportunity indicators

### 5. Policy Center

- Configure discount limits
- Set campaign budgets
- Define approval thresholds
- Toggle AI capabilities

### 6. Audit Trail

- Complete transparency of AI decisions
- Correlation IDs for tracking
- Policy evaluation results
- Execution history

### 7. Shopper Storefront

- Conversational product search
- AI-powered recommendations
- Shopping cart with attribution tracking
- Checkout flow

## 🔌 API Integration

The frontend uses a service layer (`src/services/sarthi.ts`) that abstracts all API calls.

### Switching Between Mock and Real API

**Mock Mode** (default):

```env
VITE_USE_MOCK=true
```

- Uses realistic fixture data
- Simulates API latency (260ms)
- Perfect for development and demos

**Real Mode**:

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

- Connects to actual backend
- Requires authentication
- Full CRUD operations

### Authentication Flow

1. User submits credentials on `/login`
2. Frontend calls `/api/v1/auth/login`
3. Backend returns JWT token
4. Token stored in localStorage
5. All subsequent requests include `Authorization: Bearer <token>`

## 🧪 Testing

### Automated Route Tests

```bash
./test-all-flows.sh
```

Tests all 15+ routes to ensure they load correctly.

### Manual Testing Checklist

- [ ] Landing page loads with hero section
- [ ] Login with demo credentials
- [ ] Dashboard shows revenue metrics
- [ ] Opportunities page displays AI findings
- [ ] Approve/reject an opportunity
- [ ] AI Copilot responds to queries
- [ ] Products page shows catalog
- [ ] Shop storefront allows searching
- [ ] Add items to cart
- [ ] Policies page allows configuration
- [ ] Audit trail shows activity

## 🎯 Backend Endpoints

The frontend expects these backend endpoints (when `VITE_USE_MOCK=false`):

### Authentication

- `POST /api/v1/auth/register` - Register new merchant
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Merchant

- `GET /api/v1/merchant` - Get merchant details
- `GET /api/v1/merchant/settings` - Get settings
- `PUT /api/v1/merchant/settings` - Update settings

### Dashboard

- `GET /api/v1/analytics/dashboard` - Get dashboard data

### Opportunities

- `GET /api/v1/opportunities` - List opportunities
- `GET /api/v1/opportunities/:id` - Get opportunity
- `POST /api/v1/opportunities/analyze` - Run analysis
- `POST /api/v1/opportunities/:id/decision` - Approve/reject

### Products

- `GET /api/v1/products` - List products
- `GET /api/v1/products/:id` - Get product
- `POST /api/v1/products` - Create product
- `PUT /api/v1/products/:id` - Update product

### Orders

- `GET /api/v1/orders` - List orders
- `GET /api/v1/orders/:id` - Get order
- `POST /api/v1/orders` - Create order

### Customers

- `GET /api/v1/customers` - List customers
- `GET /api/v1/customers/:id` - Get customer

### Policies

- `GET /api/v1/policies` - List policies
- `POST /api/v1/policies/evaluate` - Evaluate policy

### AI

- `POST /api/v1/ai/chat` - Chat with AI copilot

### Storefront

- `GET /api/v1/storefront/products` - List shop products
- `POST /api/v1/storefront/search` - Search products
- `POST /api/v1/storefront/cart/:sessionId/add` - Add to cart
- `POST /api/v1/storefront/checkout` - Checkout

## 🛠️ Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run format       # Format code with Prettier
```

### Tech Stack

- **React 19** - UI framework
- **TanStack Router** - File-based routing
- **TanStack Query** - Server state management
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Component library
- **TypeScript** - Type safety
- **Recharts** - Data visualization
- **Framer Motion** - Animations

## 📝 Environment Variables

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCK=true

# Optional: Analytics
VITE_ANALYTICS_ID=

# Optional: Feature flags
VITE_ENABLE_EXPERIMENTS=true
```

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

Output will be in `.output/` directory.

### Deploy to Vercel/Netlify

The build output is compatible with serverless platforms:

```bash
npm run build
# Deploy .output/public directory
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 🔒 Security

- JWT tokens stored in localStorage (consider httpOnly cookies for production)
- All API calls include authentication headers
- CORS configured on backend
- No sensitive data in frontend code
- Input validation on all forms

## 📚 Documentation

- [Backend API Documentation](../Backend/README.md)
- [Architecture Guide](../Backend/guide.md)
- [Type Definitions](./src/lib/types.ts)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `./test-all-flows.sh`
4. Submit a pull request

## 📄 License

Proprietary - Razorpay AI Buildathon 2026

## 🆘 Support

For issues or questions:

- Check the backend is running
- Verify `.env` configuration
- Check browser console for errors
- Review network tab for API calls

---

**Built with ❤️ for the Razorpay AI Buildathon**
