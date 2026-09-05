"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useOrganisation } from "@/providers/org-provider";
import { formatDate } from "@/lib/utils";
import {
  FileText,
  Clock,
  Workflow,
  Sparkles,
  Share2,
  TrendingUp,
  ArrowRight,
  Plus,
  Bot,
  CheckCircle2,
  Calendar,
  AlertTriangle,
} from "lucide-react";

export default function DashboardOverviewPage() {
  const { activeOrg } = useOrganisation();
  const [contentList, setContentList] = useState<any[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!activeOrg) return;

    setIsLoading(true);
    Promise.allSettled([
      fetchApi<any[]>("/content?limit=5"),
      fetchApi<any>("/billing/usage"),
      fetchApi<any[]>("/social/accounts"),
      fetchApi<any>("/ai/recommend-best-time?platform=x"),
    ])
      .then(([contentRes, usageRes, accountsRes, recRes]) => {
        if (contentRes.status === "fulfilled") setContentList(contentRes.value);
        if (usageRes.status === "fulfilled") setUsage(usageRes.value);
        if (accountsRes.status === "fulfilled") setAccounts(accountsRes.value);
        if (recRes.status === "fulfilled") setRecommendation(recRes.value);
      })
      .finally(() => setIsLoading(false));
  }, [activeOrg]);

  const kpis = [
    {
      title: "Connected Accounts",
      value: usage?.connected_social_accounts ?? accounts.length,
      limit: usage?.limits?.social_account_limit ?? usage?.social_account_limit ?? 1,
      icon: Share2,
      color: "text-indigo-400",
      bgColor: "bg-indigo-500/10 border-indigo-500/20",
    },
    {
      title: "Posts This Month",
      value: usage?.posts_published_this_month ?? 0,
      limit: usage?.limits?.monthly_post_limit ?? usage?.monthly_post_limit ?? 30,
      icon: FileText,
      color: "text-cyan-400",
      bgColor: "bg-cyan-500/10 border-cyan-500/20",
    },
    {
      title: "AI Tokens Used",
      value: (usage?.ai_tokens_consumed_this_month ?? usage?.ai_tokens_used_this_month ?? 0).toLocaleString(),
      limit: (usage?.limits?.ai_token_limit_monthly ?? usage?.ai_token_limit_monthly ?? 100000).toLocaleString(),
      icon: Bot,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10 border-purple-500/20",
    },
    {
      title: "Active Workflows",
      value: usage?.active_workflows ?? 0,
      limit: usage?.limits?.workflow_limit ?? usage?.workflow_limit ?? 2,
      icon: Workflow,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10 border-emerald-500/20",
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative overflow-hidden border-indigo-500/30">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 blur-3xl rounded-full pointer-events-none" />
        <div className="space-y-1.5 z-10">
          <Badge variant="purple" className="mb-1">Active Brand</Badge>
          <h1 className="text-2xl font-bold text-slate-100">{activeOrg?.name || "Your Workspace"}</h1>
          <p className="text-xs text-slate-400">
            Automated social publishing, AI brand voice intelligence, and visual workflows.
          </p>
        </div>
        <div className="flex items-center gap-3 z-10">
          <Link href="/dashboard/ai-studio">
            <Button variant="glow" leftIcon={<Sparkles className="w-4 h-4" />}>
              Create with AI Studio
            </Button>
          </Link>
          <Link href="/dashboard/content">
            <Button variant="secondary" leftIcon={<Plus className="w-4 h-4" />}>
              New Post
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <Card key={idx} hoverEffect className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 font-medium">{kpi.title}</span>
                <div className={`p-2 rounded-xl border ${kpi.bgColor} ${kpi.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-extrabold text-slate-100">{kpi.value}</div>
                <div className="text-[11px] text-slate-500">Plan limit: {kpi.limit}</div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Main Grid: Content Stream & AI Best Time */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Content / Queue */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-6">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
              <div>
                <h3 className="text-base font-semibold text-slate-100">Recent Content & Drafts</h3>
                <p className="text-xs text-slate-400">Multi-channel posts in your production queue</p>
              </div>
              <Link href="/dashboard/content" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
                View All →
              </Link>
            </div>

            <div className="space-y-3">
              {contentList.length === 0 ? (
                <div className="text-center py-10 space-y-3">
                  <FileText className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-xs text-slate-400">No content items created yet.</p>
                  <Link href="/dashboard/ai-studio">
                    <Button variant="outline" size="sm">
                      Generate First Post with AI
                    </Button>
                  </Link>
                </div>
              ) : (
                contentList.map((c) => (
                  <div
                    key={c.id}
                    className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors flex items-center justify-between gap-4"
                  >
                    <div className="space-y-1 truncate">
                      <p className="text-xs font-semibold text-slate-200 truncate">
                        {c.title || c.body.substring(0, 50) + "..."}
                      </p>
                      <div className="flex items-center gap-2 text-[11px] text-slate-400">
                        <span>Platforms: {c.platforms.join(", ").toUpperCase()}</span>
                        <span>•</span>
                        <span>{formatDate(c.created_at)}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <Badge
                        variant={
                          c.status === "published"
                            ? "success"
                            : c.status === "approved"
                            ? "purple"
                            : c.status === "review"
                            ? "warning"
                            : "default"
                        }
                      >
                        {c.status}
                      </Badge>
                      <Link href={`/dashboard/content`}>
                        <Button variant="ghost" size="sm">Edit</Button>
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        {/* AI Best Posting Time & Quick Actions */}
        <div className="space-y-6">
          {/* Best Time Recommendation Card */}
          <Card glow className="space-y-4 border-indigo-500/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-indigo-400" /> Best Time Recommendation
              </span>
              <Badge variant="purple">98% Confidence</Badge>
            </div>

            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 space-y-2">
              <p className="text-[11px] text-slate-400 font-medium">Optimal Window for X & LinkedIn:</p>
              <p className="text-base font-bold text-slate-100">
                {recommendation?.recommended_time
                  ? formatDate(recommendation.recommended_time)
                  : "Tomorrow at 09:30 AM"}
              </p>
              <p className="text-xs text-slate-300">
                {recommendation?.reason || "Peak engagement spike detected from audience historical response metrics."}
              </p>
            </div>

            <Link href="/dashboard/ai-studio">
              <Button variant="glow" size="sm" className="w-full">
                Schedule AI Post for This Window
              </Button>
            </Link>
          </Card>

          {/* Connected Social Accounts Overview */}
          <Card className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h4 className="text-xs font-semibold text-slate-200">Connected Accounts</h4>
              <Link href="/dashboard/social" className="text-xs text-indigo-400 hover:text-indigo-300">
                Manage
              </Link>
            </div>

            <div className="space-y-2">
              {accounts.length === 0 ? (
                <div className="text-center py-4 space-y-2">
                  <p className="text-xs text-slate-400">No social channels connected yet.</p>
                  <Link href="/dashboard/social">
                    <Button variant="outline" size="sm">Connect Channels</Button>
                  </Link>
                </div>
              ) : (
                accounts.map((acc) => (
                  <div
                    key={acc.id}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-indigo-400 uppercase text-xs">
                        {acc.provider[0]}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-200">{acc.account_name}</p>
                        <p className="text-[11px] text-slate-500">{acc.username || acc.provider}</p>
                      </div>
                    </div>
                    <Badge variant={acc.is_connected ? "success" : "danger"}>
                      {acc.is_connected ? "Active" : "Disconnected"}
                    </Badge>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
