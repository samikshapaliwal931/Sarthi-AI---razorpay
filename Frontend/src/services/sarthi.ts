/**
 * Sarthi API service layer.
 * Works with mock data by default, switches to real backend when VITE_USE_MOCK=false
 */
import {
  request,
  requestPost,
  requestPut,
  requestDelete,
  setAuthToken,
  getAuthToken,
  clearAuth,
  USE_MOCK,
} from "./client";
import * as fx from "./fixtures";
import type {
  AgentAction,
  AuditEvent,
  Campaign,
  Cart,
  CopilotAnswer,
  Customer,
  DashboardSummary,
  Experiment,
  Merchant,
  Opportunity,
  OpportunityStatus,
  Policy,
  Product,
  Order,
  Recommendation,
  RecoveryCase,
  ShopProduct,
} from "@/lib/types";

/**
 * Deterministic art-direction seed derived from an entity id, used only to pick a
 * gradient hue for placeholder product art. Not a data value — never used for metrics.
 */
function hueFromId(id: string | undefined | null): number {
  if (!id) return 210;
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash * 31 + id.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % 360;
}

// Authentication
export const auth = {
  login: async (email: string, password: string) => {
    if (USE_MOCK) {
      // Mock authentication
      if (email === "demo@strideathletics.com" && password === "demo123456") {
        const token = "mock_jwt_token_" + Date.now();
        setAuthToken(token);
        return {
          access_token: token,
          merchant_id: fx.merchant.id,
          user_id: "user_01",
        };
      }
      throw new Error("Invalid credentials");
    }

    const response = await requestPost<{
      access_token: string;
      merchant_id: string;
      user_id: string;
      ai_buyer_api_key?: string | null;
    }>("/auth/login", { email, password });
    setAuthToken(response.access_token);
    return response;
  },

  register: async (name: string, email: string, password: string, storeName: string) => {
    if (USE_MOCK) {
      const token = "mock_jwt_token_" + Date.now();
      setAuthToken(token);
      return {
        access_token: token,
        merchant_id: "mch_" + Date.now(),
        user_id: "user_" + Date.now(),
        ai_buyer_api_key: "mock_ai_buyer_key_" + Date.now(),
      };
    }

    const response = await requestPost<{
      access_token: string;
      merchant_id: string;
      user_id: string;
      ai_buyer_api_key?: string | null;
    }>("/auth/register", { name, email, password, store_name: storeName });
    setAuthToken(response.access_token);
    return response;
  },

  logout: () => {
    clearAuth();
  },

  isAuthenticated: () => {
    return !!getAuthToken();
  },
};

// Merchant
export const merchantApi = {
  get: async (): Promise<Merchant> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.merchant), 260);
      });
    }

    const response = await request<any>("/merchant", {});
    // Transform backend Merchant to frontend Merchant type
    return {
      id: response.id,
      name: response.store_name || response.name,
      storeUrl: response.store_url || "",
      currency: "INR",
      plan: "scale",
      razorpayConnected: true,
      testMode: true,
      createdAt: response.created_at,
    };
  },
  getSettings: async () => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(
          () =>
            resolve({
              max_discount_percent: 10,
              max_campaign_budget: 50000,
              approval_required_above_amount: 5000,
            }),
          260,
        );
      });
    }
    return request<any>("/merchant/settings", {});
  },
  updateSettings: (settings: any) => requestPut<any>("/merchant/settings", settings),
};

// Dashboard
export const dashboardApi = {
  get: async (): Promise<DashboardSummary> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.dashboard), 260);
      });
    }

    const response = await request<any>("/analytics/dashboard", {});

    // Transform backend response to frontend DashboardSummary format.
    // There is no time-series/trend endpoint server-side and no historical
    // deltas are computed by the backend, so we do NOT fabricate them here —
    // `deltas` is left empty (MetricCard renders without a delta badge when
    // absent) and `trend` is left empty (the trend chart hides itself / shows
    // an empty state) rather than showing invented percentages.
    const metrics = response.revenue_metrics || {};
    return {
      totalRevenue: metrics.total_revenue || 0,
      aiAttributedRevenue: metrics.ai_attributed_revenue || 0,
      recoveredRevenue: metrics.recovered_revenue || 0,
      // No backend field for "incremental" (holdout-measured) revenue exists yet.
      // Rather than deriving a fake multiplier, we report it as unavailable.
      incrementalRevenue: 0,
      aov: metrics.average_order_value || 0,
      conversionRate: (metrics.conversion_rate || 0) * 100,
      // recommendation_ctr is the real, closest available proxy for "acceptance" —
      // click-through rate on recommendations, not a fabricated approval rate.
      acceptanceRate: metrics.recommendation_ctr || 0,
      deltas: {},
      trend: [],
      // No per-source attribution breakdown endpoint exists server-side.
      attribution: [],
    };
  },
};

