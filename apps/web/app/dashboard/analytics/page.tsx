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
  FileText,
  Eye,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";

interface AnalyticsSummary {
  period_days: number;
  empty_state: boolean;
  published_this_period: number;
  failed_this_period: number;
  all_time_published: number;
  drafts_pending: number;
  connected_accounts: number;
  platform_breakdown: { platform: string; posts: number }[];
  note: string;
}

export default function AnalyticsPage() {
  const { activeOrg } = useOrganisation();
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (!activeOrg) return;
    setIsLoading(true);
    fetchApi<AnalyticsSummary>(`/analytics/summary?days=${days}`)
      .then((data) => setSummary(data))
      .catch(() => setSummary(null))
      .finally(() => setIsLoading(false));
  }, [activeOrg, days]);

  const maxPosts = summary?.platform_breakdown?.reduce(
    (max, p) => Math.max(max, p.posts),
    1
  ) ?? 1;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <BarChart3 className="w-6 h-6 text-indigo-400" /> Analytics & Publishing Insights
          </h1>
          <p className="text-xs text-slate-400">
            Real data from your published content and connected social channels.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                days === d
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : summary?.empty_state ? (
        /* Empty State — No fake data shown */
        <Card className="py-16 flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center">
            <BarChart3 className="w-7 h-7 text-slate-500" />
          </div>
          <div className="space-y-1.5">
            <h3 className="text-base font-semibold text-slate-200">No Analytics Data Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm">
              {summary?.note || "Connect social accounts and publish your first post to start seeing real analytics here."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 justify-center pt-2">
            <Badge variant="purple">Connect Social Accounts</Badge>
            <Badge variant="purple">Create Content</Badge>
            <Badge variant="purple">Publish Posts</Badge>
          </div>
        </Card>
      ) : (
        <>
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card hoverEffect className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Published ({days}d)</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-extrabold text-slate-100">{summary?.published_this_period ?? 0}</p>
            </Card>
            <Card hoverEffect className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Failed ({days}d)</span>
                <XCircle className="w-4 h-4 text-rose-400" />
              </div>
              <p className="text-2xl font-extrabold text-slate-100">{summary?.failed_this_period ?? 0}</p>
            </Card>
            <Card hoverEffect className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>All-Time Published</span>
                <FileText className="w-4 h-4 text-indigo-400" />
              </div>
              <p className="text-2xl font-extrabold text-slate-100">{summary?.all_time_published ?? 0}</p>
            </Card>
            <Card hoverEffect className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Connected Accounts</span>
                <Share2 className="w-4 h-4 text-cyan-400" />
              </div>
              <p className="text-2xl font-extrabold text-slate-100">{summary?.connected_accounts ?? 0}</p>
            </Card>
          </div>

          {/* Platform Breakdown */}
          <Card className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-800 pb-3">
              Publishing Volume by Channel (Last {days} Days)
            </h3>
            {!summary?.platform_breakdown?.length ? (
              <p className="text-xs text-slate-500 py-4 text-center">
                No published posts in this period.
              </p>
            ) : (
              <div className="space-y-3 pt-2">
                {summary.platform_breakdown.map((c) => (
                  <div key={c.platform} className="space-y-1.5">
                    <div className="flex justify-between text-xs text-slate-300 items-center">
                      <span className="font-medium flex items-center gap-2">
                        <SocialIcon platform={c.platform} className="w-4 h-4" />
                        {c.platform.charAt(0).toUpperCase() + c.platform.slice(1)}
                      </span>
                      <span className="text-slate-400">{c.posts} post{c.posts !== 1 ? "s" : ""} published</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-indigo-500 transition-all"
                        style={{ width: `${Math.round((c.posts / maxPosts) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Info note */}
          {summary?.note && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <p>{summary.note}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
