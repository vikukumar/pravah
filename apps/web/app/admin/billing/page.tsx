"use client";
import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { CreditCard, TrendingUp, Users, IndianRupee, Filter, RefreshCw, ExternalLink } from "lucide-react";

interface Subscription { id: string; organisation_id: string; organisation_name: string; plan_name: string; plan_price_monthly: number; status: string; billing_period: string; payment_gateway: string; current_period_start: string; current_period_end: string; trial_end: string | null; cancel_at_period_end: boolean; created_at: string; }
interface Payment { id: string; subscription_id: string; amount: number; currency: string; status: string; payment_gateway: string; gateway_payment_id: string; created_at: string; }

const STATUS_BADGE: Record<string, string> = { active: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25", trial: "bg-blue-500/15 text-blue-400 border-blue-500/25", past_due: "bg-amber-500/15 text-amber-400 border-amber-500/25", cancelled: "bg-red-500/15 text-red-400 border-red-500/25", expired: "bg-slate-700 text-slate-400 border-slate-600", grace_period: "bg-orange-500/15 text-orange-400 border-orange-500/25" };
const GATEWAY_ICONS: Record<string, string> = { razorpay: "🔵", cashfree: "🟡", stripe: "🟣" };

function fmt(d: string) { return d ? new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"; }

export default function BillingPage() {
  const toast = useToast();
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [tab, setTab] = useState<"subscriptions" | "payments">("subscriptions");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [subsData, paymentsData] = await Promise.all([
        fetchApi<Subscription[]>("/admin/billing/subscriptions?limit=100"),
        fetchApi<Payment[]>("/admin/billing/payments?limit=100"),
      ]);
      setSubs(subsData);
      setPayments(paymentsData);
    } catch { toast.error("Failed to load billing data"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filteredSubs = statusFilter === "all" ? subs : subs.filter((s) => s.status === statusFilter);
  const totalMRR = subs.filter((s) => s.status === "active" && s.billing_period === "monthly").reduce((sum, s) => sum + (s.plan_price_monthly || 0), 0);
  const totalPayments = payments.filter((p) => p.status === "success").reduce((sum, p) => sum + p.amount, 0);
  const statuses = ["active", "trial", "past_due", "grace_period", "cancelled", "expired"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-pink-500/10 border border-pink-500/20 flex items-center justify-center">
            <CreditCard className="w-5 h-5 text-pink-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Billing & Invoices</h1>
            <p className="text-slate-400 text-sm">{subs.length} subscriptions · {payments.length} payments</p>
          </div>
        </div>
        <Button onClick={load} disabled={loading} variant="outline" size="sm" leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />}>Refresh</Button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "MRR (Active)",     value: `₹${totalMRR.toLocaleString()}`, icon: TrendingUp,    color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
          { label: "Total Collected",  value: `₹${totalPayments.toLocaleString()}`, icon: IndianRupee, color: "text-indigo-400",  bg: "bg-indigo-500/10 border-indigo-500/20" },
          { label: "Active Subs",      value: subs.filter(s => s.status === "active").length, icon: Users, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
          { label: "Trial Users",      value: subs.filter(s => s.status === "trial").length, icon: CreditCard, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label} className={`p-4 border ${stat.bg}`}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-xs text-slate-500">{stat.label}</span>
              </div>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </Card>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-900/50 rounded-xl w-fit border border-slate-800">
        {(["subscriptions", "payments"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${tab === t ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"}`}>{t}</button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : tab === "subscriptions" ? (
        <div className="space-y-3">
          {/* Status filter */}
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="w-4 h-4 text-slate-500" />
            {["all", ...statuses].map((s) => (
              <button key={s} onClick={() => setStatusFilter(s)}
                className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all border ${statusFilter === s ? "bg-indigo-600/30 border-indigo-500/50 text-indigo-300" : "bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600"}`}>
                {s === "all" ? "All" : s.replace(/_/g, " ")}
                {s !== "all" && <span className="ml-1 text-[10px] opacity-60">({subs.filter(x => x.status === s).length})</span>}
              </button>
            ))}
          </div>

          {/* Subscriptions table */}
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-900/60 border-b border-slate-800">
                  <tr>
                    {["Workspace", "Plan", "Status", "Period", "Gateway", "Period End", "Trial End"].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredSubs.length === 0 ? (
                    <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-500">No subscriptions found</td></tr>
                  ) : filteredSubs.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-200">{sub.organisation_name || "—"}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-300">{sub.plan_name}</div>
                        {sub.plan_price_monthly != null && <div className="text-slate-500">₹{sub.plan_price_monthly}/mo</div>}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border capitalize ${STATUS_BADGE[sub.status] || "bg-slate-700 text-slate-400"}`}>
                          {sub.status?.replace(/_/g, " ")}
                        </span>
                        {sub.cancel_at_period_end && <div className="text-[10px] text-red-400 mt-0.5">Cancels at period end</div>}
                      </td>
                      <td className="px-4 py-3 text-slate-400 capitalize">{sub.billing_period}</td>
                      <td className="px-4 py-3 text-slate-400">
                        {sub.payment_gateway ? <>{GATEWAY_ICONS[sub.payment_gateway] || "💳"} {sub.payment_gateway}</> : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-400">{fmt(sub.current_period_end)}</td>
                      <td className="px-4 py-3 text-slate-400">{sub.trial_end ? fmt(sub.trial_end) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-900/60 border-b border-slate-800">
                <tr>
                  {["Gateway Payment ID", "Amount", "Currency", "Status", "Gateway", "Date"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {payments.length === 0 ? (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No payments found</td></tr>
                ) : payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-slate-300">{p.gateway_payment_id || "—"}</td>
                    <td className="px-4 py-3 font-bold text-white">₹{(p.amount || 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-slate-400">{p.currency}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${p.status === "success" ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/25" : p.status === "failed" ? "bg-red-500/15 text-red-400 border-red-500/25" : "bg-amber-500/15 text-amber-400 border-amber-500/25"}`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400">{GATEWAY_ICONS[p.payment_gateway] || "💳"} {p.payment_gateway}</td>
                    <td className="px-4 py-3 text-slate-400">{fmt(p.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
