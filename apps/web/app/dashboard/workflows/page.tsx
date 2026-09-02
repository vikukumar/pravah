"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { formatDate } from "@/lib/utils";
import {
  Workflow as WorkflowIcon,
  Plus,
  Play,
  Pause,
  Pencil,
  Copy,
  Trash2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Search,
  Filter,
  LayoutTemplate,
  GitBranch,
  Bot,
  Zap,
  ChevronRight,
  Activity,
} from "lucide-react";

interface Workflow {
  id: string;
  name: string;
  description?: string;
  status: string; // draft | published | archived
  version: number;
  published_version?: number;
  is_active: boolean;
  last_executed_at?: string;
  last_execution_status?: string;
  icon?: string;
  color?: string;
  tags?: string[];
  nodes: any[];
  edges: any[];
  created_at: string;
  updated_at: string;
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-slate-700/60 text-slate-300 border-slate-600",
  published: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
  archived: "bg-slate-700/30 text-slate-500 border-slate-700",
};

const EXEC_STATUS_STYLES: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  completed: { label: "Passed", icon: <CheckCircle2 className="w-3.5 h-3.5" />, color: "text-emerald-400" },
  failed: { label: "Failed", icon: <AlertTriangle className="w-3.5 h-3.5" />, color: "text-red-400" },
  running: { label: "Running", icon: <Activity className="w-3.5 h-3.5 animate-pulse" />, color: "text-blue-400" },
};

