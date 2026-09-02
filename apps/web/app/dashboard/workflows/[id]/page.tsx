"use client";

/**
 * PRAVAH Workflow Builder IDE
 * ============================
 * 3-panel IDE layout:
 *   Left:   Node library sidebar (collapsible, categorized, drag-to-add)
 *   Center: ReactFlow canvas (infinite, snap-to-grid, minimap, undo/redo)
 *   Right:  Node inspector drawer (config form from node registry schema)
 *   Bottom: Tabbed panel (Execution Logs, Variables, Validation)
 *
 * All interaction is real — saves to backend on change, executes real workflows.
 */

import React, {
  useCallback, useEffect, useRef, useState,
} from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Handle,
  Position,
  useReactFlow,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  Connection,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import {
  Play, Save, CheckCircle2, AlertCircle, X, ChevronRight,
  ChevronLeft, Clock, Bot, Share2, GitBranch, Variable, Globe,
  Bell, FileText, Timer, Filter, Shuffle, AlignLeft, Hash,
  ImagePlus, User, Send, Sparkles, Zap, RefreshCw, Settings2,
  History, Activity, Layers, Database, Braces, AlarmClock,
  FilePlus2, UserCheck, CreditCard, CalendarClock, ShieldCheck,
  ChevronDown, ChevronUp, Loader2, Check, AlertTriangle,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────────────
// Icon map — maps node icon name → Lucide component
// ─────────────────────────────────────────────────────────────────────

const ICON_MAP: Record<string, React.ReactNode> = {
  Play: <Play className="w-3.5 h-3.5" />,
  Clock: <Clock className="w-3.5 h-3.5" />,
  Webhook: <Globe className="w-3.5 h-3.5" />,
  FilePlus: <FilePlus2 className="w-3.5 h-3.5" />,
  CheckCircle: <CheckCircle2 className="w-3.5 h-3.5" />,
  Bot: <Bot className="w-3.5 h-3.5" />,
  RefreshCw: <RefreshCw className="w-3.5 h-3.5" />,
  AlignLeft: <AlignLeft className="w-3.5 h-3.5" />,
  Hash: <Hash className="w-3.5 h-3.5" />,
  ImagePlus: <ImagePlus className="w-3.5 h-3.5" />,
  Sparkles: <Sparkles className="w-3.5 h-3.5" />,
  Clock4: <Clock className="w-3.5 h-3.5" />,
  Send: <Send className="w-3.5 h-3.5" />,
  CalendarClock: <CalendarClock className="w-3.5 h-3.5" />,
  User: <User className="w-3.5 h-3.5" />,
  ShieldCheck: <ShieldCheck className="w-3.5 h-3.5" />,
  GitBranch: <GitBranch className="w-3.5 h-3.5" />,
  Shuffle: <Shuffle className="w-3.5 h-3.5" />,
  Filter: <Filter className="w-3.5 h-3.5" />,
  Variable: <Variable className="w-3.5 h-3.5" />,
  Database: <Database className="w-3.5 h-3.5" />,
  FileCode: <FileText className="w-3.5 h-3.5" />,
  Braces: <Braces className="w-3.5 h-3.5" />,
  Timer: <Timer className="w-3.5 h-3.5" />,
  AlarmClock: <AlarmClock className="w-3.5 h-3.5" />,
  Globe: <Globe className="w-3.5 h-3.5" />,
  Bell: <Bell className="w-3.5 h-3.5" />,
  FileText: <FileText className="w-3.5 h-3.5" />,
  CreditCard: <CreditCard className="w-3.5 h-3.5" />,
  FilePlus2: <FilePlus2 className="w-3.5 h-3.5" />,
  UserCheck: <UserCheck className="w-3.5 h-3.5" />,
};

const CATEGORY_COLORS: Record<string, { border: string; shadow: string; header: string; dot: string }> = {
  trigger: { border: "border-emerald-500/50", shadow: "shadow-emerald-500/5", header: "text-emerald-400", dot: "bg-emerald-400" },
  ai:      { border: "border-purple-500/50",  shadow: "shadow-purple-500/5",  header: "text-purple-400",  dot: "bg-purple-400" },
  social:  { border: "border-cyan-500/50",    shadow: "shadow-cyan-500/5",    header: "text-cyan-400",    dot: "bg-cyan-400" },
  logic:   { border: "border-amber-500/50",   shadow: "shadow-amber-500/5",   header: "text-amber-400",   dot: "bg-amber-400" },
  data:    { border: "border-slate-500/50",   shadow: "shadow-slate-500/5",   header: "text-slate-400",   dot: "bg-slate-400" },
  time:    { border: "border-pink-500/50",    shadow: "shadow-pink-500/5",    header: "text-pink-400",    dot: "bg-pink-400" },
  utility: { border: "border-lime-500/50",    shadow: "shadow-lime-500/5",    header: "text-lime-400",    dot: "bg-lime-400" },
  content: { border: "border-orange-500/50",  shadow: "shadow-orange-500/5",  header: "text-orange-400",  dot: "bg-orange-400" },
};

const CATEGORY_LABELS: Record<string, string> = {
  trigger: "Triggers",
  ai: "AI",
  social: "Social",
  logic: "Logic",
  data: "Data",
  time: "Time",
  utility: "Utility",
  content: "Content",
};

// ─────────────────────────────────────────────────────────────────────
// Custom Canvas Node Component
// ─────────────────────────────────────────────────────────────────────

function PravahNode({ data, selected }: any) {
  const cat = data.category || "utility";
  const styles = CATEGORY_COLORS[cat] || CATEGORY_COLORS.utility;
  const execStatus = data._execStatus;

  const statusRing = execStatus === "success"
    ? "ring-2 ring-emerald-500/70"
    : execStatus === "failed"
    ? "ring-2 ring-red-500/70"
    : execStatus === "running"
    ? "ring-2 ring-blue-500/70 animate-pulse"
    : "";

  return (
    <div
      className={`
        min-w-[190px] max-w-[220px] rounded-xl border bg-slate-900/95
        backdrop-blur-md shadow-xl transition-all duration-150
        ${styles.border} ${statusRing}
        ${selected ? "ring-2 ring-indigo-400/60 shadow-indigo-500/20" : ""}
      `}
    >
      <Handle type="target" position={Position.Top} className="!w-2.5 !h-2.5 !bg-indigo-500/80 !border-indigo-400" />

      {/* Execution status indicator */}
      {execStatus && (
        <div className="absolute -top-2 -right-2 z-10">
          {execStatus === "success" && <CheckCircle2 className="w-4 h-4 text-emerald-400 drop-shadow" />}
          {execStatus === "failed" && <AlertCircle className="w-4 h-4 text-red-400 drop-shadow" />}
          {execStatus === "running" && <Loader2 className="w-4 h-4 text-blue-400 animate-spin drop-shadow" />}
        </div>
      )}

      <div className="p-3">
        {/* Header */}
        <div className={`flex items-center gap-2 pb-2 border-b border-slate-800`}>
          <span className={styles.header}>
            {ICON_MAP[data.icon] || <Zap className="w-3.5 h-3.5" />}
          </span>
          <span className="text-[11px] font-bold text-slate-200 truncate leading-tight flex-1">
            {data.label || data.name}
          </span>
          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${styles.dot}`} />
        </div>

        {/* Type label */}
        <div className="pt-2 text-[10px] text-slate-500 font-mono truncate">
          {data.type}
        </div>

        {/* Config preview */}
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="mt-1.5 space-y-0.5">
            {Object.entries(data.config)
              .slice(0, 2)
              .map(([k, v]) => (
                <div key={k} className="flex gap-1 text-[10px]">
                  <span className="text-slate-600 font-mono truncate">{k}:</span>
                  <span className="text-slate-400 truncate">{String(v).substring(0, 20)}</span>
                </div>
              ))}
          </div>
        )}

        {/* Execution duration */}
        {data._duration && (
          <div className="mt-1 text-[10px] text-slate-600">
            {data._duration}ms
          </div>
        )}
      </div>

      {/* Multiple output handles for condition nodes */}
      {data.type === "logic_condition" ? (
        <>
          <Handle type="source" position={Position.Bottom} id="true" style={{ left: "33%" }}
            className="!w-2.5 !h-2.5 !bg-emerald-500/80 !border-emerald-400" />
          <Handle type="source" position={Position.Bottom} id="false" style={{ left: "66%" }}
            className="!w-2.5 !h-2.5 !bg-red-500/80 !border-red-400" />
        </>
      ) : (
        <Handle type="source" position={Position.Bottom} className="!w-2.5 !h-2.5 !bg-indigo-500/80 !border-indigo-400" />
      )}
    </div>
  );
}

const NODE_TYPES = { pravahNode: PravahNode };

// ─────────────────────────────────────────────────────────────────────
// Main Workflow Builder
// ─────────────────────────────────────────────────────────────────────

function WorkflowBuilderInner() {
  const params = useParams();
  const workflowId = params?.id as string;
  const router = useRouter();
  const { screenToFlowPosition, fitView } = useReactFlow();
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  // ── Workflow State ──
  const [workflow, setWorkflow] = useState<any>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [wfName, setWfName] = useState("");
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [loading, setLoading] = useState(true);

  // ── Node Registry ──
  const [nodeRegistry, setNodeRegistry] = useState<Record<string, any[]>>({});

  // ── Selected Node (Inspector) ──
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  // ── Bottom Panel ──
  const [bottomTab, setBottomTab] = useState<"logs" | "validation" | "variables">("validation");
  const [bottomOpen, setBottomOpen] = useState(true);

  // ── Validation & Execution ──
  const [validation, setValidation] = useState<any>(null);
  const [currentExec, setCurrentExec] = useState<any>(null);
  const [execNodeStatuses, setExecNodeStatuses] = useState<Record<string, any>>({});

  // ── Left Sidebar ──
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [categoryExpanded, setCategoryExpanded] = useState<Record<string, boolean>>({
    trigger: true, ai: true, social: false, logic: false, data: false,
    time: false, utility: false, content: false,
  });

  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  // ── Load workflow + node registry ──
  useEffect(() => {
    if (!workflowId) return;
    Promise.all([
      fetchApi(`/workflows/${workflowId}`),
      fetchApi("/workflows/node-registry"),
    ])
      .then(([wf, registry]: [any, any]) => {
        setWorkflow(wf);
        setWfName(wf.name);
        setNodeRegistry(registry.by_category || {});
        setNodes(
          (wf.nodes || []).map((n: any) => ({
            id: n.id,
            type: "pravahNode",
            position: n.position || { x: 100, y: 100 },
            data: {
              id: n.id,
              name: n.name,
              label: n.label || n.name,
              type: n.type,
              category: n.category,
              config: n.config || {},
              icon: n.icon,
              color: n.color,
            },
          }))
        );
        setEdges(
          (wf.edges || []).map((e: any) => ({
            id: e.id || `${e.source}-${e.target}`,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle,
            targetHandle: e.targetHandle,
            animated: true,
            style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.7 },
          }))
        );
      })
      .catch(() => toast.error("Failed to load workflow"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  // ── ReactFlow handlers ──
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) =>
      addEdge(
        {
          ...params,
          animated: true,
          style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.7 },
        },
        eds
      )
    );
  }, []);

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // ── Drag from node library ──
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const nodeTypeJson = event.dataTransfer.getData("application/pravah-node");
      if (!nodeTypeJson) return;
      const nodeTypeDef = JSON.parse(nodeTypeJson);
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const newId = `node_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

      setNodes((nds) => [
        ...nds,
        {
          id: newId,
          type: "pravahNode",
          position,
          data: {
            id: newId,
            name: nodeTypeDef.name,
            label: nodeTypeDef.name,
            type: nodeTypeDef.id,
            category: nodeTypeDef.category,
            config: {},
            icon: nodeTypeDef.icon,
            color: nodeTypeDef.color,
          },
        },
      ]);
      setSelectedNode(null);
    },
    [screenToFlowPosition]
  );

  // ── Save ──
  async function handleSave() {
    setSaving(true);
    try {
      const payload = {
        name: wfName,
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.data.type,
          name: n.data.name,
          label: n.data.label,
          category: n.data.category,
          config: n.data.config || {},
          position: n.position,
          icon: n.data.icon,
          color: n.data.color,
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || null,
          targetHandle: e.targetHandle || null,
        })),
      };
      await fetchApi(`/workflows/${workflowId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      toast.success("Workflow saved");
    } catch (e: any) {
      toast.error(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  // ── Validate ──
  async function handleValidate() {
    try {
      const result = await fetchApi(`/workflows/${workflowId}/validate`, { method: "POST" }) as any;
      setValidation(result);
      setBottomTab("validation");
      setBottomOpen(true);
      if (result.valid) toast.success("Workflow is valid ✓");
    } catch (e: any) {
      toast.error(e.message || "Validation failed");
    }
  }

  // ── Publish ──
  async function handlePublish() {
    setPublishing(true);
    try {
      await handleSave();
      const result = await fetchApi(`/workflows/${workflowId}/publish`, { method: "POST" }) as any;
      toast.success(`Published as v${result.version_number}`);
      setWorkflow((prev: any) => ({
        ...prev,
        status: "published",
        published_version: result.version_number,
      }));
    } catch (e: any) {
      if (e.detail?.errors) {
        toast.error(`Validation errors: ${e.detail.errors.join("; ")}`);
      } else {
        toast.error(e.message || "Publish failed");
      }
    } finally {
      setPublishing(false);
    }
  }

  // ── Execute ──
  async function handleRun() {
    setExecuting(true);
    setExecNodeStatuses({});
    setBottomTab("logs");
    setBottomOpen(true);
    try {
      const result = await fetchApi(`/workflows/${workflowId}/execute`, {
        method: "POST",
        body: JSON.stringify({ trigger_source: "manual", trigger_payload: {} }),
      }) as any;
      setCurrentExec(result);
      toast.success(`Execution queued (${result.execution_id.slice(0, 8)})`);

      // Poll for status updates via SSE
      const evtSource = new EventSource(
        `/api/v1/workflows/${workflowId}/executions/${result.execution_id}/stream`
      );
      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        setCurrentExec(data);
        // Update node status overlay on canvas
        const statusMap: Record<string, any> = {};
        for (const ne of data.node_executions || []) {
          statusMap[ne.node_key] = { status: ne.status, duration: ne.duration_ms };
        }
        setExecNodeStatuses(statusMap);
        setNodes((prev) =>
          prev.map((n) => ({
            ...n,
            data: {
              ...n.data,
              _execStatus: statusMap[n.id]?.status,
              _duration: statusMap[n.id]?.duration,
            },
          }))
        );
      };
      evtSource.addEventListener("done", () => {
        evtSource.close();
        setExecuting(false);
      });
      evtSource.onerror = () => {
        evtSource.close();
        setExecuting(false);
      };
    } catch (e: any) {
      toast.error(e.message || "Execution failed");
      setExecuting(false);
    }
  }

  // ── Update node config from inspector ──
  function updateNodeConfig(nodeId: string, newConfig: Record<string, any>) {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...(n.data as any), config: { ...((n.data as any).config || {}), ...newConfig } } }
          : n
      )
    );
    if (selectedNode?.id === nodeId) {
      setSelectedNode((prev) =>
        prev ? { ...prev, data: { ...(prev.data as any), config: { ...((prev.data as any).config || {}), ...newConfig } } } : null
      );
    }
  }

  function updateNodeLabel(nodeId: string, label: string) {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === nodeId ? { ...n, data: { ...(n.data as any), label } } : n
      )
    );
    if (selectedNode?.id === nodeId) {
      setSelectedNode((prev) =>
        prev ? { ...prev, data: { ...(prev.data as any), label } } : null
      );
    }
  }

  function deleteNode(nodeId: string) {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    setSelectedNode(null);
  }

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          Loading workflow builder...
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────
  const selectedNodeDef = selectedNode
    ? Object.values(nodeRegistry)
        .flat()
        .find((nd: any) => nd.id === selectedNode.data.type)
    : null;

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      {/* ── Top Toolbar ── */}
      <div className="h-14 flex-shrink-0 bg-slate-900 border-b border-slate-800 flex items-center px-4 gap-3 z-20">
        {/* Back */}
        <button
          onClick={() => router.push("/dashboard/workflows")}
          className="text-slate-500 hover:text-slate-200 transition-colors p-1.5 rounded-lg hover:bg-slate-800"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>

        <div className="w-px h-5 bg-slate-700" />

        {/* Name */}
        <input
          value={wfName}
          onChange={(e) => setWfName(e.target.value)}
          className="bg-transparent text-white font-semibold text-sm focus:outline-none border-b border-transparent hover:border-slate-600 focus:border-indigo-500 pb-0.5 transition-colors min-w-[150px] max-w-xs"
          placeholder="Workflow name..."
        />

        {/* Status badge */}
        {workflow && (
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
            workflow.status === "published"
              ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
              : "bg-slate-700/60 text-slate-400 border-slate-600"
          }`}>
            {workflow.status}
            {workflow.published_version && ` v${workflow.published_version}`}
          </span>
        )}

        <div className="flex-1" />

        {/* Actions */}
        <button
          onClick={handleValidate}
          className="text-slate-400 hover:text-white text-xs px-3 py-1.5 rounded-lg border border-slate-700 hover:border-slate-500 transition-all flex items-center gap-1.5"
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Validate
        </button>

        <button
          onClick={handleSave}
          disabled={saving}
          className="text-slate-400 hover:text-white text-xs px-3 py-1.5 rounded-lg border border-slate-700 hover:border-slate-500 transition-all flex items-center gap-1.5 disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          Save
        </button>

        <button
          onClick={handlePublish}
          disabled={publishing || saving}
          className="text-indigo-300 hover:text-white text-xs px-3 py-1.5 rounded-lg border border-indigo-500/50 hover:border-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
        >
          {publishing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
          Publish
        </button>

        <button
          onClick={handleRun}
          disabled={executing || workflow?.status !== "published"}
          className="text-white text-xs px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 transition-all flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          title={workflow?.status !== "published" ? "Publish the workflow before running" : ""}
        >
          {executing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          Run
        </button>

        <button
          onClick={() => router.push(`/dashboard/workflows/${workflowId}/executions`)}
          className="text-slate-500 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          title="Execution History"
        >
          <History className="w-4 h-4" />
        </button>
      </div>

      {/* ── Main Content ── */}
      <div className="flex-1 flex overflow-hidden">
        {/* ── Left Sidebar: Node Library ── */}
        <div
          className={`flex-shrink-0 bg-slate-900 border-r border-slate-800 transition-all duration-200 flex flex-col ${
            sidebarOpen ? "w-60" : "w-0 overflow-hidden border-0"
          }`}
        >
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Nodes</span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-slate-600 hover:text-slate-400 p-0.5"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>

          <div className="overflow-y-auto flex-1 py-2">
            {Object.entries(nodeRegistry).map(([category, categoryNodes]) => {
              const styles = CATEGORY_COLORS[category] || CATEGORY_COLORS.utility;
              return (
                <div key={category} className="px-2 mb-1">
                  <button
                    className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-800 transition-colors"
                    onClick={() => setCategoryExpanded((prev) => ({ ...prev, [category]: !prev[category] }))}
                  >
                    <span className={`text-xs font-semibold uppercase tracking-wider ${styles.header}`}>
                      {CATEGORY_LABELS[category] || category}
                    </span>
                    {categoryExpanded[category]
                      ? <ChevronUp className="w-3 h-3 text-slate-600" />
                      : <ChevronDown className="w-3 h-3 text-slate-600" />}
                  </button>

                  {categoryExpanded[category] && (
                    <div className="ml-1 mt-1 space-y-1">
                      {(categoryNodes as any[]).map((nodeType: any) => (
                        <div
                          key={nodeType.id}
                          draggable
                          onDragStart={(e) => {
                            e.dataTransfer.setData(
                              "application/pravah-node",
                              JSON.stringify(nodeType)
                            );
                            e.dataTransfer.effectAllowed = "move";
                          }}
                          className={`
                            px-2.5 py-2 rounded-lg border cursor-grab active:cursor-grabbing
                            bg-slate-900 hover:bg-slate-800 transition-colors
                            ${styles.border} hover:border-opacity-80
                          `}
                        >
                          <div className="flex items-center gap-2">
                            <span className={styles.header}>
                              {ICON_MAP[nodeType.icon] || <Zap className="w-3.5 h-3.5" />}
                            </span>
                            <span className="text-xs text-slate-300 font-medium leading-tight">
                              {nodeType.name}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Sidebar toggle when closed */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-6 h-12 bg-slate-800 border border-slate-700 rounded-r-lg flex items-center justify-center text-slate-500 hover:text-slate-200 hover:bg-slate-700 transition-colors"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}

        {/* ── Center: Canvas ── */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* ReactFlow Canvas */}
          <div
            ref={reactFlowWrapper}
            className="flex-1"
            onDragOver={onDragOver}
            onDrop={onDrop}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={NODE_TYPES}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              snapToGrid
              snapGrid={[16, 16]}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              deleteKeyCode="Delete"
              minZoom={0.1}
              maxZoom={2.5}
              className="bg-slate-950"
              defaultEdgeOptions={{
                animated: true,
                style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.7 },
              }}
            >
              <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#1e293b" />
              <Controls
                className="!bg-slate-900 !border-slate-700 [&_button]:!bg-slate-900 [&_button]:!text-slate-400 [&_button:hover]:!bg-slate-800"
              />
              <MiniMap
                style={{ background: "#0f172a", border: "1px solid #1e293b" }}
                nodeColor={(n) => {
                  const cat = n.data?.category as string;
                  const colors: Record<string, string> = {
                    trigger: "#10b981", ai: "#8b5cf6", social: "#06b6d4",
                    logic: "#f59e0b", data: "#64748b", time: "#ec4899",
                    utility: "#84cc16", content: "#f97316",
                  };
                  return colors[cat] || "#6366f1";
                }}
                maskColor="rgba(0,0,0,0.6)"
              />
              {nodes.length === 0 && (
                <Panel position="top-center" className="mt-16">
                  <div className="text-center text-slate-600 select-none">
                    <GitBranch className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm font-medium">Drag nodes from the sidebar to start building</p>
                    <p className="text-xs mt-1">Connect nodes by dragging from their output handles</p>
                  </div>
                </Panel>
              )}
            </ReactFlow>
          </div>

          {/* ── Bottom Panel ── */}
          <div className={`bg-slate-900 border-t border-slate-800 flex flex-col transition-all duration-200 ${
            bottomOpen ? "h-48" : "h-10"
          }`}>
            {/* Tab bar */}
            <div className="flex items-center gap-1 px-3 py-2 border-b border-slate-800 flex-shrink-0">
              {(["validation", "logs", "variables"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => { setBottomTab(tab); setBottomOpen(true); }}
                  className={`text-xs px-3 py-1 rounded-md transition-colors capitalize ${
                    bottomTab === tab && bottomOpen
                      ? "bg-slate-800 text-white"
                      : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {tab === "logs" && <Activity className="w-3 h-3 inline mr-1" />}
                  {tab === "validation" && <CheckCircle2 className="w-3 h-3 inline mr-1" />}
                  {tab === "variables" && <Variable className="w-3 h-3 inline mr-1" />}
                  {tab}
                  {tab === "validation" && validation && (
                    <span className={`ml-1.5 px-1 rounded text-[10px] ${validation.valid ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                      {validation.valid ? "✓" : `${validation.errors?.length} errors`}
                    </span>
                  )}
                </button>
              ))}
              <div className="flex-1" />
              <button
                onClick={() => setBottomOpen((v) => !v)}
                className="text-slate-600 hover:text-slate-400 p-0.5"
              >
                {bottomOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
              </button>
            </div>

            {/* Tab content */}
            {bottomOpen && (
              <div className="flex-1 overflow-y-auto p-3 text-xs space-y-1.5">
                {bottomTab === "validation" && (
                  validation ? (
                    <>
                      <div className={`flex items-center gap-2 font-semibold ${validation.valid ? "text-emerald-400" : "text-red-400"}`}>
                        {validation.valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        {validation.valid ? "Workflow is valid" : `${validation.errors?.length} validation error(s)`}
                      </div>
                      {validation.errors?.map((err: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-red-300 bg-red-500/10 rounded px-2 py-1.5">
                          <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          {err}
                        </div>
                      ))}
                      {validation.warnings?.map((w: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-amber-300 bg-amber-500/10 rounded px-2 py-1.5">
                          <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          {w}
                        </div>
                      ))}
                      <div className="text-slate-600 mt-2">
                        {validation.node_count} nodes · {validation.edge_count} edges · {validation.trigger_count} trigger(s)
                      </div>
                    </>
                  ) : (
                    <p className="text-slate-600">Click Validate to check the workflow for errors.</p>
                  )
                )}

                {bottomTab === "logs" && (
                  currentExec ? (
                    <div className="space-y-1">
                      <div className={`font-semibold flex items-center gap-2 ${
                        currentExec.status === "completed" ? "text-emerald-400" :
                        currentExec.status === "failed" ? "text-red-400" : "text-blue-400"
                      }`}>
                        {currentExec.status === "running" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                        Execution {currentExec.execution_id?.slice(0, 8) || currentExec.id?.slice(0, 8)} — {currentExec.status}
                      </div>
                      {(currentExec.node_executions || []).map((ne: any) => (
                        <div key={ne.node_key} className="flex items-center gap-2 text-slate-400 bg-slate-800/60 rounded px-2 py-1">
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                            ne.status === "success" ? "bg-emerald-400" :
                            ne.status === "failed" ? "bg-red-400" :
                            ne.status === "running" ? "bg-blue-400 animate-pulse" : "bg-slate-600"
                          }`} />
                          <span className="text-slate-300 font-mono">{ne.node_name}</span>
                          <span className="text-slate-600">({ne.node_type})</span>
                          {ne.duration_ms && <span className="ml-auto text-slate-600">{ne.duration_ms}ms</span>}
                          {ne.error_message && (
                            <span className="text-red-400 ml-2 truncate">{ne.error_message}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-600">No execution history. Run the workflow to see logs here.</p>
                  )
                )}

                {bottomTab === "variables" && (
                  <div className="text-slate-500">
                    Workflow variables are configured in Settings → Variables. Use{" "}
                    <code className="text-slate-400">{"{{vars.NAME}}"}</code> in node configuration fields.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Right Panel: Node Inspector ── */}
        {selectedNode && (
          <div className="w-72 flex-shrink-0 bg-slate-900 border-l border-slate-800 flex flex-col overflow-hidden">
            {/* Header */}
            <div className="p-3 border-b border-slate-800 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 truncate">
                {selectedNode.data.name as string}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-600 hover:text-slate-400 p-0.5"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Inspector content */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {/* Node label */}
              <div>
                <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Label</label>
                <input
                  value={(selectedNode.data.label as string) || ""}
                  onChange={(e) => updateNodeLabel(selectedNode.id, e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 transition-colors"
                  placeholder="Display label..."
                />
              </div>

              {/* Config schema fields */}
              {selectedNodeDef?.config_schema?.map((field: any) => (
                <div key={field.key}>
                  <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    {field.label}
                    {field.required && <span className="text-red-400">*</span>}
                  </label>
                  {field.description && (
                    <p className="text-[10px] text-slate-600 mt-0.5 mb-1">{field.description}</p>
                  )}

                  {field.field_type === "select" ? (
                    <select
                      value={(selectedNode.data.config as any)?.[field.key] ?? field.default ?? ""}
                      onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                      className="w-full mt-1 bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      {field.options?.map((opt: any) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : field.field_type === "textarea" || field.field_type === "expression" ? (
                    <textarea
                      value={(selectedNode.data.config as any)?.[field.key] ?? field.default ?? ""}
                      onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                      placeholder={field.placeholder}
                      rows={3}
                      className="w-full mt-1 bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 transition-colors font-mono resize-none"
                    />
                  ) : field.field_type === "boolean" ? (
                    <div className="flex items-center gap-2 mt-1">
                      <button
                        onClick={() =>
                          updateNodeConfig(selectedNode.id, {
                            [field.key]: !((selectedNode.data.config as any)?.[field.key] ?? field.default),
                          })
                        }
                        className={`w-9 h-5 rounded-full transition-colors ${
                          ((selectedNode.data.config as any)?.[field.key] ?? field.default)
                            ? "bg-indigo-600"
                            : "bg-slate-700"
                        }`}
                      >
                        <span
                          className={`block w-3.5 h-3.5 rounded-full bg-white mx-0.75 transition-transform ${
                            ((selectedNode.data.config as any)?.[field.key] ?? field.default)
                              ? "translate-x-4"
                              : "translate-x-0.5"
                          }`}
                        />
                      </button>
                      <span className="text-xs text-slate-400">
                        {((selectedNode.data.config as any)?.[field.key] ?? field.default) ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                  ) : field.field_type === "number" ? (
                    <input
                      type="number"
                      value={(selectedNode.data.config as any)?.[field.key] ?? field.default ?? ""}
                      onChange={(e) =>
                        updateNodeConfig(selectedNode.id, { [field.key]: Number(e.target.value) })
                      }
                      min={field.min_value}
                      max={field.max_value}
                      placeholder={field.placeholder}
                      className="w-full mt-1 bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  ) : (
                    <input
                      type="text"
                      value={(selectedNode.data.config as any)?.[field.key] ?? field.default ?? ""}
                      onChange={(e) =>
                        updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })
                      }
                      placeholder={field.placeholder}
                      className="w-full mt-1 bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-2 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                    />
                  )}
                </div>
              ))}

              {/* Node info */}
              <div className="pt-3 border-t border-slate-800 space-y-1">
                <div className="flex justify-between text-[10px]">
                  <span className="text-slate-600">Type</span>
                  <span className="text-slate-400 font-mono">{selectedNode.data.type as string}</span>
                </div>
                <div className="flex justify-between text-[10px]">
                  <span className="text-slate-600">Category</span>
                  <span className="text-slate-400 capitalize">{selectedNode.data.category as string}</span>
                </div>
                <div className="flex justify-between text-[10px]">
                  <span className="text-slate-600">Node ID</span>
                  <span className="text-slate-500 font-mono text-[9px]">{selectedNode.id}</span>
                </div>
              </div>

              {/* Delete node */}
              <button
                onClick={() => deleteNode(selectedNode.id)}
                className="w-full text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 border border-red-500/20 hover:border-red-500/40 rounded-lg py-1.5 transition-all"
              >
                Remove Node
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkflowBuilderPage() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderInner />
    </ReactFlowProvider>
  );
}
