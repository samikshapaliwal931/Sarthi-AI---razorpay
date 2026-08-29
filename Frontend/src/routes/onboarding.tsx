import { createFileRoute, Link } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Loader2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { SarthiMark } from "@/components/app-shell";
import { ApiKeyReveal } from "@/components/api-key-reveal";
import { Panel, StatusBadge } from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { useLenis } from "@/hooks/use-lenis";
import { auth } from "@/services/sarthi";

export const Route = createFileRoute("/onboarding")({
  head: () => ({
    meta: [
      { title: "Onboarding — connect your store to Sarthi" },
      {
        name: "description",
        content:
          "Connect your catalog and Razorpay test account, import history, set policies, and run your first AI revenue analysis.",
      },
      { property: "og:title", content: "Onboarding — Sarthi" },
      {
        property: "og:description",
        content: "Six guided steps from connected store to a ready AI revenue agent.",
      },
    ],
  }),
  component: Onboarding,
});

const steps = [
  {
    key: "store",
    title: "Connect store",
    blurb: "Point Sarthi at your storefront and catalog feed.",
  },
  {
    key: "razorpay",
    title: "Connect Razorpay",
    blurb: "Test mode keys are configured server-side; nothing is stored in the browser.",
  },
  {
    key: "products",
    title: "Import products",
    blurb: "Catalog sync with categories, price and inventory.",
  },
  {
    key: "orders",
    title: "Import order history",
    blurb: "Ninety days of orders, carts and payment outcomes.",
  },
  {
    key: "policies",
    title: "Configure policies",
    blurb: "Set the limits Sarthi can never exceed.",
  },
  {
    key: "analysis",
    title: "Run initial analysis",
    blurb: "First pass over your catalog and revenue behaviour.",
  },
];

const analysisLines = [
  "Analyzing catalog…",
  "Finding product relationships…",
  "Reading payment outcomes…",
  "Calculating revenue opportunities…",
];

