import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { DataTable, type Column } from "@/components/data-table";
import {
  PageHeader,
  Panel,
  QueryBoundary,
  StatusBadge,
  inr,
  num,
  pct,
  statusTone,
} from "@/components/primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/services/sarthi";
import type { Product } from "@/lib/types";

export const Route = createFileRoute("/products/")({
  head: () => ({
    meta: [
      { title: "Catalog intelligence — Sarthi" },
      {
        name: "description",
        content:
          "Every product scored by Sarthi for conversion, AOV contribution and cross-sell potential.",
      },
      { property: "og:title", content: "Catalog intelligence — Sarthi" },
      {
        property: "og:description",
        content: "Product-level AI scoring, inventory health and cross-sell potential.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ProductsPage,
});

function ProductsPage() {
  const [q, setQ] = useState("");
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  // Search hits the real backend q= filter (not a client-side slice of one page),
  // so it finds matches across the whole catalog, not just the first 100 rows.
  const query = useQuery({
    queryKey: ["products", q],
    queryFn: () => api.listProducts({ q: q || undefined }),
  });

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [basePrice, setBasePrice] = useState("999");

  const create = useMutation({
    mutationFn: () => api.createProduct({ name, category, basePrice: Number(basePrice) || 0 }),
    onSuccess: () => {
      toast.success("Product added", { description: `${name} is live in the catalog.` });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      setShowCreate(false);
      setName("");
      setCategory("");
      setBasePrice("999");
    },
    onError: (err: any) => {
      toast.error("Couldn't add product", { description: err?.message ?? "Try again." });
    },
  });

  const columns: Column<Product>[] = [
    {
      key: "name",
      header: "Product",
      primary: true,
      cell: (p) => (
        <div className="flex items-center gap-3">
          <span
            className="size-8 shrink-0 rounded-md border border-border"
            style={{ background: `oklch(0.9 0.06 ${p.imageHue})` }}
            aria-hidden
          />
          <div>
            <p className="font-medium">{p.name}</p>
            <p className="tabular text-xs text-muted-foreground">{p.sku}</p>
          </div>
        </div>
      ),
    },
    { key: "category", header: "Category", mobileLabel: "Category", cell: (p) => p.category },
    {
      key: "price",
      header: "Price",
      align: "right",
      mobileLabel: "Price",
      cell: (p) => <span className="tabular">{inr(p.price)}</span>,
    },
    {
      key: "inv",
      header: "Inventory",
      align: "right",
      mobileLabel: "Inventory",
      cell: (p) => <span className="tabular">{num(p.inventory)}</span>,
    },
    {
      key: "cvr",
      header: "Conversion",
      align: "right",
      mobileLabel: "Conversion",
      cell: (p) => <span className="tabular">{pct(p.conversionRate)}</span>,
    },
    {
      key: "score",
      header: "AI score",
      align: "right",
      mobileLabel: "AI score",
      cell: (p) => (
        <div className="ml-auto flex w-28 items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-[width] duration-700"
              style={{ width: `${p.aiScore}%` }}
            />
          </div>
          <span className="tabular text-xs">{p.aiScore}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      mobileLabel: "Status",
      cell: (p) => (
        <StatusBadge tone={statusTone(p.status)}>{p.status.replace(/_/g, " ")}</StatusBadge>
      ),
    },
  ];

  return (
    <AppShell>
      <PageHeader
        eyebrow="Commerce"
        title="Catalog intelligence"
        description="Sarthi scores each product on conversion, contribution to AOV and untapped cross-sell paths. Open a product to see the evidence."
        actions={
          <div className="flex items-center gap-2">
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search products"
              aria-label="Search products"
              className="w-56"
            />
            <Button onClick={() => setShowCreate(true)}>Add product</Button>
          </div>
        }
      />
      <QueryBoundary
        query={query}
        rows={5}
        isEmpty={(d) => d.length === 0}
        emptyTitle="No products yet"
      >
        {(rows) => (
          <Panel
            title="Products"
            description={`${rows.length} product${rows.length === 1 ? "" : "s"}${q ? ` matching "${q}"` : ""}`}
          >
            <DataTable
              caption="Product catalog with AI scores"
              columns={columns}
              rows={rows}
              onRowClick={(p) => navigate({ to: "/products/$id", params: { id: p.id } })}
            />
          </Panel>
        )}
      </QueryBoundary>

      {showCreate ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Add product</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowCreate(false)}>
                Close
              </Button>
            </div>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                create.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="prod_name">Name</Label>
                <Input
                  id="prod_name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Trail Runner Pro"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="prod_category">Category</Label>
                <Input
                  id="prod_category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  placeholder="Running Shoes"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="prod_price">Base price (₹)</Label>
                <Input
                  id="prod_price"
                  type="number"
                  min={0}
                  value={basePrice}
                  onChange={(e) => setBasePrice(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={create.isPending}>
                  {create.isPending ? "Adding…" : "Add product"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