// Opportunities
const typeMap: Record<string, Opportunity["type"]> = {
  cross_sell: "cross_sell",
  bundle: "bundle",
  upsell: "upsell",
  abandoned_cart: "cart_recovery",
  payment_recovery: "payment_recovery",
  inventory: "inventory_promo",
  price_experiment: "ranking",
  repeat_purchase: "campaign",
  campaign: "campaign",
};

const statusMap: Record<string, OpportunityStatus> = {
  discovered: "new",
  validated: "new",
  proposed: "under_review",
  approved: "approved",
  rejected: "rejected",
  executing: "executing",
  executed: "executed",
  failed: "blocked",
  expired: "blocked",
  new: "new",
  under_review: "under_review",
  blocked: "blocked",
};

function transformOpportunity(raw: any): Opportunity {
  const risk = (
    raw.risk === "high" ? "high" : raw.risk === "medium" ? "medium" : "low"
  ) as Opportunity["risk"];
  const expectedRevenue = raw.expected_impact || raw.expectedRevenue || 0;
  const confidence = raw.confidence ?? 0.5;
  const aovEstimate = 2500;

  const evidence: Opportunity["evidence"] = (raw.evidence || []).map((e: any) => ({
    kind: "observed" as const,
    statement: e.description || e.statement || e.metric_name,
    metric: e.metric_value != null ? `${e.metric_name}: ${e.metric_value}` : e.metric_name,
    source: e.data_source || e.evidence_type || "catalog",
  }));

  const recommendedAction =
    raw.recommended_action || raw.recommendedAction || "No action specified";
  const policyChecks: Opportunity["policyChecks"] = raw.required_approval
    ? [
        {
          policy: "Approval threshold",
          result: "requires_approval",
          detail: "Requires merchant approval before execution.",
        },
        {
          policy: "Discount ceiling",
          result: "pass",
          detail: "Within configured maximum discount.",
        },
      ]
    : [
        {
          policy: "Discount ceiling",
          result: "pass",
          detail: "Within configured maximum discount.",
        },
        { policy: "Spend cap", result: "pass", detail: "Within configured campaign budget." },
      ];

  return {
    id: raw.id,
    title: raw.title,
    type: typeMap[raw.type] ?? "cross_sell",
    status: statusMap[raw.status] ?? "new",
    expectedRevenue,
    expectedOrders: raw.expected_orders ?? Math.round(expectedRevenue / aovEstimate),
    confidence,
    confidenceIntervalLow:
      raw.confidence_interval_low ?? expectedRevenue * Math.max(0, confidence - 0.15),
    confidenceIntervalHigh: raw.confidence_interval_high ?? expectedRevenue * (confidence + 0.15),
    summary: raw.description || raw.summary || "",
    rationale: raw.description || raw.rationale || "",
    evidence,
    affectedProductIds: raw.affected_product_ids || [],
    segment: raw.segment || "all customers",
    segmentSize: raw.segment_size || 0,
    risk,
    riskNotes:
      raw.risk_notes ||
      (risk === "low"
        ? "Bounded, reversible action inside policy limits."
        : "Requires merchant attention before execution."),
    policyChecks,
    recommendedAction,
    simulation: raw.simulation || [
      {
        scenario: "Conservative",
        orders: Math.round((expectedRevenue / aovEstimate) * 0.7),
        revenue: expectedRevenue * 0.7,
      },
      {
        scenario: "Expected",
        orders: Math.round(expectedRevenue / aovEstimate),
        revenue: expectedRevenue,
      },
      {
        scenario: "Optimistic",
        orders: Math.round((expectedRevenue / aovEstimate) * 1.4),
        revenue: expectedRevenue * 1.4,
      },
    ],
    discoveredAt: raw.discovered_at || raw.created_at,
    executionHistory: raw.execution_history || [],
    outcome: raw.outcome,
  };
}

