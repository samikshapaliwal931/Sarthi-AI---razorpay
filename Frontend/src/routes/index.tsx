import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { SarthiMark } from "@/components/app-shell";
import { Counter, Reveal, inr } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { useLenis } from "@/hooks/use-lenis";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Sarthi — the AI Revenue Agent for ecommerce merchants" },
      {
        name: "description",
        content:
          "Sarthi finds revenue opportunities in your catalog, orders and payments, explains the evidence, and executes only what your policies allow.",
      },
      { property: "og:title", content: "Sarthi — the AI Revenue Agent for ecommerce" },
      {
        property: "og:description",
        content:
          "Discover, explain, propose, govern, approve, execute, measure. A revenue agent merchants can actually run their business on.",
      },
    ],
  }),
  component: Landing,
});

const arc = [
  {
    step: "Discover",
    copy: "Continuously reads catalog, orders, carts, payments and customer behaviour.",
  },
  { step: "Explain", copy: "Every finding carries the observations and metrics that produced it." },
  {
    step: "Propose",
    copy: "Bounded actions with expected revenue, orders and a confidence interval.",
  },
  {
    step: "Govern",
    copy: "Policy engine checks discount, spend, rate and communication limits first.",
  },
  { step: "Approve", copy: "You decide. Pricing and campaign changes never bypass your sign-off." },
  {
    step: "Execute",
    copy: "Recovery workflows, bundles and campaigns go live with a correlation ID.",
  },
  { step: "Measure", copy: "Attribution reconciles what actually happened against the forecast." },
  { step: "Learn", copy: "Experiments quantify lift so the next proposal is better calibrated." },
];

function Landing() {
  useLenis();
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <SarthiMark />
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link to="/shop">
                Storefront demo{" "}
                <span className="ml-1 text-[10px] text-muted-foreground">(shopper view)</span>
              </Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link to="/login">Sign in</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/dashboard">Open merchant cockpit</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="grain relative overflow-hidden border-b border-border">
        <div className="mx-auto max-w-6xl px-6 py-24 md:py-36">
          <motion.p
            className="eyebrow"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            AI Revenue Agent · Ecommerce
          </motion.p>
          <motion.h1
            className="mt-6 max-w-4xl text-balance text-5xl font-semibold leading-[0.98] tracking-tight md:text-7xl"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.75, delay: 0.06, ease: [0.22, 1, 0.36, 1] }}
          >
            An AI employee that finds revenue, then asks permission to go get it.
          </motion.h1>
          <motion.p
            className="mt-7 max-w-xl text-base leading-relaxed text-muted-foreground"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.75, delay: 0.14 }}
          >
            Sarthi reads your catalog, orders, carts and payments; surfaces bounded revenue actions
            with the evidence behind them; and executes only inside the limits you set.
          </motion.p>
          <motion.div
            className="mt-10 flex flex-wrap gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.24 }}
          >
            <Button asChild size="lg">
              <Link to="/onboarding">
                Connect your store <ArrowRight className="size-4" aria-hidden />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/dashboard">See a live cockpit</Link>
            </Button>
          </motion.div>

          <dl className="mt-20 grid gap-8 border-t border-border pt-10 sm:grid-cols-3">
            {[
              { label: "AI-attributed revenue", value: 675000, fmt: (v: number) => inr(v, true) },
              { label: "Recovered revenue", value: 214000, fmt: (v: number) => inr(v, true) },
              {
                label: "Recommendation acceptance",
                value: 72,
                fmt: (v: number) => `${Math.round(v)}%`,
              },
            ].map((s) => (
              <div key={s.label}>
                <dt className="eyebrow">{s.label}</dt>
                <dd className="mt-3 text-4xl font-semibold tracking-tight">
                  <Counter value={s.value} format={s.fmt} />
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-24">
        <Reveal>
          <p className="eyebrow">The operating loop</p>
          <h2 className="mt-4 max-w-2xl text-3xl font-semibold tracking-tight md:text-4xl">
            Every rupee Sarthi touches is traceable end to end.
          </h2>
        </Reveal>
        <div className="mt-14 grid gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
          {arc.map((a, i) => (
            <Reveal key={a.step} delay={i * 0.04}>
              <div className="border-t border-border pt-5">
                <span className="tabular text-xs text-primary">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-3 text-lg font-semibold tracking-tight">{a.step}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{a.copy}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="border-y border-border bg-surface">
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-24 lg:grid-cols-2">
          <Reveal>
            <p className="eyebrow">Governance first</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">
              No automated action can exceed the limits you configure.
            </h2>
            <p className="mt-5 max-w-lg text-sm leading-relaxed text-muted-foreground">
              Discount ceilings, campaign budgets, automated spend, hourly action caps, refund and
              payment permissions, communication frequency. The policy engine evaluates before
              anything executes, and every decision — including blocks — lands in an immutable audit
              trail with a correlation ID.
            </p>
            <Button asChild className="mt-8" variant="outline">
              <Link to="/policies">
                <ShieldCheck className="size-4" aria-hidden /> Explore the policy center
              </Link>
            </Button>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="rounded-xl border border-border bg-card p-6 shadow-lift">
              <p className="eyebrow">Audit sample</p>
              <div className="mt-5 space-y-4 text-sm">
                <div className="hairline pb-4">
                  <p className="font-medium">Evaluate inventory promotion</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Input: discount Airflow Tee by 25% for 7 days
                  </p>
                </div>
                <div className="hairline pb-4">
                  <p className="text-destructive">Blocked — exceeds configured maximum of 15%</p>
                  <p className="mt-1 text-xs text-muted-foreground">Policy Engine · corr_1c03</p>
                </div>
                <p className="text-xs text-muted-foreground">
                  Execution: not executed. Merchant notified. Re-proposal allowed after restock.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-12 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <SarthiMark />
        <p>
          Real Razorpay test-mode payments, a real Postgres-backed agent and a real policy engine —
          not a static demo.
        </p>
      </footer>
    </div>
  );
}
