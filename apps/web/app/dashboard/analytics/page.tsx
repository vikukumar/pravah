"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SocialIcon } from "@/components/ui/social-icon";
import { useOrganisation } from "@/providers/org-provider";
import {
  BarChart3,
  TrendingUp,
  Share2,
  Users,
  Eye,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";

export default function AnalyticsPage() {
  const { activeOrg } = useOrganisation();
  const [usage, setUsage] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<any>(null);

  useEffect(() => {
    if (!activeOrg) return;

    fetchApi<any>("/billing/usage")
      .then((data) => setUsage(data))
      .catch(() => {});

    fetchApi<any>("/ai/recommend-best-time?platform=x")
      .then((data) => setRecommendation(data))
      .catch(() => {});
  }, [activeOrg]);

  const metrics = [
    { label: "Total Impressions", value: "148,290", change: "+24.8%", icon: Eye, color: "text-indigo-400" },
    { label: "Audience Growth", value: "3,480", change: "+18.2%", icon: Users, color: "text-cyan-400" },
    { label: "Total Shares / Reposts", value: "1,940", change: "+32.1%", icon: Share2, color: "text-purple-400" },
    { label: "Engagement Rate", value: "4.82%", change: "+1.2%", icon: TrendingUp, color: "text-emerald-400" },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
          <BarChart3 className="w-6 h-6 text-indigo-400" /> Analytics & Intelligence ROI
        </h1>
        <p className="text-xs text-slate-400">
          Monitor multi-channel impressions, engagement velocity, and automated pipeline yield.
        </p>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <Card key={idx} hoverEffect className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>{m.label}</span>
                <Icon className={`w-4 h-4 ${m.color}`} />
              </div>
              <div className="flex items-baseline justify-between pt-1">
                <span className="text-2xl font-extrabold text-slate-100">{m.value}</span>
                <span className="text-xs text-emerald-400 flex items-center font-semibold">
                  <ArrowUpRight className="w-3.5 h-3.5" /> {m.change}
                </span>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Channel Breakdown & AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-800 pb-3">
            Publishing Volume by Channel (Last 30 Days)
          </h3>
          <div className="space-y-3 pt-2">
            {[
              { id: "x", channel: "X (Twitter)", posts: 42, pct: 85, color: "bg-cyan-500" },
              { id: "linkedin", channel: "LinkedIn", posts: 28, pct: 60, color: "bg-indigo-500" },
              { id: "facebook", channel: "Facebook Pages", posts: 19, pct: 40, color: "bg-blue-500" },
              { id: "instagram", channel: "Instagram", posts: 15, pct: 30, color: "bg-rose-500" },
              { id: "youtube", channel: "YouTube", posts: 8, pct: 20, color: "bg-red-500" },
            ].map((c) => (
              <div key={c.channel} className="space-y-1.5">
                <div className="flex justify-between text-xs text-slate-300 items-center">
                  <span className="font-medium flex items-center gap-2">
                    <SocialIcon platform={c.id} className="w-4 h-4" />
                    {c.channel}
                  </span>
                  <span className="text-slate-400">{c.posts} posts published</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div className={`h-full rounded-full ${c.color}`} style={{ width: `${c.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* AI Insight Card */}
        <Card glow className="space-y-4 border-indigo-500/30">
          <div className="flex items-center gap-2 text-xs font-semibold text-indigo-300">
            <Sparkles className="w-4 h-4 text-indigo-400" /> AI Optimization Insight
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Posts published with <strong>authoritative</strong> tone on Tuesdays and Thursdays at 09:30 AM generate <strong>3.2x</strong> more reposts and comments compared to weekend slots.
          </p>
          <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-300">
            Next recommendation: Schedule 2 thought leadership pieces on LinkedIn before Thursday.
          </div>
        </Card>
      </div>
    </div>
  );
}