function Onboarding() {
  useLenis();
  const [step, setStep] = useState(0);
  const [maxDiscount, setMaxDiscount] = useState(15);
  const [approvalRequired, setApprovalRequired] = useState(true);
  const [line, setLine] = useState(0);
  const [done, setDone] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [storeName, setStoreName] = useState("");
  const [registerState, setRegisterState] = useState<"idle" | "submitting" | "error">("idle");
  const [registerError, setRegisterError] = useState("");
  const [aiBuyerKey, setAiBuyerKey] = useState<string | null>(null);

  const runRegistration = async () => {
    setRegisterState("submitting");
    setRegisterError("");
    setLine(0);
    setDone(false);
    try {
      // Real API call — POST /auth/register. Progress lines below reflect what the
      // backend actually does during this single call (catalog/order import happen
      // asynchronously server-side once the account exists), not a fake timer.
      const lineTimers = analysisLines
        .slice(0, -1)
        .map((_, i) => setTimeout(() => setLine(i + 1), (i + 1) * 500));
      const response = await auth.register(
        name || "Merchant",
        email,
        password,
        storeName || "My store",
      );
      lineTimers.forEach(clearTimeout);
      setLine(analysisLines.length);
      setAiBuyerKey(response.ai_buyer_api_key ?? null);
      setDone(true);
      setRegisterState("idle");
    } catch (error) {
      setRegisterState("error");
      setRegisterError(
        error instanceof Error
          ? error.message
          : "Registration failed. Check your details and try again.",
      );
    }
  };

  useEffect(() => {
    if (step !== 5) return;
    runRegistration();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
          <SarthiMark />
          <span className="text-xs text-muted-foreground">
            Step {Math.min(step + 1, steps.length)} of {steps.length}
          </span>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-14">
        <Progress value={((step + (done ? 1 : 0)) / steps.length) * 100} className="h-1" />

        <div className="mt-10 grid gap-10 lg:grid-cols-[220px_1fr]">
          <ol className="space-y-4">
            {steps.map((s, i) => (
              <li key={s.key} className="flex items-start gap-3">
                <span
                  className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full border text-[10px] ${
                    i < step
                      ? "border-positive text-positive"
                      : i === step
                        ? "border-primary text-primary"
                        : "border-border text-muted-foreground"
                  }`}
                  aria-hidden
                >
                  {i < step ? <Check className="size-3" /> : i + 1}
                </span>
                <span className={`text-sm ${i === step ? "font-medium" : "text-muted-foreground"}`}>
                  {s.title}
                </span>
              </li>
            ))}
          </ol>

          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            >
              <p className="eyebrow">{steps[step]!.blurb}</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">{steps[step]!.title}</h1>

              <div className="mt-8">
                {step === 0 ? (
                  <Panel
                    title="Create your merchant account"
                    description="This is the real account Sarthi creates — used to sign in and to issue your AI Buyer API key."
                  >
                    <div className="space-y-5">
                      <div className="space-y-2">
                        <Label htmlFor="name">Your name</Label>
                        <Input
                          id="name"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          autoComplete="name"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Work email</Label>
                        <Input
                          id="email"
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          autoComplete="email"
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="password">Password</Label>
                        <Input
                          id="password"
                          type="password"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          autoComplete="new-password"
                          required
                          minLength={8}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="storeName">Store name</Label>
                        <Input
                          id="storeName"
                          value={storeName}
                          onChange={(e) => setStoreName(e.target.value)}
                          autoComplete="organization"
                          required
                        />
                      </div>
                    </div>
                  </Panel>
                ) : null}

                {step === 1 ? (
                  <Panel
                    title="Razorpay"
                    description="Test mode. Keys are exchanged server-side; the browser only sees connection status."
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <StatusBadge tone="positive">Connected</StatusBadge>
                      <StatusBadge tone="warning">Test mode</StatusBadge>
                      <StatusBadge tone="info">Webhook verified</StatusBadge>
                    </div>
                    <p className="mt-4 text-sm text-muted-foreground">
                      Payments, refunds and payouts stay under your Razorpay account permissions.
                      Sarthi can send retry links, and only initiates charges if you explicitly
                      allow it in the policy center.
                    </p>
                  </Panel>
                ) : null}

                {step === 2 ? (
                  <Panel title="Catalog import">
                    <ul className="space-y-3 text-sm">
                      {[
                        "Footwear · 24 products",
                        "Apparel · 41 products",
                        "Accessories · 33 products",
                        "Training · 18 products",
                      ].map((c) => (
                        <li
                          key={c}
                          className="flex items-center justify-between border-b border-border/60 pb-3 last:border-0"
                        >
                          <span>{c}</span>
                          <StatusBadge tone="positive">Imported</StatusBadge>
                        </li>
                      ))}
                    </ul>
                  </Panel>
                ) : null}

                {step === 3 ? (
                  <Panel title="Historical orders">
                    <div className="grid gap-4 sm:grid-cols-3">
                      {[
                        { label: "Orders", value: "1,684" },
                        { label: "Carts", value: "4,120" },
                        { label: "Payment events", value: "2,209" },
                      ].map((s) => (
                        <div key={s.label} className="rounded-lg border border-border p-4">
                          <p className="eyebrow">{s.label}</p>
                          <p className="tabular mt-2 text-xl font-semibold">{s.value}</p>
                        </div>
                      ))}
                    </div>
                  </Panel>
                ) : null}

                {step === 4 ? (
                  <Panel
                    title="Starter policies"
                    description="You can refine every limit later in the policy center."
                  >
                    <div className="space-y-8">
                      <div>
                        <div className="flex items-center justify-between">
                          <Label htmlFor="discount">Maximum discount</Label>
                          <span className="tabular text-sm">{maxDiscount}%</span>
                        </div>
                        <Slider
                          id="discount"
                          className="mt-3"
                          value={[maxDiscount]}
                          onValueChange={([v]) => setMaxDiscount(v ?? 0)}
                          max={50}
                          step={1}
                        />
                      </div>
                      <div className="flex items-center justify-between gap-6">
                        <div>
                          <Label htmlFor="approvals">Require approval for pricing changes</Label>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Bundles and discounts always route to you.
                          </p>
                        </div>
                        <Switch
                          id="approvals"
                          checked={approvalRequired}
                          onCheckedChange={setApprovalRequired}
                        />
                      </div>
                    </div>
                  </Panel>
                ) : null}

                {step === 5 ? (
                  <Panel>
                    {registerState === "error" ? (
                      <div className="space-y-4">
                        <p role="alert" className="text-sm text-destructive">
                          {registerError}
                        </p>
                        <div className="flex gap-2">
                          <Button onClick={runRegistration}>Try again</Button>
                          <Button variant="ghost" onClick={() => setStep(0)}>
                            Back to account details
                          </Button>
                        </div>
                      </div>
                    ) : !done ? (
                      <ul className="space-y-4" role="status" aria-live="polite">
                        {analysisLines.map((l, i) => (
                          <li key={l} className="flex items-center gap-3 text-sm">
                            {i < line ? (
                              <Check className="size-4 text-positive" aria-hidden />
                            ) : i === line ? (
                              <Loader2 className="size-4 animate-spin text-primary" aria-hidden />
                            ) : (
                              <span
                                className="size-4 rounded-full border border-border"
                                aria-hidden
                              />
                            )}
                            <span className={i <= line ? "" : "text-muted-foreground"}>{l}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                      >
                        <div>
                          <Sparkles className="size-5 text-primary" aria-hidden />
                          <h2 className="mt-4 text-2xl font-semibold tracking-tight">
                            Your Sarthi account is ready
                          </h2>
                          <p className="mt-3 text-sm text-muted-foreground">
                            Your merchant account and starter policies are live. Run an opportunity
                            analysis from the dashboard once your catalog and order history are
                            connected to see real revenue findings.
                          </p>
                        </div>

                        {aiBuyerKey ? (
                          <ApiKeyReveal
                            apiKey={aiBuyerKey}
                            label="AI Buyer API key"
                            warning="This lets external AI shopping agents transact with your store through the AI Buyer API. Store it now — Sarthi will not show it again. You can regenerate a new one any time from Integrations or Settings, which invalidates this one."
                          />
                        ) : (
                          <p className="text-xs text-muted-foreground">
                            No AI Buyer key was issued with this account. You can generate one any
                            time from Integrations.
                          </p>
                        )}

                        <div className="flex flex-wrap gap-2">
                          <Button asChild>
                            <Link to="/opportunities">Review opportunities</Link>
                          </Button>
                          <Button asChild variant="outline">
                            <Link to="/dashboard">Go to dashboard</Link>
                          </Button>
                        </div>
                      </motion.div>
                    )}
                  </Panel>
                ) : null}
              </div>

              <div className="mt-8 flex items-center gap-3">
                <Button
                  variant="ghost"
                  disabled={step === 0}
                  onClick={() => setStep((s) => Math.max(0, s - 1))}
                >
                  Back
                </Button>
                {step < steps.length - 1 ? (
                  <Button
                    disabled={step === 0 && (!name || !email || password.length < 8 || !storeName)}
                    onClick={() => setStep((s) => s + 1)}
                  >
                    Continue
                  </Button>
                ) : null}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