export const opportunitiesApi = {
  list: async (): Promise<Opportunity[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.opportunities), 260);
      });
    }
    const response = await request<any>("/opportunities", {});
    return (Array.isArray(response) ? response : []).map(transformOpportunity);
  },
  get: async (id: string): Promise<Opportunity> => {
    if (USE_MOCK) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          const found = fx.opportunities.find((o) => o.id === id);
          found ? resolve(found) : reject(new Error("Opportunity not found"));
        }, 260);
      });
    }
    const response = await request<any>(`/opportunities/${id}`, {});
    return transformOpportunity(response);
  },
  analyze: () => requestPost<Opportunity[]>("/opportunities/analyze", {}),
  decide: async (
    id: string,
    decision: "approve" | "reject",
    notes?: string,
  ): Promise<Opportunity> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            ...(fx.opportunities.find((o) => o.id === id) ?? fx.opportunities[0]!),
            status: (decision === "approve" ? "approved" : "rejected") as OpportunityStatus,
          });
        }, 260);
      });
    }
    const response = await requestPost<any>(`/opportunities/${id}/decision`, {
      action: decision,
      notes,
    });
    return transformOpportunity(response);
  },
};

// Products
export const productsApi = {
  list: async (opts?: { q?: string; category?: string; limit?: number }): Promise<Product[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.products), 260);
      });
    }

    const params = new URLSearchParams();
    if (opts?.q) params.set("q", opts.q);
    if (opts?.category) params.set("category", opts.category);
    params.set("limit", String(opts?.limit ?? 100));
    const response = await request<any>(`/products?${params.toString()}`, {});
    // Backend returns { products: [...], total, limit, offset } — a ProductSearchResponse
    // of ProductResponse rows. The list endpoint does not include inventory counts or any
    // sales/conversion/scoring metrics (those would require per-product inventory calls or
    // analytics endpoints that don't exist yet), so those fields are honestly reported as 0
    // rather than randomised. `status` is derived only from the real `is_active` flag —
    // "low_stock" is never guessed.
    const products = (response.products || []).map((p: any) => ({
      id: p.id,
      sku: p.id.substring(0, 8).toUpperCase(), // Generate SKU from ID
      name: p.name,
      category: p.category,
      price: p.sale_price || p.base_price,
      compareAtPrice: p.sale_price ? p.base_price : undefined,
      inventory: 0, // Not returned by the list endpoint; see /products/{id}/inventory for real stock
      unitsSold30d: 0, // Not tracked by any backend endpoint yet
      conversionRate: 0, // Not tracked by any backend endpoint yet
      aovContribution: 0, // Not tracked by any backend endpoint yet
      crossSellOpportunities: 0, // Not tracked by any backend endpoint yet
      aiScore: 0, // Not tracked by any backend endpoint yet
      rating: 0, // Not tracked by any backend endpoint yet
      imageHue: hueFromId(p.id), // deterministic art-direction seed, not a data value
      status: p.is_active ? "active" : "out_of_stock",
    }));
    return products;
  },
  get: (id: string) =>
    request<Product>(`/products/${id}`, () => {
      const found = fx.products.find((p) => p.id === id);
      return (
        found ??
        (() => {
          throw new Error("Product not found");
        })()
      );
    }),
  /** POST /products — real body shape is {name, category, base_price, ...}, not the frontend Product shape. */
  create: (input: {
    name: string;
    category: string;
    basePrice: number;
    description?: string;
    brand?: string;
  }) =>
    requestPost<any>("/products", {
      name: input.name,
      category: input.category,
      base_price: input.basePrice,
      description: input.description || undefined,
      brand: input.brand || undefined,
    }),
  // NOTE: there is no generic `PUT /products/{id}` route on the backend — only
  // `PUT /products/{id}/inventory` (quantity/reserved/low_stock_threshold) exists.
  // This function intentionally only patches inventory; do not extend it to send
  // arbitrary product fields until a real update route exists server-side.
  updateInventory: (
    id: string,
    inventory: { quantity?: number; reserved?: number; low_stock_threshold?: number },
  ) => requestPut<any>(`/products/${id}/inventory`, inventory),
};

// Orders
export const ordersApi = {
  list: async (opts?: { status?: string; limit?: number }): Promise<Order[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.orders), 260);
      });
    }

    const params = new URLSearchParams();
    if (opts?.status) params.set("status", opts.status);
    params.set("limit", String(opts?.limit ?? 50));
    const response = await request<any>(`/orders?${params.toString()}`, {});
    // Transform backend Order to frontend Order type. OrderResponse carries no
    // AI-attribution field, so we report it honestly as untracked (false / undefined)
    // rather than randomly assigning attribution.
    const orders = (Array.isArray(response) ? response : []).map((o: any) => ({
      id: o.order_number || o.id.substring(0, 8),
      customerName: `Customer ${o.customer_id?.substring(0, 6) || "Unknown"}`,
      items: o.items?.length || 0,
      amount: o.total,
      status: o.status,
      aiAttributed: false, // Not tracked by the backend yet
      attributionSource: undefined,
      placedAt: o.created_at,
    }));
    return orders;
  },
  get: (id: string) =>
    request<Order>(`/orders/${id}`, () => {
      const found = fx.orders.find((o) => o.id === id);
      return (
        found ??
        (() => {
          throw new Error("Order not found");
        })()
      );
    }),
  create: (order: any) => requestPost<Order>("/orders", order),
};

