"use client";

import React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Calendar, User } from "lucide-react";

export default function BlogPage() {
  const articles = [
    {
      title: "How to Build Self-Optimizing Social Automation with Visual DAG Workflows",
      slug: "visual-dag-workflows-social-automation",
      category: "Engineering",
      date: "September 2026",
      author: "Pravah Research Team",
      summary:
        "An in-depth look at implementing topological sorting, cycle detection, and idempotent node state machines in distributed social publishing pipelines.",
    },
    {
      title: "Brand Voice Intelligence: Fine-Tuning LLM Prompts on Historical Engagement",
      slug: "brand-voice-intelligence-llms",
      category: "AI & ML",
      date: "August 2026",
      author: "AI Systems Group",
      summary:
        "Why generic prompting fails at social distribution, and how dynamic few-shot injection with brand persona guidelines yields 3.4x higher engagement.",
    },
    {
      title: "The Architecture of Multi-Tenant Security in Modern SaaS",
      slug: "multi-tenant-security-architecture",
      category: "Security",
      date: "August 2026",
      author: "Platform Security",
      summary:
        "Protecting user secrets, OAuth access tokens, and organisation boundaries using AES-256 encryption at rest and strict tenant context middleware.",
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-12">
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <Badge variant="info">Engineering & Insights</Badge>
        <h1 className="text-4xl font-extrabold text-slate-100">The PRAVAH Journal</h1>
        <p className="text-xs sm:text-sm text-slate-400">
          Deep dives into AI orchestration, distributed scheduling architectures, and growth automation engineering.
        </p>
      </div>

      <div className="space-y-6">
        {articles.map((art, idx) => (
          <Card key={idx} hoverEffect className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge variant="purple">{art.category}</Badge>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> {art.date}</span>
                <span className="flex items-center gap-1.5"><User className="w-3.5 h-3.5" /> {art.author}</span>
              </div>
            </div>

            <h2 className="text-xl font-bold text-slate-100 hover:text-indigo-400 transition-colors cursor-pointer">
              {art.title}
            </h2>

            <p className="text-xs text-slate-300 leading-relaxed">{art.summary}</p>

            <div className="pt-2">
              <span className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer">
                Read Deep Dive <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
