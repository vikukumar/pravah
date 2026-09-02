"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { Plan, Subscription, UsageMetrics } from "@pravah/shared-types";
import { formatDate } from "@/lib/utils";
import {
  CreditCard,
  Check,
  Zap,
  TrendingUp,
  ShieldCheck,
  Bot,
  Share2,
  Workflow,
  Users,
  FileText,
  Globe,
} from "lucide-react";

export default function BillingPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageMetrics | null>(null);
  const [selectedCurrency, setSelectedCurrency] = useState<string>("INR");
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>({ INR: 1.0, USD: 0.0119, EUR: 0.0111, GBP: 0.0094 });
  const [currencySymbols, setCurrencySymbols] = useState<Record<string, string>>({ INR: "₹", USD: "$", EUR: "€", GBP: "£" });
  const [isLoading, setIsLoading] = useState(true);

  // Upgrade Modal
  const [selectedPlanForUpgrade, setSelectedPlanForUpgrade] = useState<Plan | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "yearly">("monthly");
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  const fetchData = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const [plansRes, subRes, usageRes, ratesRes] = await Promise.all([
        fetchApi<Plan[]>("/billing/plans"),
        fetchApi<Subscription>("/billing/subscription"),
        fetchApi<UsageMetrics>("/billing/usage"),
        fetchApi<any>("/billing/exchange-rates").catch(() => null),
      ]);
      setPlans(plansRes);
      setSubscription(subRes);
      setUsage(usageRes);
      if (ratesRes?.rates) setExchangeRates(ratesRes.rates);
      if (ratesRes?.symbols) setCurrencySymbols(ratesRes.symbols);
    } catch {
      // Free plan fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeOrg]);

  const formatPrice = (priceInINR: number | undefined) => {
    if (!priceInINR || priceInINR === 0) return "0";
    const rate = exchangeRates[selectedCurrency] || 1.0;
    const converted = priceInINR * rate;
    const symbol = currencySymbols[selectedCurrency] || selectedCurrency;

    if (selectedCurrency === "INR") {
      return `₹${priceInINR.toLocaleString("en-IN")}`;
    }
    return `${symbol}${converted.toLocaleString(undefined, { minimumFractionDigits: converted % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 })}`;
  };

  const handleRazorpayUpgrade = async () => {
    if (!selectedPlanForUpgrade) return;
    setIsProcessingPayment(true);
    try {
      // 1. Create real order on server
      const orderData = await fetchApi<any>("/billing/razorpay/create-order", {
        method: "POST",
        body: JSON.stringify({
          plan_id: selectedPlanForUpgrade.id,
          billing_period: billingPeriod,
        }),
      });

      if (!orderData?.order_id || !orderData?.key_id) {
        throw new Error("Payment gateway not configured. Contact administrator.");
      }

      // 2. Open real Razorpay JS SDK checkout modal
      await new Promise<void>((resolve, reject) => {
        // Dynamically load Razorpay checkout script
        const loadScript = () =>
          new Promise<void>((res, rej) => {
            if ((window as any).Razorpay) { res(); return; }
            const script = document.createElement("script");
            script.src = "https://checkout.razorpay.com/v1/checkout.js";
            script.onload = () => res();
            script.onerror = () => rej(new Error("Failed to load Razorpay SDK."));
            document.body.appendChild(script);
          });

        loadScript().then(() => {
          const RazorpayInstance = new (window as any).Razorpay({
            key: orderData.key_id,
            order_id: orderData.order_id,
            amount: orderData.amount,
            currency: orderData.currency || "INR",
            name: "PRAVAH",
            description: `${selectedPlanForUpgrade!.name} Plan — ${billingPeriod}`,
            prefill: { name: "", email: "" },
            theme: { color: "#6366f1" },
            handler: async (response: any) => {
              try {
                // 3. Verify real payment signature on server (HMAC-SHA256)
                await fetchApi("/billing/razorpay/verify", {
                  method: "POST",
                  body: JSON.stringify({
                    plan_id: selectedPlanForUpgrade!.id,
                    billing_period: billingPeriod,
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature,
                  }),
                });
                resolve();
              } catch (verifyErr: any) {
                reject(verifyErr);
              }
            },
            modal: {
              ondismiss: () => reject(new Error("Payment cancelled.")),
            },
          });
          RazorpayInstance.open();
        }).catch(reject);
      });

      toast.success("Subscription Activated!", `Upgraded to ${selectedPlanForUpgrade.name} plan.`);
      setSelectedPlanForUpgrade(null);
      fetchData();
    } catch (err: any) {
      if (err.message !== "Payment cancelled.") {
        toast.error("Payment Failed", err.message || "Could not complete transaction.");
      }
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const meters = [
    {
      title: "Connected Social Channels",
      current: usage?.connected_social_accounts ?? 0,
      limit: usage?.limits?.social_account_limit ?? 1,
      icon: Share2,
      color: "bg-indigo-500",
    },
    {
      title: "Posts Published (This Month)",
      current: usage?.posts_published_this_month ?? 0,
      limit: usage?.limits?.monthly_post_limit ?? 30,
      icon: FileText,
      color: "bg-cyan-500",
    },
    {
      title: "AI Tokens Consumed",
      current: usage?.ai_tokens_consumed_this_month ?? 0,
      limit: usage?.limits?.ai_token_limit_monthly ?? 100000,
      icon: Bot,
      color: "bg-purple-500",
    },
    {
      title: "Active Automation Workflows",
      current: usage?.active_workflows ?? 0,
      limit: usage?.limits?.workflow_limit ?? 2,
      icon: Workflow,
      color: "bg-emerald-500",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header with Currency Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <CreditCard className="w-6 h-6 text-indigo-400" /> Plan & Usage Quotas
          </h1>
          <p className="text-xs text-slate-400">
            Track resource consumption, manage invoices, and scale your brand capacity in INR (₹).
          </p>
        </div>

        {/* Currency Switcher */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300">
          <Globe className="w-3.5 h-3.5 text-indigo-400" />
          <select
            value={selectedCurrency}
            onChange={(e) => setSelectedCurrency(e.target.value)}
            className="bg-transparent text-xs font-semibold text-slate-100 focus:outline-none cursor-pointer"
          >
            <option value="INR" className="bg-slate-900 text-slate-100">INR (₹) — Base</option>
            <option value="USD" className="bg-slate-900 text-slate-100">USD ($)</option>
            <option value="EUR" className="bg-slate-900 text-slate-100">EUR (€)</option>
            <option value="GBP" className="bg-slate-900 text-slate-100">GBP (£)</option>
            <option value="AED" className="bg-slate-900 text-slate-100">AED (AED)</option>
            <option value="CAD" className="bg-slate-900 text-slate-100">CAD (CA$)</option>
            <option value="AUD" className="bg-slate-900 text-slate-100">AUD (A$)</option>
            <option value="SGD" className="bg-slate-900 text-slate-100">SGD (S$)</option>
          </select>
        </div>
      </div>

      {/* Active Subscription Summary */}
      <Card glow className="p-6 border-indigo-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <Badge variant="purple" className="text-xs font-bold">
              {subscription?.plan_name || "Free 30-Day Trial"}
            </Badge>
            <Badge variant="success">Active</Badge>
          </div>
          <p className="text-xs text-slate-300">
            Current Billing Cycle: <strong className="capitalize">{subscription?.billing_period || "Monthly"}</strong>
          </p>
          {subscription?.trial_end && (
            <p className="text-[11px] text-amber-400">
              Trial ends on {formatDate(subscription.trial_end)}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="glow"
            onClick={() => {
              const target = plans.find((p) => p.slug === "pro") || plans[1];
              if (target) setSelectedPlanForUpgrade(target);
            }}
          >
            Upgrade Capacity
          </Button>
        </div>
      </Card>

      {/* Real-time Usage Progress Meters */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-200">Real-Time Resource Quotas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {meters.map((meter, idx) => {
            const Icon = meter.icon;
            const pct = Math.min(100, Math.round((meter.current / (meter.limit || 1)) * 100));
            return (
              <Card key={idx} className="p-5 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200 flex items-center gap-2">
                    <Icon className="w-4 h-4 text-indigo-400" /> {meter.title}
                  </span>
                  <span className="font-mono text-slate-400">
                    {meter.current.toLocaleString()} / {meter.limit.toLocaleString()} ({pct}%)
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div className={`h-full rounded-full ${meter.color}`} style={{ width: `${pct}%` }} />
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Available Plans */}
      <div className="space-y-4 pt-4">
        <h3 className="text-sm font-semibold text-slate-200">Available Subscription Tiers</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((p) => {
            const isCurrent = subscription?.plan_id === p.id;
            const rawPrice = billingPeriod === "monthly" ? p.price_monthly : p.price_yearly;
            const formatted = formatPrice(rawPrice);

            return (
              <Card key={p.id} hoverEffect className={`p-6 space-y-4 flex flex-col justify-between ${isCurrent ? "border-indigo-500/50 bg-indigo-950/20" : ""}`}>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-bold text-slate-100">{p.name}</h4>
                    {isCurrent && <Badge variant="purple">Current Plan</Badge>}
                  </div>
                  <p className="text-xs text-slate-400 min-h-[32px]">{p.description}</p>
                  <div className="space-y-0.5">
                    <p className="text-2xl font-extrabold text-slate-100">
                      {p.is_free ? "Free" : formatted} <span className="text-xs text-slate-400 font-normal">/ mo</span>
                    </p>
                    {selectedCurrency !== "INR" && !p.is_free && (
                      <p className="text-[10px] text-slate-500 font-mono">
                        (₹{rawPrice?.toLocaleString("en-IN")})
                      </p>
                    )}
                  </div>
                  <ul className="space-y-2 pt-2 border-t border-slate-800 text-xs text-slate-300">
                    <li className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-indigo-400" />
                      {p.features?.social_account_limit} Social Accounts
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-indigo-400" />
                      {(p.features?.ai_token_limit_monthly ?? 100000).toLocaleString()} AI Tokens
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-indigo-400" />
                      {p.features?.workflow_limit} Visual Workflows
                    </li>
                  </ul>
                </div>

                {!isCurrent && (
                  <Button
                    variant="glow"
                    size="sm"
                    className="w-full"
                    onClick={() => setSelectedPlanForUpgrade(p)}
                  >
                    Select {p.name}
                  </Button>
                )}
              </Card>
            );
          })}
        </div>
      </div>

      {/* Upgrade Checkout Modal */}
      <Modal
        isOpen={!!selectedPlanForUpgrade}
        onClose={() => setSelectedPlanForUpgrade(null)}
        title={`Upgrade to ${selectedPlanForUpgrade?.name}`}
        description="Verify your billing preferences to activate upgraded capacity."
      >
        {selectedPlanForUpgrade && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-200">Plan</span>
                <span className="text-indigo-300 font-bold">{selectedPlanForUpgrade.name}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-200">Total Due</span>
                <span className="text-slate-100 font-extrabold text-sm">
                  ₹{(billingPeriod === "monthly" ? selectedPlanForUpgrade.price_monthly : selectedPlanForUpgrade.price_yearly)?.toLocaleString("en-IN")} INR
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-300">Supported Payment Gateways</label>
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1 text-xs text-slate-300">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold">
                  <ShieldCheck className="w-4 h-4" /> Razorpay & Cashfree Certified (UPI, Cards, NetBanking)
                </div>
                <p className="text-[11px] text-slate-400">
                  Instant webhook confirmation & automated quota expansion.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <Button variant="outline" size="sm" onClick={() => setSelectedPlanForUpgrade(null)}>
                Cancel
              </Button>
              <Button
                variant="glow"
                size="sm"
                onClick={handleRazorpayUpgrade}
                isLoading={isProcessingPayment}
              >
                Confirm & Pay
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