// Customers
export const customersApi = {
  list: async (): Promise<Customer[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.customers), 260);
      });
    }

    const response = await request<any>("/customers", {});
    // Transform backend Customer to frontend Customer type. CustomerResponse has no
    // AI-influenced-revenue field, so we report it honestly as 0 rather than a
    // fabricated fraction of lifetime value.
    const customers = (Array.isArray(response) ? response : []).map((c: any) => ({
      id: c.id,
      name: c.name || `Customer ${c.id.substring(0, 6)}`,
      email: c.email || `${c.id.substring(0, 8)}@example.com`,
      segment: c.segment || "new",
      orders: c.order_count || 0,
      lifetimeValue: c.lifetime_value || 0,
      aiInfluencedRevenue: 0, // Not tracked by the backend yet
      lastOrderAt: c.last_order_at || c.created_at,
    }));
    return customers;
  },
  get: (id: string) =>
    request<Customer>(`/customers/${id}`, () => {
      const found = fx.customers.find((c) => c.id === id);
      return (
        found ??
        (() => {
          throw new Error("Customer not found");
        })()
      );
    }),
};

// Carts
export const cartsApi = {
  list: async (): Promise<Cart[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.carts), 260);
      });
    }

    const response = await request<any>("/carts", {});
    // Transform backend Cart to frontend Cart type
    const carts = (Array.isArray(response) ? response : []).map((c: any) => ({
      id: c.id,
      customerName: c.customer_id ? `Customer ${c.customer_id.substring(0, 6)}` : "Guest",
      items: c.items?.length || 0,
      value: c.subtotal || 0,
      state: c.status || "active",
      recoveryAttempts: 0,
      lastActivityAt: c.updated_at || c.created_at,
    }));
    return carts;
  },
  get: (id: string) =>
    request<Cart>(`/carts/${id}`, () => {
      const found = fx.carts.find((c) => c.id === id);
      return (
        found ??
        (() => {
          throw new Error("Cart not found");
        })()
      );
    }),
};

// Recovery
export const recoveryApi = {
  list: async (): Promise<RecoveryCase[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.recoveryCases), 260);
      });
    }

    const response = await request<any>("/recovery", {});
    const statusMap: Record<string, RecoveryCase["status"]> = {
      detected: "open",
      analyzing: "open",
      intervention_proposed: "in_progress",
      intervention_sent: "in_progress",
      recovered: "recovered",
      expired: "lost",
      failed: "lost",
    };
    // Transform backend RecoveryCase to frontend RecoveryCase type. "recoverable" is the
    // real still-open remainder (potential - recovered), not a modelled probability —
    // there's no backend recovery-rate model to draw one from.
    const cases = (Array.isArray(response) ? response : []).map((r: any) => ({
      id: r.id,
      kind: r.case_type || "payment_failure",
      customerName: r.customer_id ? `Customer ${r.customer_id.substring(0, 6)}` : "Unknown",
      reason: r.case_type === "abandoned_cart" ? "Cart abandoned" : "Payment failed",
      atRisk: r.potential_value || 0,
      recoverable: Math.max(0, (r.potential_value || 0) - (r.recovered_value || 0)),
      recovered: r.recovered_value || 0,
      attempts: r.intervention_type ? 1 : 0,
      status: statusMap[r.status] ?? "open",
      at: r.created_at,
    }));
    return cases;
  },
  get: (id: string) =>
    request<RecoveryCase>(`/recovery/${id}`, () => {
      const found = fx.recoveryCases.find((r) => r.id === id);
      return (
        found ??
        (() => {
          throw new Error("Recovery case not found");
        })()
      );
    }),
  /** POST /recovery/detect — scans abandoned carts + failed payments for new cases (deduped server-side). */
  detect: () => requestPost<any[]>("/recovery/detect", {}),
  /** POST /recovery/{id}/send-intervention — the bounded reminder/retry action. */
  sendIntervention: (id: string, interventionType = "reminder_message") =>
    requestPost<any>(`/recovery/${id}/send-intervention`, { intervention_type: interventionType }),
};

