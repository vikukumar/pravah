"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import {
  CheckCircle2, AlertCircle, Clock, Loader2, ChevronLeft,
  Activity, ChevronDown, ChevronUp, History,
} from "lucide-react";

const STATUS_STYLES: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  completed: { label: "Completed", icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  failed:    { label: "Failed",    icon: <AlertCircle className="w-3.5 h-3.5" />,  color: "text-red-400",     bg: "bg-red-500/10" },
  running:   { label: "Running",   icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, color: "text-blue-400", bg: "bg-blue-500/10" },
  queued:    { label: "Queued",    icon: <Clock className="w-3.5 h-3.5" />,         color: "text-slate-400",   bg: "bg-slate-700/40" },
  cancelled: { label: "Cancelled", icon: <AlertCircle className="w-3.5 h-3.5" />,  color: "text-slate-500",   bg: "bg-slate-700/30" },
};

export default function WorkflowExecutionsPage() {
  const params = useParams();
  const workflowId = params?.id as string;
  const router = useRouter();

  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<any>(null);

  useEffect(() => {
    if (!workflowId) return;
    Promise.all([
      fetchApi(`/workflows/${workflowId}/executions?limit=50`),
      fetchApi(`/workflows/${workflowId}`),
    ]).then(([execs, wf]) => {
      setExecutions(Array.isArray(execs) ? execs : []);
      setWorkflow(wf);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [workflowId]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => router.push(`/dashboard/workflows/${workflowId}`)}
          className="text-slate-500 hover:text-slate-200 p-2 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-slate-400" />
            Execution History
          </h1>
          {workflow && (
            <p className="text-sm text-slate-500 mt-0.5">{workflow.name}</p>
          )}
        </div>
        <div className="ml-auto">
          <Button
            onClick={() => {
              setLoading(true);
              fetchApi(`/workflows/${workflowId}/executions?limit=50`)
                .then((data) => setExecutions(Array.isArray(data) ? data : []))
                .finally(() => setLoading(false));
            }}
            variant="ghost"
            className="text-slate-400 hover:text-white border border-slate-700"
          >
            Refresh
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
        </div>
      ) : executions.length === 0 ? (
        <div className="text-center py-16">
          <Activity className="w-12 h-12 text-slate-700 mx-auto mb-4" />
          <p className="text-slate-500 text-sm">No executions yet. Run the workflow to see history here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {executions.map((exec) => {
            const st = STATUS_STYLES[exec.status] || STATUS_STYLES.queued;
            const isExpanded = expandedId === exec.id;
            return (
              <div key={exec.id} className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                {/* Execution summary row */}
                <button
                  className="w-full flex items-center gap-4 p-4 hover:bg-slate-800/50 transition-colors text-left"
                  onClick={() => setExpandedId(isExpanded ? null : exec.id)}
                >
                  <div className={`flex items-center gap-2 text-sm font-medium ${st.color}`}>
                    {st.icon}
                    {st.label}
                  </div>
                  <div className="text-xs text-slate-600 font-mono">
                    {exec.id?.slice(0, 12)}
                  </div>
                  <div className="text-xs text-slate-500">
                    {exec.trigger_source}
                  </div>
                  {exec.duration_ms && (
                    <div className="text-xs text-slate-600">{exec.duration_ms}ms</div>
                  )}
                  <div className="ml-auto flex items-center gap-3">
                    <div className="text-xs text-slate-600">
                      {formatDate(exec.queued_at || exec.started_at)}
                    </div>
                    <div className={`text-xs px-2 py-0.5 rounded-full ${st.bg} ${st.color}`}>
                      {exec.workflow_version ? `v${exec.workflow_version}` : ""}
                    </div>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-600" /> : <ChevronDown className="w-4 h-4 text-slate-600" />}
                  </div>
                </button>

                {/* Expanded: node execution details */}
                {isExpanded && (
                  <div className="border-t border-slate-800 p-4">
                    {exec.error_message && (
                      <div className="mb-3 text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2 border border-red-500/20">
                        {exec.error_message}
                      </div>
                    )}
                    {exec.node_executions?.length > 0 ? (
                      <div className="space-y-2">
                        {exec.node_executions.map((ne: any) => {
                          const nst = STATUS_STYLES[ne.status] || STATUS_STYLES.queued;
                          return (
                            <div
                              key={ne.node_key}
                              className={`flex items-start gap-3 text-xs p-2.5 rounded-lg ${nst.bg}`}
                            >
                              <span className={nst.color}>{nst.icon}</span>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className={`font-medium ${nst.color}`}>{ne.node_name}</span>
                                  <span className="text-slate-600 font-mono text-[10px]">{ne.node_type}</span>
                                  {ne.duration_ms && (
                                    <span className="ml-auto text-slate-600">{ne.duration_ms}ms</span>
                                  )}
                                </div>
                                {ne.error_message && (
                                  <p className="mt-1 text-red-400 text-[10px]">{ne.error_message}</p>
                                )}
                                {ne.output_data && Object.keys(ne.output_data).length > 0 && (
                                  <div className="mt-1.5 font-mono text-[10px] text-slate-500 bg-slate-950/60 rounded p-1.5 overflow-x-auto">
                                    {JSON.stringify(ne.output_data, null, 2).slice(0, 300)}
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-600">No node execution details available.</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