export default function WorkflowsPage() {
  const router = useRouter();
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [deleteTarget, setDeleteTarget] = useState<Workflow | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  useEffect(() => {
    if (activeOrg) loadWorkflows();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeOrg, statusFilter]);

  async function loadWorkflows() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (search) params.set("search", search);
      const data = await fetchApi(`/workflows?${params}`);
      setWorkflows(Array.isArray(data) ? data : []);
    } catch {
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    try {
      const wf = await fetchApi("/workflows", {
        method: "POST",
        body: JSON.stringify({ name: newName.trim(), nodes: [], edges: [] }),
      }) as any;
      setCreating(false);
      setNewName("");
      toast.success(`Workflow "${wf.name}" created`);
      router.push(`/dashboard/workflows/${wf.id}`);
    } catch (e: any) {
      toast.error(e.message || "Failed to create workflow");
    }
  }

  async function handleDuplicate(wf: Workflow) {
    try {
      const copy = await fetchApi(`/workflows/${wf.id}/duplicate`, { method: "POST" }) as any;
      toast.success(`Duplicated as "${copy.name}"`);
      loadWorkflows();
    } catch (e: any) {
      toast.error(e.message || "Failed to duplicate");
    }
  }

  async function handleToggleActive(wf: Workflow) {
    const action = wf.is_active ? "deactivate" : "activate";
    try {
      await fetchApi(`/workflows/${wf.id}/${action}`, { method: "POST" });
      toast.success(`Workflow ${wf.is_active ? "paused" : "activated"}`);
      loadWorkflows();
    } catch (e: any) {
      toast.error(e.message || `Failed to ${action}`);
    }
  }

  async function handleDelete(wf: Workflow) {
    try {
      await fetchApi(`/workflows/${wf.id}`, { method: "DELETE" });
      setDeleteTarget(null);
      toast.success("Workflow archived");
      loadWorkflows();
    } catch (e: any) {
      toast.error(e.message || "Failed to delete");
    }
  }

  const filteredWorkflows = workflows.filter((w) =>
    !search || w.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-indigo-400" />
            </div>
            Workflows
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Visual automation workflows — connect AI, social publishing, and business logic.
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="ghost"
            onClick={() => router.push("/dashboard/workflows/templates")}
            className="text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 gap-2"
          >
            <LayoutTemplate className="w-4 h-4" />
            Templates
          </Button>
          <Button
            onClick={() => setCreating(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 px-4"
          >
            <Plus className="w-4 h-4" />
            New Workflow
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadWorkflows()}
            placeholder="Search workflows..."
            className="pl-9 bg-slate-900 border-slate-700 text-white placeholder:text-slate-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Workflow Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 rounded-2xl bg-slate-800/50 animate-pulse" />
          ))}
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-20 h-20 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
            <GitBranch className="w-10 h-10 text-indigo-400/60" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No workflows yet</h3>
          <p className="text-slate-500 text-sm max-w-sm mb-6">
            Create your first workflow to automate social media publishing with AI.
          </p>
          <Button
            onClick={() => setCreating(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2"
          >
            <Plus className="w-4 h-4" /> Create Workflow
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredWorkflows.map((wf) => {
            const execStatus = wf.last_execution_status
              ? EXEC_STATUS_STYLES[wf.last_execution_status]
              : null;
            return (
              <Card
                key={wf.id}
                className="group bg-slate-900/80 border-slate-700/60 hover:border-indigo-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/5 cursor-pointer overflow-hidden"
                onClick={() => router.push(`/dashboard/workflows/${wf.id}`)}
              >
                <div className="p-5">
                  {/* Top row */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-9 h-9 rounded-xl flex items-center justify-center text-white text-sm font-bold"
                        style={{ backgroundColor: wf.color || "#4f46e5", opacity: 0.9 }}
                      >
                        {wf.name[0]?.toUpperCase() || "W"}
                      </div>
                      <div>
                        <h3 className="font-semibold text-white text-sm leading-tight group-hover:text-indigo-300 transition-colors">
                          {wf.name}
                        </h3>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded-full border font-medium ${STATUS_STYLES[wf.status] || STATUS_STYLES.draft}`}
                          >
                            {wf.status}
                          </span>
                          {wf.is_active && (
                            <span className="text-xs px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 font-medium flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                              Active
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 transition-colors mt-1" />
                  </div>

                  {/* Description */}
                  {wf.description && (
                    <p className="text-xs text-slate-500 mb-3 line-clamp-2">{wf.description}</p>
                  )}

                  {/* Stats row */}
                  <div className="flex items-center gap-4 text-xs text-slate-500 mb-3">
                    <span className="flex items-center gap-1">
                      <Bot className="w-3 h-3" />
                      {wf.nodes?.length || 0} nodes
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      v{wf.version}
                    </span>
                    {execStatus && (
                      <span className={`flex items-center gap-1 ${execStatus.color}`}>
                        {execStatus.icon}
                        {execStatus.label}
                      </span>
                    )}
                  </div>

                  {/* Last run */}
                  {wf.last_executed_at && (
                    <p className="text-xs text-slate-600">
                      Last run: {formatDate(wf.last_executed_at)}
                    </p>
                  )}

                  {/* Actions */}
                  <div
                    className="flex gap-2 mt-4 pt-3 border-t border-slate-800"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Button
                      size="sm"
                      variant="ghost"
                      className="flex-1 text-xs text-slate-400 hover:text-white hover:bg-slate-800 gap-1.5"
                      onClick={() => router.push(`/dashboard/workflows/${wf.id}`)}
                    >
                      <Pencil className="w-3 h-3" /> Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className={`flex-1 text-xs gap-1.5 ${
                        wf.is_active
                          ? "text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                          : "text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                      }`}
                      onClick={() => handleToggleActive(wf)}
                      disabled={wf.status !== "published"}
                    >
                      {wf.is_active ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                      {wf.is_active ? "Pause" : "Activate"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800"
                      onClick={() => handleDuplicate(wf)}
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs text-slate-500 hover:text-red-400 hover:bg-red-500/10"
                      onClick={() => setDeleteTarget(wf)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={creating}
        onClose={() => { setCreating(false); setNewName(""); }}
        title="New Workflow"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-400">
            Give your workflow a name. You can add nodes and configure it in the builder.
          </p>
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            placeholder="e.g. Daily LinkedIn Posts"
            className="bg-slate-800 border-slate-600 text-white"
            autoFocus
          />
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="ghost" onClick={() => setCreating(false)} className="text-slate-400">
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newName.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              Create & Open Builder
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Archive Workflow"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-300">
            Archive <span className="font-semibold text-white">"{deleteTarget?.name}"</span>?{" "}
            Archived workflows stop running but their history is preserved.
          </p>
          <div className="flex gap-3 justify-end pt-2">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} className="text-slate-400">
              Cancel
            </Button>
            <Button
              onClick={() => deleteTarget && handleDelete(deleteTarget)}
              className="bg-red-600 hover:bg-red-500 text-white"
            >
              Archive
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
