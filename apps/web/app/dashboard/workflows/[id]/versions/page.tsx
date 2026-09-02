"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { formatDate } from "@/lib/utils";
import {
  History,
  ChevronLeft,
  RotateCcw,
  CheckCircle2,
  Clock,
  Loader2,
  Layers,
  GitBranch,
} from "lucide-react";

interface WorkflowVersionItem {
  id: string;
  workflow_id: string;
  version_number: number;
  is_active: boolean;
  description?: string;
  published_at?: string;
  published_by_id?: string;
  node_count: number;
  edge_count: number;
}

export default function WorkflowVersionsPage() {
  const params = useParams();
  const workflowId = params?.id as string;
  const router = useRouter();
  const toast = useToast();

  const [versions, setVersions] = useState<WorkflowVersionItem[]>([]);
  const [workflow, setWorkflow] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [restoringVersion, setRestoringVersion] = useState<number | null>(null);

  useEffect(() => {
    if (!workflowId) return;
    loadVersions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  async function loadVersions() {
    setLoading(true);
    try {
      const [vData, wfData] = await Promise.all([
        fetchApi(`/workflows/${workflowId}/versions`),
        fetchApi(`/workflows/${workflowId}`),
      ]);
      setVersions(Array.isArray(vData) ? vData : []);
      setWorkflow(wfData);
    } catch (e: any) {
      toast.error(e.message || "Failed to load versions");
    } finally {
      setLoading(false);
    }
  }

  async function handleRestore(versionNumber: number) {
    setRestoringVersion(versionNumber);
    try {
      await fetchApi(`/workflows/${workflowId}/versions/${versionNumber}/restore`, {
        method: "POST",
      });
      toast.success(`Restored draft to snapshot from v${versionNumber}`);
      router.push(`/dashboard/workflows/${workflowId}`);
    } catch (e: any) {
      toast.error(e.message || "Failed to restore version");
    } finally {
      setRestoringVersion(null);
    }
  }

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
            <History className="w-5 h-5 text-indigo-400" />
            Workflow Versions & Snapshots
          </h1>
          {workflow && (
            <p className="text-sm text-slate-500 mt-0.5">
              {workflow.name} &bull; Current Version v{workflow.published_version || workflow.version}
            </p>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
        </div>
      ) : versions.length === 0 ? (
        <div className="text-center py-16 bg-slate-900/50 border border-slate-800 rounded-2xl p-8 max-w-lg mx-auto">
          <GitBranch className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-base font-semibold text-white mb-1">No published versions yet</h3>
          <p className="text-slate-400 text-sm mb-6">
            Publish your workflow from the builder to create immutable version snapshots.
          </p>
          <Button
            onClick={() => router.push(`/dashboard/workflows/${workflowId}`)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            Open Workflow Builder
          </Button>
        </div>
      ) : (
        <div className="max-w-3xl space-y-4">
          {versions.map((ver) => (
            <div
              key={ver.id}
              className={`p-5 rounded-xl border bg-slate-900/80 transition-all ${
                ver.is_active
                  ? "border-indigo-500/50 shadow-lg shadow-indigo-500/5"
                  : "border-slate-800"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-white">
                      Version {ver.version_number}
                    </span>
                    {ver.is_active ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Active Published
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                        Archived Snapshot
                      </span>
                    )}
                  </div>
                  {ver.description && (
                    <p className="text-sm text-slate-300">{ver.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5" />
                      {ver.node_count} nodes &bull; {ver.edge_count} connections
                    </span>
                    {ver.published_at && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {formatDate(ver.published_at)}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleRestore(ver.version_number)}
                    disabled={restoringVersion === ver.version_number}
                    className="text-xs text-slate-300 hover:text-white border border-slate-700 hover:border-slate-500 gap-1.5"
                  >
                    {restoringVersion === ver.version_number ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <RotateCcw className="w-3.5 h-3.5" />
                    )}
                    Restore as Draft
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