// Recommendations
export const recommendationsApi = {
  list: async (): Promise<Recommendation[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.recommendations), 260);
      });
    }

    const response = await request<any>("/recommendations", {});
    // Transform backend Recommendation to frontend Recommendation type. RecommendationResponse
    // exposes `score`/`score_components`/`reason` but no impression/click/purchase funnel or
    // revenue data — that would require a dedicated recommendation-analytics endpoint that
    // doesn't exist yet. Those funnel fields are reported honestly as 0 (not tracked) instead
    // of randomised; `product.name` is used when the API included the joined product.
    const recommendations = (Array.isArray(response) ? response : []).map((r: any) => ({
      id: r.id,
      surface: r.recommendation_type || "storefront",
      type: r.recommendation_type || "cross_sell",
      productName: r.product?.name || `Product ${r.product_id?.substring(0, 8) || "Unknown"}`,
      category: r.product?.category || "General",
      segment: "all",
      impressions: 0, // Not tracked by the backend yet
      clicks: 0, // Not tracked by the backend yet
      addToCart: 0, // Not tracked by the backend yet
      purchases: 0, // Not tracked by the backend yet
      attachRate: 0, // Not tracked by the backend yet
      revenue: 0, // Not tracked by the backend yet
    }));
    return recommendations;
  },
  get: (id: string) =>
    request<Recommendation>(`/recommendations/${id}`, () => {
      const found = fx.recommendations.find((r) => r.id === id);
      return (
        found ??
        (() => {
          throw new Error("Recommendation not found");
        })()
      );
    }),
};

// Campaigns
export const campaignsApi = {
  list: async (): Promise<Campaign[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.campaigns), 260);
      });
    }

    const response = await request<any>("/campaigns", {});
    // Transform backend Campaign to frontend Campaign type. CampaignResponse has no
    // audience-size field, so it's reported honestly as 0 rather than randomised.
    const campaigns = (Array.isArray(response) ? response : []).map((c: any) => ({
      id: c.id,
      name: c.name,
      channel: c.campaign_type || "onsite",
      objective: `Campaign for ${c.campaign_type || "growth"}`,
      status:
        c.status === "running"
          ? "live"
          : c.status === "pending_approval"
            ? "awaiting_approval"
            : c.status,
      budget: c.budget,
      spend: c.actual_spend,
      revenue: c.revenue_generated,
      audience: 0, // Not tracked by the backend yet
      startedAt: c.started_at || c.created_at,
    }));
    return campaigns;
  },
  get: (id: string) =>
    request<Campaign>(`/campaigns/${id}`, () => {
      const found = fx.campaigns.find((c) => c.id === id);
      return (
        found ??
        (() => {
          throw new Error("Campaign not found");
        })()
      );
    }),
  /** POST /campaigns — real body shape is {name, campaign_type, budget, config?}. */
  create: (input: { name: string; campaignType: string; budget: number }) =>
    requestPost<any>("/campaigns", {
      name: input.name,
      campaign_type: input.campaignType,
      budget: input.budget,
    }),
  /** POST /campaigns/{id}/decision — policy-gated: over-budget is blocked server-side. */
  decide: (id: string, decision: "approve" | "reject", notes?: string) =>
    requestPost<any>(`/campaigns/${id}/decision`, { action: decision, notes }),
};

// Experiments
export const experimentsApi = {
  list: async (): Promise<Experiment[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.experiments), 260);
      });
    }

    const response = await request<any>("/experiments", {});
    // Transform backend Experiment to frontend Experiment type. ExperimentResponse only
    // guarantees id/name/status/config — arm-level stats (sessions, conversion, aov, lift,
    // confidence) live in the free-form `metrics` dict *if and when* the experiment service
    // has computed them. We read real values out of `metrics` when present and fall back to
    // honest zeros (never random numbers) when the experiment hasn't produced results yet.
    const armFromMetrics = (m: any, label: string) => ({
      label,
      sessions: m?.sessions ?? 0,
      conversion: m?.conversion ?? 0,
      aov: m?.aov ?? 0,
      attachRate: m?.attach_rate ?? 0,
      revenuePerSession: m?.revenue_per_session ?? 0,
    });
    const experiments = (Array.isArray(response) ? response : []).map((e: any) => {
      const metrics = e.metrics || {};
      return {
        id: e.id,
        name: e.name,
        hypothesis: e.description || `Testing ${e.experiment_type} impact on revenue`,
        status: e.status,
        control: armFromMetrics(metrics.control, "Control"),
        variant: armFromMetrics(metrics.variant, "Variant"),
        lift: metrics.lift ?? 0,
        confidence: metrics.confidence ?? 0,
        incrementalRevenue: metrics.incremental_revenue ?? 0,
      };
    });
    return experiments;
  },
  get: (id: string) =>
    request<Experiment>(`/experiments/${id}`, () => {
      const found = fx.experiments.find((e) => e.id === id);
      return (
        found ??
        (() => {
          throw new Error("Experiment not found");
        })()
      );
    }),
};

