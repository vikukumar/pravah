"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plan } from "@pravah/shared-types";
import { Check, ArrowRight, Globe, RefreshCw } from "lucide-react";

export default function PricingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [selectedCurrency, setSelectedCurrency] = useState<string>("INR");
  const [exchangeRates, setExchangeRates] = useState<Record<string, number>>({ INR: 1.0, USD: 0.0119, EUR: 0.0111, GBP: 0.0094 });
  const [currencySymbols, setCurrencySymbols] = useState<Record<string, string>>({ INR: "₹", USD: "$", EUR: "€", GBP: "£" });
  const [isLoadingRates, setIsLoadingRates] = useState(false);

  useEffect(() => {
    fetchApi<Plan[]>("/billing/plans")
      .then((data) => setPlans(data))
      .catch(() => {});

    setIsLoadingRates(true);
    fetchApi<any>("/billing/exchange-rates")
      .then((res) => {
        if (res.rates) setExchangeRates(res.rates);
        if (res.symbols) setCurrencySymbols(res.symbols);
      })
      .catch(() => {})
      .finally(() => setIsLoadingRates(false));
  }, []);

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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      <div className="text-center space-y-4 max-w-2xl mx-auto">
        <Badge variant="purple">Simple & Predictable</Badge>
        <h1 className="text-4xl font-extrabold text-slate-100">Plans for Teams of All Sizes</h1>
        <p className="text-xs sm:text-sm text-slate-400">
          Base pricing in Indian Rupee (INR ₹) with real-time currency conversion for global teams.
        </p>

        {/* Controls Bar: Billing cycle & Currency */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          {/* Billing cycle toggle */}
          <div className="inline-flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setBillingCycle("monthly")}
              className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                billingCycle === "monthly" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle("yearly")}
              className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                billingCycle === "yearly" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Yearly <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded">Save 20%</span>
            </button>
          </div>

          {/* Currency Switcher */}
          <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300">
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
              <option value="JPY" className="bg-slate-900 text-slate-100">JPY (¥)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((p) => {
          const rawPrice = billingCycle === "monthly" ? p.price_monthly : p.price_yearly;
          const isPro = p.slug === "pro";
          const formattedPrice = formatPrice(rawPrice);

          return (
            <Card
              key={p.id}
              hoverEffect
              className={`p-6 space-y-6 flex flex-col justify-between ${
                isPro ? "border-indigo-500/50 bg-indigo-950/20 shadow-xl shadow-indigo-600/10" : ""
              }`}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-slate-100">{p.name}</h3>
                  {isPro && <Badge variant="purple">Most Popular</Badge>}
                </div>
                <p className="text-xs text-slate-400 min-h-[32px]">{p.description}</p>
                <div className="space-y-1">
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold text-slate-100">
                      {p.is_free ? "Free" : formattedPrice}
                    </span>
                    {!p.is_free && (
                      <span className="text-xs text-slate-400">
                        {billingCycle === "monthly" ? "/ mo" : "/ yr"}
                      </span>
                    )}
                  </div>
                  {selectedCurrency !== "INR" && !p.is_free && (
                    <p className="text-[10px] text-slate-500 font-mono">
                      (Base: ₹{rawPrice?.toLocaleString("en-IN")})
                    </p>
                  )}
                </div>

                <ul className="space-y-2.5 pt-4 border-t border-slate-800 text-xs text-slate-300">
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                    {p.features?.social_account_limit} Connected Social Profiles
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                    {p.features?.monthly_post_limit} Posts / month
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                    {(p.features?.ai_token_limit_monthly ?? 100000).toLocaleString()} AI Tokens / mo
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                    {p.features?.workflow_limit} Automation Workflows
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                    {p.features?.member_limit} Team Member seat{p.features?.member_limit === 1 ? "" : "s"}
                  </li>
                </ul>
              </div>

              <Link href="/register" className="block pt-4">
                <Button
                  variant={isPro ? "glow" : "outline"}
                  className="w-full"
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  {p.is_free ? "Start 30-Day Trial" : `Choose ${p.name}`}
                </Button>
              </Link>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
