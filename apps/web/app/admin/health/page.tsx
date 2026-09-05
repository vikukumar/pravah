"use client";
import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { Activity, CheckCircle, AlertTriangle, XCircle, RefreshCw, Database, Cpu, Zap, Clock } from "lucide-react";

interface ServiceHealth { status: string; latency_ms?: number; note?: string; error?: string; active_executions?: number; }
interface HealthData { status: string; checked_at: string; services: Record<string, ServiceHealth>; platform: { total_users: number; total_orgs: number }; config: Record<string, boolean>; }

const STATUS_CONFIG = {
  ok:          { color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20", icon: CheckCircle, label: "Healthy" },
  unavailable: { color: "text-amber-400",   bg: "bg-amber-500/10 border-amber-500/20",   icon: AlertTriangle, label: "Unavailable" },
  error:       { color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20",       icon: XCircle, label: "Error" },
  unknown:     { color: "text-slate-400",   bg: "bg-slate-800 border-slate-700",         icon: AlertTriangle, label: "Unknown" },
};

const SERVICE_ICONS: Record<string, React.ElementType> = { database: Database, redis: Zap, workflow_engine: Cpu };

function ServiceCard({ name, service }: { name: string; service: ServiceHealth }) {
  const cfg = STATUS_CONFIG[service.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.unknown;
  const Icon = SERVICE_ICONS[name] || Activity;
  const StatusIcon = cfg.icon;
  return (
    <Card className={`p-4 border ${cfg.bg}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-semibold text-white capitalize">{name.replace("_", " ")}</span>
        </div>
        <div className={`flex items-center gap-1.5 ${cfg.color}`}>
          <StatusIcon className="w-3.5 h-3.5" />
          <span className="text-xs font-medium">{cfg.label}</span>
        </div>
      </div>
      <div className="space-y-1">
        {service.latency_ms !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-500">Latency</span>
            <span className={`text-[11px] font-mono font-bold ${service.latency_ms < 10 ? "text-emerald-400" : service.latency_ms < 50 ? "text-amber-400" : "text-red-400"}`}>{service.latency_ms}ms</span>
          </div>
        )}
        {service.active_executions !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-slate-500">Active Runs</span>
            <span className="text-[11px] font-mono text-slate-300">{service.active_executions}</span>
          </div>
        )}
        {service.note && <p className="text-[10px] text-slate-500 mt-1">{service.note}</p>}
        {service.error && <p className="text-[10px] text-red-400 mt-1 break-all">{service.error}</p>}
      </div>
    </Card>
  );
}

export default function HealthPage() {
  const toast = useToast();
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchApi<HealthData>("/admin/health");
      setHealth(data);
      setLastRefresh(new Date());
    } catch { toast.error("Failed to load health status"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, load]);

  const overallCfg = health ? (STATUS_CONFIG[health.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.unknown) : STATUS_CONFIG.unknown;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Activity className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">System Health</h1>
            <p className="text-slate-400 text-sm">
              {lastRefresh ? `Last checked: ${lastRefresh.toLocaleTimeString()}` : "Checking..."}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <button type="button" role="switch" aria-checked={autoRefresh} onClick={() => setAutoRefresh(v => !v)}
              className={`relative inline-flex h-5 w-9 rounded-full border-2 border-transparent transition-colors ${autoRefresh ? "bg-emerald-600" : "bg-slate-700"}`}>
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${autoRefresh ? "translate-x-4" : "translate-x-0"}`} />
            </button>
            <span className="text-xs text-slate-400">Auto-refresh (10s)</span>
          </label>
          <Button onClick={load} disabled={loading} variant="outline" size="sm" leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />}>Refresh</Button>
        </div>
      </div>

      {/* Overall status banner */}
      {health && (
        <div className={`p-4 rounded-2xl border flex items-center gap-4 ${overallCfg.bg}`}>
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${health.status === "ok" ? "bg-emerald-500/20" : "bg-red-500/20"}`}>
            <overallCfg.icon className={`w-6 h-6 ${overallCfg.color}`} />
          </div>
          <div>
            <h2 className={`text-lg font-bold ${overallCfg.color}`}>
              {health.status === "ok" ? "All Systems Operational" : "System Degraded"}
            </h2>
            <p className="text-xs text-slate-400">Checked at {new Date(health.checked_at).toLocaleString()}</p>
          </div>
        </div>
      )}

      {loading && !health ? (
        <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : health && (
        <>
          {/* Services */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Services</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(health.services).map(([name, service]) => (
                <ServiceCard key={name} name={name} service={service} />
              ))}
            </div>
          </div>

          {/* Platform stats */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Platform Stats</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total Users", value: health.platform?.total_users?.toLocaleString() || "—", icon: "👥" },
                { label: "Total Workspaces", value: health.platform?.total_orgs?.toLocaleString() || "—", icon: "🏢" },
                { label: "Active Workflow Runs", value: health.services.workflow_engine?.active_executions ?? "—", icon: "⚙️" },
                { label: "DB Latency", value: health.services.database?.latency_ms ? `${health.services.database.latency_ms}ms` : "—", icon: "⚡" },
              ].map((stat) => (
                <Card key={stat.label} className="p-4 text-center">
                  <div className="text-2xl mb-2">{stat.icon}</div>
                  <p className="text-2xl font-bold text-white">{stat.value}</p>
                  <p className="text-xs text-slate-500">{stat.label}</p>
                </Card>
              ))}
            </div>
          </div>

          {/* Config status */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Configuration Status</h2>
            <Card className="divide-y divide-slate-800">
              {Object.entries(health.config).map(([key, isSet]) => (
                <div key={key} className="flex items-center justify-between px-4 py-3">
                  <span className="text-xs text-slate-300 font-medium">{key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</span>
                  <div className={`flex items-center gap-1.5 ${isSet ? "text-emerald-400" : "text-slate-500"}`}>
                    {isSet ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    <span className="text-xs">{isSet ? "Configured" : "Not set"}</span>
                  </div>
                </div>
              ))}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
