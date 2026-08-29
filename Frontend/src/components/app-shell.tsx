import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  BadgeCheck,
  BarChart3,
  Boxes,
  Bot,
  ClipboardList,
  CreditCard,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  Lightbulb,
  Megaphone,
  Menu,
  Plug,
  Receipt,
  Settings,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Users,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { auth } from "@/services/sarthi";

const nav: { group: string; items: { to: string; label: string; icon: typeof Gauge }[] }[] = [
  {
    group: "Revenue",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/opportunities", label: "Opportunities", icon: Lightbulb },
      { to: "/ai-copilot", label: "AI Copilot", icon: Bot },
      { to: "/revenue-recovery", label: "Revenue Recovery", icon: Receipt },
      { to: "/analytics", label: "Analytics", icon: BarChart3 },
    ],
  },
  {
    group: "Commerce",
    items: [
      { to: "/products", label: "Products", icon: Boxes },
      { to: "/orders", label: "Orders", icon: CreditCard },
      { to: "/customers", label: "Customers", icon: Users },
      { to: "/carts", label: "Carts", icon: ShoppingBag },
    ],
  },
  {
    group: "Growth",
    items: [
      { to: "/campaigns", label: "Campaigns", icon: Megaphone },
      { to: "/recommendations", label: "Recommendations", icon: Sparkles },
      { to: "/experiments", label: "Experiments", icon: FlaskConical },
    ],
  },
  {
    group: "Governance",
    items: [
      { to: "/agent-activity", label: "Agent Activity", icon: Activity },
      { to: "/audit", label: "Audit Trail", icon: ClipboardList },
      { to: "/policies", label: "Policy Center", icon: ShieldCheck },
    ],
  },
  {
    group: "Workspace",
    items: [
      { to: "/integrations", label: "Integrations", icon: Plug },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function SarthiMark({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span className="relative grid size-7 place-items-center rounded-md border border-primary/40 bg-primary/10">
        <span className="block h-3 w-[2px] rotate-[24deg] bg-primary" aria-hidden />
        <span className="absolute bottom-1.5 left-1.5 size-1 rounded-full bg-primary" aria-hidden />
      </span>
      <span className="font-display text-[15px] font-semibold tracking-tight">Sarthi</span>
    </span>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <nav aria-label="Main" className="space-y-6 px-3 py-4">
      {nav.map((section) => (
        <div key={section.group}>
          <p className="eyebrow px-2 pb-2">{section.group}</p>
          <ul className="space-y-0.5">
            {section.items.map((item) => {
              const active = pathname === item.to || pathname.startsWith(`${item.to}/`);
              const Icon = item.icon;
              return (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "group relative flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[13px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      active
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
                    )}
                  >
                    {active ? (
                      <motion.span
                        layoutId="nav-active"
                        className="absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-full bg-primary"
                        aria-hidden
                      />
                    ) : null}
                    <Icon className="size-4 shrink-0" aria-hidden />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const reduced = useReducedMotion();
  const navigate = useNavigate();

  // Every merchant-cockpit route renders inside AppShell, so this is the single guard point:
  // an unauthenticated visitor is redirected to /login rather than being able to browse
  // merchant-only data (opportunities, orders, policies, audit trail, ...).
  useEffect(() => {
    if (!auth.isAuthenticated()) {
      navigate({ to: "/login" });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  return (
    <div className="min-h-screen bg-background">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <div className="flex">
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
          <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-5">
            <Link
              to="/dashboard"
              className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <SarthiMark />
            </Link>
            <span className="rounded-full border border-border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
              Merchant Cockpit
            </span>
          </div>
          <div className="flex-1 overflow-y-auto">
            <NavList />
          </div>
          <div className="space-y-2 border-t border-sidebar-border p-3">
            <Link
              to="/shop"
              className="flex items-center gap-2 rounded-md border border-border px-2.5 py-2 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
            >
              <ShoppingBag className="size-4" aria-hidden /> Storefront demo (shopper view)
            </Link>
            <Link
              to="/"
              className="block px-2.5 text-[11px] text-muted-foreground transition-colors hover:text-foreground"
            >
              ← Back to landing page
            </Link>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-md md:px-8">
            <div className="flex items-center gap-3">
              <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="lg:hidden"
                    aria-label="Open navigation"
                  >
                    <Menu className="size-4" aria-hidden />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-72 overflow-y-auto bg-sidebar p-0">
                  <SheetTitle className="sr-only">Navigation</SheetTitle>
                  <div className="flex h-14 items-center border-b border-sidebar-border px-5">
                    <SarthiMark />
                  </div>
                  <NavList onNavigate={() => setOpen(false)} />
                </SheetContent>
              </Sheet>
              <span className="lg:hidden">
                <SarthiMark />
              </span>
              <span className="hidden items-center gap-2 text-xs text-muted-foreground lg:flex">
                <BadgeCheck className="size-3.5 text-positive" aria-hidden />
                Kadam Athletics · Razorpay test mode
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 rounded-full border border-border px-2.5 py-1 text-[11px] text-muted-foreground sm:inline-flex">
                <span className="size-1.5 animate-pulse rounded-full bg-positive" aria-hidden />
                Agent running
              </span>
              <Button asChild size="sm" variant="outline">
                <Link to="/ai-copilot">Ask Sarthi</Link>
              </Button>
            </div>
          </header>

          <main id="main" className="min-w-0 flex-1 px-4 pb-20 pt-8 md:px-8">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={pathname}
                initial={reduced ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduced ? undefined : { opacity: 0, y: -6 }}
                transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
                className="mx-auto w-full max-w-[1240px] space-y-8"
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </div>
  );
}