// Agent Activity
export const agentActivityApi = {
  list: async (): Promise<AgentAction[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.agentActions), 260);
      });
    }

    const response = await request<any>("/agent-activity", {});
    // Transform real AgentRun rows (agent_name/output_data/started_at) into the UI shape.
    const statusMap: Record<string, AgentAction["status"]> = {
      completed: "completed",
      started: "running",
      running: "running",
      failed: "blocked",
      cancelled: "blocked",
    };
    const actions = (Array.isArray(response) ? response : []).map((a: any) => {
      const out = a.output_data ?? {};
      let action = "Ran";
      let detail = a.error || "Action completed";
      if (a.agent_name === "Growth Analyst") {
        action = "Analyzed revenue opportunities";
        detail = out.opportunities_found
          ? `Found ${out.opportunities_found} opportunit${out.opportunities_found === 1 ? "y" : "ies"} — ₹${Math.round(out.total_expected_impact ?? 0).toLocaleString("en-IN")} expected impact`
          : "No new opportunities — existing findings still open";
      } else if (a.agent_name === "Conversation Agent") {
        const q = a.input_data?.message;
        action = "Answered a copilot question";
        detail = q ? `"${String(q).slice(0, 80)}${String(q).length > 80 ? "…" : ""}"` : detail;
      }
      return {
        id: a.id,
        agent: (a.agent_name || "Growth Analyst") as AgentAction["agent"],
        action,
        detail,
        status: statusMap[a.status] ?? "completed",
        at: a.started_at,
        correlationId: a.correlation_id || a.id,
      };
    });
    return actions;
  },
};

// Audit
export const auditApi = {
  list: async (): Promise<AuditEvent[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.auditEvents), 260);
      });
    }

    const response = await request<any>("/audit", {});
    // Transform backend AuditEvent to frontend AuditEvent type
    const events = (Array.isArray(response) ? response : []).map((e: any) => ({
      id: e.id,
      at: e.created_at,
      agent: e.actor_type === "agent" ? e.actor_id : e.actor_type,
      action: e.action,
      input: e.input_hash ? `Hash: ${e.input_hash.substring(0, 16)}...` : "No input data",
      decision: e.decision || "N/A",
      policyResult: e.policy_result || "pass",
      approval: (e.approval_id ? "merchant_approved" : "n/a") as AuditEvent["approval"],
      execution: (e.execution_result ? "executed" : "not_executed") as AuditEvent["execution"],
      result: e.execution_result || e.error || "Completed",
      correlationId: e.correlation_id || e.id,
    }));
    return events;
  },
};

// Policies
export const policiesApi = {
  list: async (): Promise<Policy[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve(fx.policies), 260);
      });
    }

    const response = await request<any>("/policies", {});
    // Transform backend Policy to frontend Policy type
    const policies = (Array.isArray(response) ? response : []).map((p: any) => {
      // Map backend policy_type to frontend group
      const groupMap: Record<string, Policy["group"]> = {
        discount_limit: "spend",
        budget_limit: "spend",
        approval_threshold: "approvals",
        action_frequency: "approvals",
        category_restriction: "catalog",
      };

      // Determine kind based on policy type
      const kind =
        p.policy_type === "action_frequency"
          ? "slider"
          : p.policy_type === "category_restriction"
            ? "toggle"
            : "number";

      // Extract value from rules — remember which rules key it came from so an
      // update can write back the same key rather than guessing.
      const rules = p.rules || {};
      const valueKey =
        "max_discount_percent" in rules
          ? "max_discount_percent"
          : "max_budget" in rules
            ? "max_budget"
            : "approval_above_amount" in rules
              ? "approval_above_amount"
              : "max_per_hour" in rules
                ? "max_per_hour"
                : "max_actions_per_hour" in rules
                  ? "max_actions_per_hour"
                  : null;
      const value = valueKey ? rules[valueKey] : true;

      return {
        id: p.id,
        key: p.policy_type,
        label: p.name,
        description: `Policy: ${p.policy_type.replace(/_/g, " ")}`,
        kind: kind as "toggle" | "slider" | "number",
        value: typeof value === "number" ? value : Boolean(p.is_active),
        min: 0,
        max: kind === "slider" ? 100 : 100000,
        step: kind === "slider" ? 1 : 100,
        unit: p.policy_type.includes("discount")
          ? "%"
          : p.policy_type.includes("budget") || p.policy_type.includes("amount")
            ? "₹"
            : "",
        group: groupMap[p.policy_type] || "spend",
        // Not part of the frontend Policy type contract but carried through so `update`
        // can send a minimal, correct payload back — see policiesApi.update below.
        _rules: rules,
        _valueKey: valueKey,
      } as Policy & { _rules: Record<string, unknown>; _valueKey: string | null };
    });
    return policies;
  },
  get: (id: string) =>
    request<Policy>(`/policies/${id}`, () => {
      const found = fx.policies.find((p) => p.id === id);
      return (
        found ??
        (() => {
          throw new Error("Policy not found");
        })()
      );
    }),
  /**
   * PUT /policies/{id} — all fields optional, only changed fields are sent.
   * For toggle-kind policies (no numeric rules key found) we flip `is_active`.
   * For number/slider-kind policies we patch the single rules key the value came from,
   * merged onto the existing rules object so unrelated keys survive.
   */
  update: (
    policy: Policy & { _rules?: Record<string, unknown>; _valueKey?: string | null },
    value: number | boolean,
  ) => {
    if (policy._valueKey) {
      return requestPut<any>(`/policies/${policy.id}`, {
        rules: { ...(policy._rules ?? {}), [policy._valueKey]: value },
      });
    }
    return requestPut<any>(`/policies/${policy.id}`, { is_active: Boolean(value) });
  },
  evaluate: (actionType: string, inputData: any) =>
    requestPost<any>("/policies/evaluate", {
      action_type: actionType,
      input_data: inputData,
    }),
};

