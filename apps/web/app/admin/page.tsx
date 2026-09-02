"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import {
  Users,
  Building,
  CreditCard,
  Share2,
  Workflow,
  Bot,
  AlertOctagon,
  TrendingUp,
  ShieldCheck,
} from "lucide-react";

export default function AdminOverviewPage() {
  const toast = useToast();
  const [metrics, setMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTogglingEmergency, setIsTogglingEmergency] = useState(false);

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const data = await fetchApi<any>("/admin/metrics");
      setMetrics(data);
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleEmergencyStop = async (pause: boolean) => {
    setIsTogglingEmergency(true);
    try {
      await fetchApi(`/admin/emergency-stop?pause_all=${pause}`, { method: "POST" });
      toast.success(
        pause ? "Emergency Pause Enabled" : "Publishing Resumed",
        `Global social publishing is now ${pause ? "PAUSED" : "ACTIVE"}.`
      );
      fetchMetrics();
    } catch (err: any) {
      toast.error("Action Failed", err.message || "Failed to update emergency control.");
    } finally {
      setIsTogglingEmergency(false);
    }
  };

  const cards = [
    { title: "Total Users", value: metrics?.total_users ?? 0, icon: Users, color: "text-indigo-400" },
    { title: "Active Workspaces", value: metrics?.total_organisations ?? 0, icon: Building, color: "text-cyan-400" },
    { title: "Active Subscriptions", value: metrics?.active_subscriptions ?? 0, icon: CreditCard, color: "text-emerald-400" },
    { title: "Total Platform Revenue", value: `$${metrics?.total_revenue_usd ?? 0}`, icon: TrendingUp, color: "text-purple-400" },
    { title: "Published Posts", value: metrics?.total_published_posts ?? 0, icon: Share2, color: "text-indigo-400" },
    { title: "Workflow Executions", value: metrics?.total_workflow_executions ?? 0, icon: Workflow, color: "text-cyan-400" },
    { title: "AI Tokens Metered", value: (metrics?.total_ai_tokens_consumed ?? 0).toLocaleString(), icon: Bot, color: "text-purple-400" },
    { title: "Platform Health", value: "100% SLA", icon: ShieldCheck, color: "text-emerald-400" },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100">Super Administrator Metrics</h1>
          <p className="text-xs text-slate-400">Platform-wide telemetry, subscriptions, and emergency governance.</p>
        </div>
      </div>

      {/* Global Emergency Stop Control */}
      <Card className="p-6 border-rose-500/40 bg-rose-950/10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center">
              <AlertOctagon className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Global Emergency Stop Control</h3>
              <p className="text-xs text-slate-400">
                Immediately halt all automated background publishing across all tenant workspaces.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="danger"
              size="sm"
              onClick={() => handleEmergencyStop(true)}
              isLoading={isTogglingEmergency}
            >
              Halt All Publishing
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleEmergencyStop(false)}
              isLoading={isTogglingEmergency}
            >
              Resume Publishing
            </Button>
          </div>
        </div>
      </Card>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((c, idx) => {
          const Icon = c.icon;
          return (
            <Card key={idx} hoverEffect className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">{c.title}</span>
                <Icon className={`w-4 h-4 ${c.color}`} />
              </div>
              <div className="text-2xl font-extrabold text-slate-100">{c.value}</div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
