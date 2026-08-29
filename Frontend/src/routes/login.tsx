import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Loader2, Lock } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { SarthiMark } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { auth } from "@/services/sarthi";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — Sarthi" },
      {
        name: "description",
        content: "Sign in to the Sarthi revenue cockpit to review AI opportunities and approvals.",
      },
      { property: "og:title", content: "Sign in — Sarthi" },
      { property: "og:description", content: "Access your merchant revenue cockpit." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@strideathletics.com");
  const [password, setPassword] = useState("demo123456");
  const [state, setState] = useState<"idle" | "submitting" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 4) {
      setState("error");
      setErrorMessage("Enter a password of at least 4 characters to continue.");
      return;
    }

    setState("submitting");
    setErrorMessage("");

    try {
      await auth.login(email, password);
      toast.success("Welcome back!", {
        description: "Successfully signed in to your revenue cockpit.",
      });
      navigate({ to: "/dashboard" });
    } catch (error) {
      setState("error");
      const message = error instanceof Error ? error.message : "Login failed";
      setErrorMessage(message);
      toast.error("Sign in failed", {
        description: message,
      });
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="flex flex-col justify-between px-6 py-10 md:px-14">
        <SarthiMark />
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto w-full max-w-sm"
        >
          <h1 className="text-3xl font-semibold tracking-tight">Sign in</h1>
          <p className="mt-2 text-sm text-muted-foreground">Continue to your revenue cockpit.</p>

          <form className="mt-8 space-y-5" onSubmit={submit} noValidate>
            <div className="space-y-2">
              <Label htmlFor="email">Work email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setState("idle");
                  setErrorMessage("");
                }}
                aria-invalid={state === "error"}
                aria-describedby={state === "error" ? "login-error" : undefined}
                required
              />
              {state === "error" && errorMessage ? (
                <p id="login-error" role="alert" className="text-xs text-destructive">
                  {errorMessage}
                </p>
              ) : null}
            </div>
            <Button type="submit" className="w-full" disabled={state === "submitting"}>
              {state === "submitting" ? (
                <Loader2 className="size-4 animate-spin" aria-hidden />
              ) : null}
              {state === "submitting" ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <div className="mt-6 rounded-lg border border-border bg-muted/50 p-4">
            <p className="text-xs font-medium">Demo Credentials</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Email: demo@strideathletics.com
              <br />
              Password: demo123456
            </p>
          </div>

          <p className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
            <Lock className="size-3.5" aria-hidden /> Secure authentication with JWT tokens.
          </p>
          <p className="mt-6 text-sm text-muted-foreground">
            New merchant?{" "}
            <Link to="/onboarding" className="text-primary underline-offset-4 hover:underline">
              Start onboarding
            </Link>
          </p>
        </motion.div>
        <p className="text-xs text-muted-foreground">© 2026 Sarthi</p>
      </div>

      <aside className="grain hidden border-l border-border bg-surface p-14 lg:flex lg:flex-col lg:justify-center">
        <p className="eyebrow">Inside the cockpit</p>
        <blockquote className="mt-6 max-w-md font-display text-3xl font-semibold leading-tight tracking-tight">
          "It proposed the shoe + socks bundle with the co-purchase evidence attached. We approved
          it in forty seconds."
        </blockquote>
        <p className="mt-6 text-sm text-muted-foreground">Head of Growth, Stride Athletics</p>
      </aside>
    </div>
  );
}