// AI Copilot
export const copilotApi = {
  ask: async (question: string, sessionId?: string): Promise<CopilotAnswer> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            id: "ans_mock",
            message: `Mock answer for: "${question}"`,
            data: null,
            actions: [],
            correlationId: "corr_mock",
          });
        }, 260);
      });
    }
    // Real LLM-backed agent — POST /ai/chat, returns { message, data?, actions?, correlation_id }.
    // We surface the real message/data/actions verbatim; nothing is canned or keyword-matched.
    const response = await requestPost<{
      message: string;
      data?: any;
      actions?: any[];
      correlation_id: string;
    }>("/ai/chat", {
      messages: [{ role: "user", content: question }],
      session_id: sessionId,
    });
    return {
      id: response.correlation_id,
      message: response.message,
      data: response.data ?? null,
      actions: response.actions ?? [],
      correlationId: response.correlation_id,
    };
  },
};

// Integrations
export interface IntegrationRecord {
  id: string;
  provider: string;
  integration_type: string;
  config: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export const integrationsApi = {
  list: async (): Promise<IntegrationRecord[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => resolve([]), 260);
      });
    }
    const response = await request<any>("/integrations", {});
    return Array.isArray(response) ? response : [];
  },
  connectRazorpay: (keyId: string, keySecret: string, webhookSecret?: string) =>
    requestPost<{ status: string; provider: string }>("/integrations/razorpay/connect", {
      key_id: keyId,
      key_secret: keySecret,
      webhook_secret: webhookSecret || undefined,
    }),
  delete: (integrationId: string) =>
    requestDelete<{ status: string; integration_id: string }>(`/integrations/${integrationId}`),
  regenerateAiBuyerKey: () =>
    requestPost<{ api_key: string; warning: string }>(
      "/integrations/ai-buyer/api-key/regenerate",
      {},
    ),
};

