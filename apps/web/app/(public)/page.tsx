"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchApi } from "@/lib/api";
import { Plan } from "@pravah/shared-types";
import {
  Sparkles,
  ArrowRight,
  Workflow,
  Share2,
  Calendar,
  Zap,
  ShieldCheck,
  BarChart3,
  Bot,
  Layers,
  Clock,
  Check,
  CheckCircle2,
  ChevronDown,
  Globe,
} from "lucide-react";

export default function HomePage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  useEffect(() => {
    fetchApi<Plan[]>("/billing/plans")
      .then((data) => setPlans(data))
      .catch(() => {});
  }, []);

  const faqs = [
    {
      q: "What makes PRAVAH different from legacy scheduling tools?",
      a: "PRAVAH integrates deep AI brand voice intelligence with a full drag-and-drop Visual Workflow DAG engine. It doesn't just queue posts—it can dynamically research topics, generate platform-optimized creatives, route for multi-tier team approvals, and dispatch at algorithmic peak times automatically.",
    },
    {
      q: "Which social media networks are supported?",
      a: "We provide official OAuth integration and direct publishing for X (Twitter), Facebook Pages & Groups, Instagram Business, LinkedIn Profiles & Company Pages, and YouTube Community/Videos.",
    },
    {
      q: "Can I connect custom AI models or OpenRouter API keys?",
      a: "Yes! PRAVAH natively integrates OpenRouter, giving you access to 400+ frontier AI models (Claude 3.5, GPT-4o, Llama 3, Gemini 1.5) plus support for custom private LLM endpoints.",
    },
    {
      q: "Is there a free trial?",
      a: "Yes! Every new account gets an immediate 30-day Free Trial with 1 connected account, full AI studio access, and workflow automations—no credit card required.",
    },
    {
      q: "Are credentials and access tokens secure?",
      a: "All third-party OAuth access tokens and API keys are protected using AES-256 Fernet encryption at rest, coupled with strict tenant isolation and RBAC controls.",
    },
  ];

  return (
    <div className="space-y-24 pb-20 overflow-hidden">
      {/* Hero Section */}
      <section className="relative pt-20 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        {/* Glow backdrop */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-indigo-600/15 blur-[140px] pointer-events-none rounded-full" />

        <div className="relative z-10 space-y-6 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Next-Gen AI Social Media Operating System
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-100 tracking-tight leading-[1.15]">
            Unleash the Flow of{" "}
            <span className="text-gradient-vibrant">Autonomous Content</span> & Intelligent Workflows
          </h1>

          <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            PRAVAH combines multi-tenant brand intelligence, visual no-code DAG automation, and official API publishing into a single unified platform.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link href="/register">
              <Button variant="glow" size="lg" className="w-full sm:w-auto" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Start 30-Day Free Trial
              </Button>
            </Link>
            <Link href="/features">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto" leftIcon={<Workflow className="w-4 h-4 text-indigo-400" />}>
                Explore Visual Workflows
              </Button>
            </Link>
          </div>

          <div className="pt-6 flex items-center justify-center gap-8 text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> No credit card required</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> 5-minute setup</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-emerald-400" /> Official OAuth 2.0</span>
          </div>
        </div>

        {/* Hero Interactive App Showcase Preview */}
        <div className="mt-14 relative max-w-5xl mx-auto">
          <div className="relative rounded-2xl border border-slate-700/60 bg-slate-900/80 backdrop-blur-xl p-4 sm:p-6 shadow-2xl shadow-indigo-950/40">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="text-xs text-slate-400 ml-2 font-mono">pravah://dashboard/ai-studio</span>
              </div>
              <Badge variant="purple">AI Flow Active</Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
              <div className="glass-panel rounded-xl p-4 space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
                  <Bot className="w-4 h-4" /> 1. Brand Intelligence
                </div>
                <p className="text-xs text-slate-300">
                  Analyzing past top-performing posts & brand tone guidelines.
                </p>
                <div className="text-[11px] font-mono bg-slate-950/60 p-2.5 rounded-lg text-slate-400 border border-slate-800">
                  Tone: Authoritative & Visionary<br />
                  Target Audience: SaaS Founders
                </div>
              </div>

              <div className="glass-panel rounded-xl p-4 space-y-3 border-indigo-500/40 shadow-md shadow-indigo-500/10">
                <div className="flex items-center gap-2 text-xs font-semibold text-cyan-400">
                  <Workflow className="w-4 h-4" /> 2. Visual DAG Trigger
                </div>
                <p className="text-xs text-slate-300">
                  Executing condition nodes & multi-format image rendering.
                </p>
                <div className="text-[11px] font-mono bg-slate-950/60 p-2.5 rounded-lg text-slate-400 border border-slate-800">
                  Node 1: OpenRouter AI text<br />
                  Node 2: Photorealistic Banner<br />
                  Node 3: Approval Dispatch
                </div>
              </div>

              <div className="glass-panel rounded-xl p-4 space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                  <Clock className="w-4 h-4" /> 3. Best Time Publishing
                </div>
                <p className="text-xs text-slate-300">
                  Scheduled for optimal peak engagement window.
                </p>
                <div className="text-[11px] font-mono bg-slate-950/60 p-2.5 rounded-lg text-emerald-300 border border-emerald-950/40">
                  Platform: X & LinkedIn<br />
                  Time: Tuesday, 09:30 AM (98% peak)
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Pillar Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="info">Engineered for Scale</Badge>
          <h2 className="text-3xl font-bold text-slate-100">Everything Needed to Dominate Social</h2>
          <p className="text-xs text-slate-400">
            From single creators to enterprise agencies running dozens of brands.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Bot className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">AI Studio with Brand Voice</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Generate platform-tailored copy, hashtags, CTAs, and photorealistic visual assets with full brand persona memory and token metering.
            </p>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
              <Workflow className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">Visual No-Code DAG Builder</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Build custom automated pipelines with triggers, conditional logic, AI generation, and multi-channel publishing on a visual React Flow canvas.
            </p>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
              <Calendar className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">Smart Calendar & Best Time</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Schedule content with drag-and-drop ease, approval workflow gates, and algorithmic recommendations based on historical engagement patterns.
            </p>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Share2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">Official Social API Connect</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Direct OAuth 2.0 connection to X, Facebook, Instagram, LinkedIn, and YouTube with token encryption and automated token refresh handling.
            </p>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center">
              <Layers className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">Multi-Tenant RBAC & Teams</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Manage multiple independent brand workspaces with granular 28+ permissions, custom roles, invitation tokens, and strict tenant boundaries.
            </p>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">Real-Time Analytics & Quotas</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track post reach, engagement metrics, token consumption, and subscription usage meters with Razorpay & Cashfree billing integrations.
            </p>
          </Card>
        </div>
      </section>

      {/* Dynamic Pricing Section */}
      <section id="pricing" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <Badge variant="purple">Transparent Pricing</Badge>
          <h2 className="text-3xl font-bold text-slate-100">Start Free. Upgrade As You Scale.</h2>
          <p className="text-xs text-slate-400">
            Every plan includes our core visual automation engine and official social integrations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((p) => {
            const isStarter = p.slug === "starter";
            return (
              <Card
                key={p.id}
                hoverEffect
                className={`relative flex flex-col justify-between p-8 space-y-6 ${
                  isStarter ? "border-indigo-500/50 shadow-xl shadow-indigo-500/10 bg-slate-900/90" : ""
                }`}
              >
                {isStarter && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-indigo-500 to-cyan-500 text-white text-[11px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider">
                    Most Popular
                  </div>
                )}

                <div className="space-y-4">
                  <h3 className="text-xl font-bold text-slate-100">{p.name}</h3>
                  <p className="text-xs text-slate-400">{p.description}</p>
                  <div className="flex items-baseline gap-1 pt-2">
                    <span className="text-3xl font-extrabold text-slate-100">
                      {p.is_free ? "₹0" : `₹${p.price_monthly?.toLocaleString("en-IN")}`}
                    </span>
                    <span className="text-xs text-slate-400">/ month</span>
                  </div>

                  <ul className="space-y-2.5 pt-4 text-xs text-slate-300 border-t border-slate-800">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                      {p.features?.social_account_limit} Connected Social Accounts
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                      {p.features?.monthly_post_limit === 999999 ? "Unlimited" : p.features?.monthly_post_limit} Posts / month
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                      {(p.features?.ai_token_limit_monthly ?? 100000).toLocaleString()} AI Tokens / month
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                      {p.features?.workflow_limit} Active Visual Workflows
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-indigo-400 shrink-0" />
                      {p.features?.member_limit} Team Members
                    </li>
                  </ul>
                </div>

                <Link href="/register">
                  <Button variant={isStarter ? "glow" : "outline"} className="w-full">
                    {p.is_free ? "Get Started Free" : "Upgrade to " + p.name}
                  </Button>
                </Link>
              </Card>
            );
          })}
        </div>
      </section>

      {/* FAQ Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="text-center space-y-3">
          <Badge variant="default">Got Questions?</Badge>
          <h2 className="text-3xl font-bold text-slate-100">Frequently Asked Questions</h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div
                key={idx}
                className="glass-panel rounded-xl p-4 cursor-pointer transition-colors hover:border-slate-700"
                onClick={() => setOpenFaq(isOpen ? null : idx)}
              >
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-slate-200">{faq.q}</h4>
                  <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                </div>
                {isOpen && <p className="text-xs text-slate-400 mt-3 leading-relaxed border-t border-slate-800 pt-3">{faq.a}</p>}
              </div>
            );
          })}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="glass-panel rounded-3xl p-8 sm:p-14 text-center relative overflow-hidden border-indigo-500/30">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/10 via-purple-600/10 to-cyan-600/10 pointer-events-none" />
          <div className="relative z-10 space-y-4 max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-slate-100">
              Ready to automate your social media empire?
            </h2>
            <p className="text-xs text-slate-300">
              Join thousands of growth teams deploying high-converting content with PRAVAH.
            </p>
            <div className="pt-4">
              <Link href="/register">
                <Button variant="glow" size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Start Your 30-Day Free Trial
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
