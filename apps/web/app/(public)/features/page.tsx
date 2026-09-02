"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Workflow,
  Share2,
  Calendar,
  Zap,
  ShieldCheck,
  BarChart3,
  Bot,
  Layers,
  Clock,
  ArrowRight,
  GitBranch,
  Key,
} from "lucide-react";

export default function FeaturesPage() {
  const featureBlocks = [
    {
      title: "AI Studio with Context Memory",
      icon: Bot,
      badge: "Intelligent Generation",
      description:
        "PRAVAH AI doesn't just write generic copy. It analyzes past engagement, brand voice guidelines, industry terminology, and target audience persona to generate authentic posts that convert.",
      bullets: [
        "OpenRouter integration supporting 400+ frontier AI models",
        "Configurable brand tones (Authoritative, Casual, Visionary, Humorous)",
        "Automated hashtag clustering and CTA generation",
        "Token metering and detailed cost observability",
      ],
    },
    {
      title: "Visual DAG Workflow Canvas",
      icon: Workflow,
      badge: "No-Code Automation",
      description:
        "Design complex publishing pipelines without writing code. Connect triggers (manual, schedule, webhook) to AI generation nodes, approval gates, format adaptors, and multi-channel publishing steps.",
      bullets: [
        "React Flow interactive visual node editor",
        "Conditional branching based on content score or sentiment",
        "Step-by-step execution history and node debugging logs",
        "DAG topological execution with cycle prevention",
      ],
    },
    {
      title: "Algorithmic Best-Time Posting Engine",
      icon: Clock,
      badge: "Peak Engagement",
      description:
        "Never guess when your audience is active. PRAVAH analyzes historical post reactions, platform benchmark indices, and timezone distribution to recommend the exact minute for maximum visibility.",
      bullets: [
        "Platform-specific time window optimization (X, LinkedIn, FB, IG)",
        "Confidence score metrics with explainable rationale",
        "Automated one-click scheduling directly from recommendations",
        "Timezone auto-conversion for global teams",
      ],
    },
    {
      title: "Multi-Tenant Enterprise RBAC",
      icon: ShieldCheck,
      badge: "Security & Tenancy",
      description:
        "Total workspace isolation engineered for agencies and conglomerates. Manage multiple distinct brands with 28+ granular permissions, team hierarchies, and cryptographic token security.",
      bullets: [
        "Strict tenant boundary validation preventing IDOR leaks",
        "Custom role creation with granular permission assignment",
        "Time-limited team member invitation tokens",
        "Detailed audit logging for all administrative actions",
      ],
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <Badge variant="purple">Architecture & Capabilities</Badge>
        <h1 className="text-4xl font-extrabold text-slate-100">
          The Full Stack of Modern Social Intelligence
        </h1>
        <p className="text-xs sm:text-sm text-slate-400">
          Every tool, engine, and security layer engineered from first principles for mission-critical SaaS operations.
        </p>
      </div>

      <div className="space-y-12">
        {featureBlocks.map((block, idx) => {
          const Icon = block.icon;
          const isEven = idx % 2 === 0;
          return (
            <div
              key={idx}
              className={`grid grid-cols-1 lg:grid-cols-2 gap-8 items-center ${
                !isEven ? "lg:flex-row-reverse" : ""
              }`}
            >
              <div className="space-y-4">
                <Badge variant="info">{block.badge}</Badge>
                <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
                  <Icon className="w-6 h-6 text-indigo-400" /> {block.title}
                </h2>
                <p className="text-xs text-slate-300 leading-relaxed">{block.description}</p>
                <ul className="space-y-2 text-xs text-slate-400">
                  {block.bullets.map((b, bIdx) => (
                    <li key={bIdx} className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                      {b}
                    </li>
                  ))}
                </ul>
              </div>

              <Card glow className="p-6 bg-slate-900/60 border-slate-800">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                  <span className="text-xs font-mono text-indigo-400">{block.title}</span>
                  <span className="text-[11px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                    Live Engine
                  </span>
                </div>
                <div className="space-y-3 font-mono text-[11px] text-slate-400 bg-slate-950 p-4 rounded-xl border border-slate-800/80">
                  <p className="text-slate-200">// PRAVAH Orchestration Layer</p>
                  <p className="text-indigo-300">status: &apos;ACTIVE&apos;</p>
                  <p className="text-cyan-300">encryption: &apos;AES-256-Fernet&apos;</p>
                  <p className="text-emerald-300">sla_target: &apos;99.95%&apos;</p>
                  <p className="text-slate-500">// Ready for automated trigger</p>
                </div>
              </Card>
            </div>
          );
        })}
      </div>

      <div className="text-center pt-8">
        <Link href="/register">
          <Button variant="glow" size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
            Experience PRAVAH Features Free
          </Button>
        </Link>
      </div>
    </div>
  );
}
