/**
 * Sarthi domain contracts.
 * These interfaces are the contract between the UI and the API layer.
 * The mock service layer in `src/services` implements them today; a real
 * backend can replace each service function without touching components.
 */

export type ID = string;
export type ISODate = string;

export interface Merchant {
  id: ID;
  name: string;
  storeUrl: string;
  currency: "INR";
  plan: "growth" | "scale" | "enterprise";
  razorpayConnected: boolean;
  testMode: boolean;
  createdAt: ISODate;
}

export interface Product {
  id: ID;
  sku: string;
  name: string;
  category: string;
  price: number;
  compareAtPrice?: number;
  inventory: number;
  unitsSold30d: number;
  conversionRate: number;
  aovContribution: number;
  crossSellOpportunities: number;
  aiScore: number; // 0-100
  rating: number;
  imageHue: number; // deterministic art-direction seed
  status: "active" | "low_stock" | "out_of_stock";
}

export interface Customer {
  id: ID;
  name: string;
  email: string;
  segment: "new" | "returning" | "vip" | "at_risk";
  orders: number;
  lifetimeValue: number;
  lastOrderAt: ISODate;
  aiInfluencedRevenue: number;
}

export type OrderStatus = "paid" | "pending" | "failed" | "refunded" | "fulfilled";

export interface Order {
  id: ID;
  customerName: string;
  items: number;
  amount: number;
  status: OrderStatus;
  aiAttributed: boolean;
  attributionSource?: RevenueAttribution["source"];
  placedAt: ISODate;
}

export interface Cart {
  id: ID;
  customerName: string;
  items: number;
  value: number;
  state: "active" | "abandoned" | "recovered" | "checkout_started";
  lastActivityAt: ISODate;
  recoveryAttempts: number;
}

export interface Payment {
  id: ID;
  orderId: ID;
  amount: number;
  method: "upi" | "card" | "netbanking" | "wallet";
  status: "created" | "authorized" | "captured" | "failed" | "refunded";
  failureReason?: string;
  createdAt: ISODate;
}

export type OpportunityType =
  | "cross_sell"
  | "bundle"
  | "upsell"
  | "cart_recovery"
  | "payment_recovery"
  | "inventory_promo"
  | "campaign"
  | "ranking";

export type OpportunityStatus =
  "new" | "under_review" | "approved" | "rejected" | "executing" | "executed" | "blocked";

export interface EvidencePoint {
  kind: "observed" | "recommendation";
  statement: string;
  metric?: string;
  source: string;
}

export interface Opportunity {
  id: ID;
  title: string;
  type: OpportunityType;
  status: OpportunityStatus;
  expectedRevenue: number;
  expectedOrders: number;
  confidence: number; // 0-1
  confidenceIntervalLow: number;
  confidenceIntervalHigh: number;
  summary: string;
  rationale: string;
  evidence: EvidencePoint[];
  affectedProductIds: ID[];
  segment: string;
  segmentSize: number;
  risk: "low" | "medium" | "high";
  riskNotes: string;
  policyChecks: PolicyCheck[];
  recommendedAction: string;
  simulation: { scenario: string; orders: number; revenue: number }[];
  discoveredAt: ISODate;
  executionHistory: AgentAction[];
  outcome?: { revenue: number; orders: number; incremental: number; note: string };
}

export interface PolicyCheck {
  policy: string;
  result: "pass" | "block" | "requires_approval";
  detail: string;
}

export interface Recommendation {
  id: ID;
  surface: "storefront" | "cart" | "email" | "checkout";
  type: OpportunityType;
  productName: string;
  category: string;
  segment: string;
  impressions: number;
  clicks: number;
  addToCart: number;
  purchases: number;
  attachRate: number;
  revenue: number;
}

export interface Campaign {
  id: ID;
  name: string;
  channel: "email" | "whatsapp" | "onsite" | "sms";
  objective: string;
  status:
    | "draft"
    | "awaiting_approval"
    | "approved"
    | "rejected"
    | "live"
    | "paused"
    | "completed"
    | "cancelled";
  budget: number;
  spend: number;
  revenue: number;
  audience: number;
  startedAt: ISODate;
}

export interface Experiment {
  id: ID;
  name: string;
  hypothesis: string;
  status: "running" | "concluded" | "paused";
  control: ExperimentArm;
  variant: ExperimentArm;
  lift: number;
  confidence: number;
  incrementalRevenue: number;
}

export interface ExperimentArm {
  label: string;
  sessions: number;
  conversion: number;
  aov: number;
  attachRate: number;
  revenuePerSession: number;
}

export type AgentName =
  | "Growth Analyst"
  | "Conversation Agent"
  | "Recommendation Engine"
  | "Policy Engine"
  | "Merchant Approval"
  | "Campaign Executor"
  | "Recovery Agent"
  | "Attribution Engine";

export interface AgentAction {
  id: ID;
  agent: AgentName;
  action: string;
  detail: string;
  status: "completed" | "running" | "blocked" | "awaiting_approval";
  at: ISODate;
  correlationId: string;
}

export interface AgentRun {
  id: ID;
  trigger: string;
  startedAt: ISODate;
  actions: AgentAction[];
}

export interface Policy {
  id: ID;
  key: string;
  label: string;
  description: string;
  kind: "toggle" | "slider" | "number";
  value: number | boolean;
  min?: number;
  max?: number;
  step?: number;
  unit?: string;
  group: "spend" | "approvals" | "communication" | "payments" | "catalog";
}

export interface AuditEvent {
  id: ID;
  at: ISODate;
  agent: AgentName;
  action: string;
  input: string;
  decision: string;
  policyResult: "pass" | "block" | "requires_approval";
  approval: "auto" | "merchant_approved" | "merchant_rejected" | "pending" | "n/a";
  execution: "executed" | "not_executed" | "partial";
  result: string;
  correlationId: string;
}

export interface RevenueAttribution {
  source: "cross_sell" | "recovery" | "upsell" | "campaign";
  label: string;
  revenue: number;
  deltaPct: number;
}

export interface RecoveryCase {
  id: ID;
  kind: "payment_failure" | "abandoned_cart" | "incomplete_checkout";
  customerName: string;
  atRisk: number;
  recoverable: number;
  attempts: number;
  recovered: number;
  status: "open" | "recovered" | "lost" | "in_progress";
  reason: string;
  at: ISODate;
}

export interface MetricPoint {
  date: string;
  revenue: number;
  aiRevenue: number;
  orders: number;
  aov: number;
  conversion: number;
}

export interface DashboardSummary {
  totalRevenue: number;
  aiAttributedRevenue: number;
  recoveredRevenue: number;
  incrementalRevenue: number;
  aov: number;
  conversionRate: number;
  acceptanceRate: number;
  deltas: Record<string, number>;
  trend: MetricPoint[];
  attribution: RevenueAttribution[];
}

/**
 * Mirrors the real backend ChatResponse from POST /ai/chat: { message, data, actions,
 * correlation_id }. This is the real LLM-backed agent response — no canned/keyword-matched
 * fields (headline/finding/numbers/intervention) are fabricated on top of it.
 */
export interface CopilotAnswer {
  id: ID;
  message: string;
  data?: Record<string, unknown> | null;
  actions: { type?: string; label?: string; [key: string]: unknown }[];
  correlationId: string;
}

export interface ShopProduct extends Product {
  whyRecommended: string;
  availability: "in_stock" | "low_stock" | "out_of_stock";
}

export interface CartLine {
  productId: ID;
  name: string;
  price: number;
  qty: number;
  viaSarthi: boolean;
}