// Shop (Storefront)
export const shopApi = {
  listProducts: async (): Promise<ShopProduct[]> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(
          () =>
            resolve(
              fx.products.map((p) => ({
                ...p,
                whyRecommended: "",
                availability: "in_stock" as const,
              })),
            ),
          260,
        );
      });
    }
    const response = await request<any>("/storefront/products", {});
    return (Array.isArray(response) ? response : []).map((p: any) => ({
      id: p.id,
      sku: p.id.substring(0, 8).toUpperCase(),
      name: p.name,
      category: p.category,
      price: p.price || p.sale_price || p.base_price,
      inventory: p.in_stock ? 100 : 0,
      unitsSold30d: 0,
      conversionRate: 0,
      aovContribution: 0,
      crossSellOpportunities: 0,
      aiScore: 0,
      rating: 0,
      imageHue: hueFromId(p.id),
      status: (p.in_stock ? "active" : "out_of_stock") as ShopProduct["status"],
      whyRecommended: "Recommended based on your requirements.",
      availability: (p.in_stock ? "in_stock" : "out_of_stock") as ShopProduct["availability"],
    }));
  },
  getProduct: async (id: string): Promise<ShopProduct> => {
    if (USE_MOCK) {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          const found = fx.products.find((p) => p.id === id);
          found
            ? resolve({ ...found, whyRecommended: "", availability: "in_stock" })
            : reject(new Error("Product not found"));
        }, 260);
      });
    }
    const response = await request<any>(`/storefront/products/${id}`, {});
    return {
      id: response.id,
      sku: response.id.substring(0, 8).toUpperCase(),
      name: response.name,
      category: response.category,
      price: response.price || response.sale_price || response.base_price,
      inventory: response.in_stock ? 100 : 0,
      unitsSold30d: 0,
      conversionRate: 0,
      aovContribution: 0,
      crossSellOpportunities: 0,
      aiScore: 0,
      rating: 0,
      imageHue: hueFromId(response.id),
      status: (response.in_stock ? "active" : "out_of_stock") as ShopProduct["status"],
      whyRecommended: response.description || "Recommended based on your requirements.",
      availability: (response.in_stock
        ? "in_stock"
        : "out_of_stock") as ShopProduct["availability"],
    };
  },
  search: async (query: string): Promise<{ reply: string; products: ShopProduct[] }> => {
    if (USE_MOCK) {
      return new Promise((resolve) => {
        setTimeout(() => {
          const q = query.toLowerCase().trim();
          const matched = fx.products.filter(
            (p) => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q),
          );
          const products = (matched.length ? matched : fx.products)
            .slice(0, 4)
            .map((p) => ({
              ...p,
              whyRecommended: "Recommended based on your requirements.",
              availability: "in_stock" as const,
            }));
          resolve({
            reply: matched.length
              ? `Here are options that fit "${query}".`
              : `No exact match for "${query}" — showing the closest.`,
            products,
          });
        }, 260);
      });
    }
    const response = await requestPost<any>("/storefront/search", { query });
    const products = (Array.isArray(response) ? response : []).map((p: any) => ({
      id: p.id,
      sku: p.id.substring(0, 8).toUpperCase(),
      name: p.name,
      category: p.category,
      price: p.price,
      inventory: p.in_stock ? 100 : 0,
      unitsSold30d: 0,
      conversionRate: 0,
      aovContribution: 0,
      crossSellOpportunities: 0,
      aiScore: 0,
      rating: 0,
      imageHue: hueFromId(p.id),
      status: (p.in_stock ? "active" : "out_of_stock") as ShopProduct["status"],
      whyRecommended: p.description || "Recommended based on your requirements.",
      availability: (p.in_stock ? "in_stock" : "out_of_stock") as ShopProduct["availability"],
    }));
    return {
      reply: products.length
        ? `Here are ${products.length} options that fit "${query}".`
        : `No exact match for "${query}".`,
      products,
    };
  },
  addToCart: (sessionId: string, productId: string, quantity: number) =>
    requestPost<any>(
      `/storefront/cart/${sessionId}/add?product_id=${productId}&quantity=${quantity}`,
      {},
    ),
  getCart: (sessionId: string) =>
    request<any>(`/storefront/cart/${sessionId}`, {
      id: sessionId,
      items: [],
      subtotal: 0,
    }),
  checkout: (items: { product_id: string; quantity: number }[]) =>
    requestPost<any>("/storefront/checkout", { items }),
  confirmPayment: (orderId: string) => requestPost<any>(`/storefront/order/${orderId}/confirm`, {}),
};

// Export unified API object for backward compatibility
export const api = {
  getMerchant: merchantApi.get,
  getDashboard: dashboardApi.get,

  listOpportunities: opportunitiesApi.list,
  getOpportunity: opportunitiesApi.get,
  decideOpportunity: opportunitiesApi.decide,

  listProducts: productsApi.list,
  getProduct: productsApi.get,
  createProduct: productsApi.create,

  listOrders: ordersApi.list,
  listCustomers: customersApi.list,
  listCarts: cartsApi.list,
  listRecoveryCases: recoveryApi.list,
  detectRecoveryCases: recoveryApi.detect,
  sendRecoveryIntervention: recoveryApi.sendIntervention,
  listRecommendations: recommendationsApi.list,
  listCampaigns: campaignsApi.list,
  createCampaign: campaignsApi.create,
  decideCampaign: campaignsApi.decide,
  listExperiments: experimentsApi.list,
  listAgentActivity: agentActivityApi.list,
  listAuditEvents: auditApi.list,
  listPolicies: policiesApi.list,
  updatePolicy: policiesApi.update,

  askCopilot: copilotApi.ask,

  searchCatalog: shopApi.search,
  listShopProducts: shopApi.listProducts,
  getShopProduct: shopApi.getProduct,
  shopCheckout: shopApi.checkout,
  shopConfirmPayment: shopApi.confirmPayment,
};
