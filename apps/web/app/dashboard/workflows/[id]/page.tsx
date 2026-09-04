"use client";

/**
 * PRAVAH Flowise-Style Workflow & Tool Canvas Editor
 * ===================================================
 * Features:
 *   - 100% Unbranded Canvas (No React Flow watermark / attribution)
 *   - Flowise-Grade Interactive Nodes:
 *       • Inline dropdowns, inputs, and toggles directly on the node cards
 *       • Left & Right socket handles with connection labels
 *       • Duplicate, Delete, and "Edit Tool Options" quick actions on node header
 *       • Live execution status badges with duration & error highlights
 *   - Flowise-Style "Add Nodes & Tools" Modal / Palette:
 *       • Searchable catalog of Tools, Triggers, AI Models, Social Channels, Logic
 *       • Click-to-add or drag-and-drop onto canvas
 *   - Comprehensive Tool Inspector & Parameter Editor:
 *       • Dynamic key-value header/parameter editor
 *       • Interactive prompt template editor with dynamic variable pills ({{...}})
 *       • Live "Test Step / Preview Output" runner
 *   - Auto-Layout / Organize Nodes
 *   - Seamless integration with real backend execution & SSE streaming
 */

import React, {
  useCallback, useEffect, useMemo, useRef, useState, createContext, useContext,
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
  Plus, Search, Copy, Trash2, Wrench, Code, SlidersHorizontal,
  Terminal, ArrowRight, ExternalLink, HelpCircle,
} from "lucide-react";

// ─────────────────────────────────────────────────────────────────────
// Icon Map
// ─────────────────────────────────────────────────────────────────────

const ICON_MAP: Record<string, React.ReactNode> = {
  Play: <Play className="w-4 h-4" />,
  Clock: <Clock className="w-4 h-4" />,
  Webhook: <Globe className="w-4 h-4" />,
  FilePlus: <FilePlus2 className="w-4 h-4" />,
  CheckCircle: <CheckCircle2 className="w-4 h-4" />,
  Bot: <Bot className="w-4 h-4" />,
  RefreshCw: <RefreshCw className="w-4 h-4" />,
  AlignLeft: <AlignLeft className="w-4 h-4" />,
  Hash: <Hash className="w-4 h-4" />,
  ImagePlus: <ImagePlus className="w-4 h-4" />,
  Sparkles: <Sparkles className="w-4 h-4" />,
  Clock4: <Clock className="w-4 h-4" />,
  Send: <Send className="w-4 h-4" />,
  CalendarClock: <CalendarClock className="w-4 h-4" />,
  User: <User className="w-4 h-4" />,
  ShieldCheck: <ShieldCheck className="w-4 h-4" />,
  GitBranch: <GitBranch className="w-4 h-4" />,
  Shuffle: <Shuffle className="w-4 h-4" />,
  Filter: <Filter className="w-4 h-4" />,
  Variable: <Variable className="w-4 h-4" />,
  Database: <Database className="w-4 h-4" />,
  FileCode: <Code className="w-4 h-4" />,
  Braces: <Braces className="w-4 h-4" />,
  Timer: <Timer className="w-4 h-4" />,
  AlarmClock: <AlarmClock className="w-4 h-4" />,
  Globe: <Globe className="w-4 h-4" />,
  Bell: <Bell className="w-4 h-4" />,
  FileText: <FileText className="w-4 h-4" />,
  CreditCard: <CreditCard className="w-4 h-4" />,
  FilePlus2: <FilePlus2 className="w-4 h-4" />,
  UserCheck: <UserCheck className="w-4 h-4" />,
  Wrench: <Wrench className="w-4 h-4" />,
};

const CATEGORY_STYLES: Record<string, {
  border: string;
  glow: string;
  badge: string;
  badgeBg: string;
  headerBg: string;
  iconColor: string;
  handleColor: string;
}> = {
  trigger: {
    border: "border-emerald-500/50 hover:border-emerald-400/80",
    glow: "shadow-emerald-500/10",
    badge: "text-emerald-400",
    badgeBg: "bg-emerald-500/10 border-emerald-500/30",
    headerBg: "from-emerald-500/15 via-emerald-500/5 to-transparent",
    iconColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    handleColor: "!bg-emerald-500 !border-slate-900",
  },
  ai: {
    border: "border-purple-500/50 hover:border-purple-400/80",
    glow: "shadow-purple-500/10",
    badge: "text-purple-400",
    badgeBg: "bg-purple-500/10 border-purple-500/30",
    headerBg: "from-purple-500/15 via-purple-500/5 to-transparent",
    iconColor: "text-purple-400 bg-purple-500/10 border-purple-500/30",
    handleColor: "!bg-purple-500 !border-slate-900",
  },
  utility: {
    border: "border-blue-500/50 hover:border-blue-400/80",
    glow: "shadow-blue-500/10",
    badge: "text-blue-400",
    badgeBg: "bg-blue-500/10 border-blue-500/30",
    headerBg: "from-blue-500/15 via-blue-500/5 to-transparent",
    iconColor: "text-blue-400 bg-blue-500/10 border-blue-500/30",
    handleColor: "!bg-blue-500 !border-slate-900",
  },
  social: {
    border: "border-cyan-500/50 hover:border-cyan-400/80",
    glow: "shadow-cyan-500/10",
    badge: "text-cyan-400",
    badgeBg: "bg-cyan-500/10 border-cyan-500/30",
    headerBg: "from-cyan-500/15 via-cyan-500/5 to-transparent",
    iconColor: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
    handleColor: "!bg-cyan-500 !border-slate-900",
  },
  logic: {
    border: "border-amber-500/50 hover:border-amber-400/80",
    glow: "shadow-amber-500/10",
    badge: "text-amber-400",
    badgeBg: "bg-amber-500/10 border-amber-500/30",
    headerBg: "from-amber-500/15 via-amber-500/5 to-transparent",
    iconColor: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    handleColor: "!bg-amber-500 !border-slate-900",
  },
  data: {
    border: "border-indigo-500/50 hover:border-indigo-400/80",
    glow: "shadow-indigo-500/10",
    badge: "text-indigo-400",
    badgeBg: "bg-indigo-500/10 border-indigo-500/30",
    headerBg: "from-indigo-500/15 via-indigo-500/5 to-transparent",
    iconColor: "text-indigo-400 bg-indigo-500/10 border-indigo-500/30",
    handleColor: "!bg-indigo-500 !border-slate-900",
  },
  content: {
    border: "border-orange-500/50 hover:border-orange-400/80",
    glow: "shadow-orange-500/10",
    badge: "text-orange-400",
    badgeBg: "bg-orange-500/10 border-orange-500/30",
    headerBg: "from-orange-500/15 via-orange-500/5 to-transparent",
    iconColor: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    handleColor: "!bg-orange-500 !border-slate-900",
  },
  time: {
    border: "border-pink-500/50 hover:border-pink-400/80",
    glow: "shadow-pink-500/10",
    badge: "text-pink-400",
    badgeBg: "bg-pink-500/10 border-pink-500/30",
    headerBg: "from-pink-500/15 via-pink-500/5 to-transparent",
    iconColor: "text-pink-400 bg-pink-500/10 border-pink-500/30",
    handleColor: "!bg-pink-500 !border-slate-900",
  },
};

const CATEGORY_LABELS: Record<string, string> = {
  trigger: "Triggers",
  utility: "Tools & APIs",
  ai: "AI & Agents",
  social: "Social Publishing",
  logic: "Logic & Routing",
  data: "Data & Variables",
  time: "Time & Delays",
  content: "Content Operations",
};

// ─────────────────────────────────────────────────────────────────────
// Node Actions Context (Decoupled from Node Data to Prevent Stale Closures & Render Cascades)
// ─────────────────────────────────────────────────────────────────────

interface NodeActionsContextType {
  updateNodeConfig: (nodeId: string, newConfig: Record<string, any>) => void;
  deleteNode: (nodeId: string) => void;
  duplicateNode: (nodeId: string) => void;
  openInspector: (nodeId: string) => void;
}

const NodeActionsContext = createContext<NodeActionsContextType>({
  updateNodeConfig: () => {},
  deleteNode: () => {},
  duplicateNode: () => {},
  openInspector: () => {},
});

const useNodeActions = () => useContext(NodeActionsContext);

// ─────────────────────────────────────────────────────────────────────
// Flowise-Grade Interactive Node Component
// ─────────────────────────────────────────────────────────────────────

function FlowiseNode({ id, data, selected }: any) {
  const { openInspector, duplicateNode, deleteNode, updateNodeConfig } = useNodeActions();

  const cat = data.category || "utility";
  const styles = CATEGORY_STYLES[cat] || CATEGORY_STYLES.utility;
  const execStatus = data._execStatus;
  const config = data.config || {};
  const schema = data.nodeDef?.config_schema || [];

  // Identify prominent inline fields (selects, key text inputs)
  const inlineSelects = schema.filter((f: any) => f.field_type === "select").slice(0, 2);
  const inlineTextField = schema.find((f: any) => f.field_type === "text" && !f.key.toLowerCase().includes("token") && !f.key.toLowerCase().includes("secret"));
  const inlineTextarea = schema.find((f: any) => (f.field_type === "textarea" || f.field_type === "expression"));

  return (
    <div
      className={`
        w-80 rounded-2xl border bg-slate-900/95 backdrop-blur-xl shadow-2xl transition-all duration-200
        ${styles.border} ${styles.glow}
        ${selected ? "ring-2 ring-indigo-400/90 shadow-indigo-500/30 border-indigo-400" : ""}
        ${execStatus === "running" ? "ring-2 ring-blue-500 animate-pulse border-blue-400" : ""}
        ${execStatus === "success" ? "ring-1 ring-emerald-500/80" : ""}
        ${execStatus === "failed" ? "ring-2 ring-red-500/80 border-red-500" : ""}
      `}
    >
      {/* ── Left Input Handle ── */}
      {cat !== "trigger" && (
        <div className="absolute -left-3 top-1/2 -translate-y-1/2 flex items-center group">
          <Handle
            type="target"
            position={Position.Left}
            className={`!w-3 !h-3 !border-2 ${styles.handleColor}`}
          />
          <span className="hidden group-hover:block absolute left-4 px-1.5 py-0.5 rounded bg-slate-950 text-[9px] font-mono text-slate-300 whitespace-nowrap shadow border border-slate-800 pointer-events-none">
            Input
          </span>
        </div>
      )}

      {/* ── Header ── */}
      <div className={`px-3.5 py-3 rounded-t-2xl bg-gradient-to-b ${styles.headerBg} border-b border-slate-800/80 flex items-center justify-between gap-2`}>
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className={`p-1.5 rounded-xl border flex-shrink-0 ${styles.iconColor}`}>
            {ICON_MAP[data.icon] || <Zap className="w-4 h-4" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5">
              <h4 className="text-xs font-bold text-white truncate leading-tight">
                {data.label || data.name}
              </h4>
            </div>
            <div className="flex items-center gap-1 mt-0.5">
              <span className={`text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border ${styles.badgeBg} ${styles.badge}`}>
                {CATEGORY_LABELS[cat] || cat}
              </span>
              <span className="text-[9px] text-slate-500 font-mono truncate max-w-[100px]">
                {data.type}
              </span>
            </div>
          </div>
        </div>

        {/* Action icons on node header */}
        <div className="flex items-center gap-0.5 nodrag">
          <button
            onClick={(e) => {
              e.stopPropagation();
              openInspector(id);
            }}
            title="Configure tool options"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              duplicateNode(id);
            }}
            title="Duplicate node"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteNode(id);
            }}
            title="Remove node"
            className="p-1 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Execution Status Bar ── */}
      {execStatus && (
        <div className={`px-3 py-1 flex items-center justify-between text-[10px] font-mono border-b ${
          execStatus === "success" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
          execStatus === "failed" ? "bg-red-500/10 text-red-400 border-red-500/20" :
          "bg-blue-500/10 text-blue-400 border-blue-500/20 animate-pulse"
        }`}>
          <div className="flex items-center gap-1.5">
            {execStatus === "success" && <CheckCircle2 className="w-3.5 h-3.5" />}
            {execStatus === "failed" && <AlertCircle className="w-3.5 h-3.5" />}
            {execStatus === "running" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span className="capitalize">{execStatus}</span>
          </div>
          {data._duration && <span>{data._duration}ms</span>}
        </div>
      )}

      {/* ── Node Body with Flowise-Style Inline Controls ── */}
      <div className="p-3.5 space-y-2.5">
        {/* Inline Selects (e.g. Method, Model, Platform, Operator) */}
        {inlineSelects.map((f: any) => (
          <div key={f.key} className="space-y-1 nodrag">
            <label className="text-[10px] font-semibold text-slate-400 flex items-center justify-between">
              <span>{f.label}</span>
              {f.required && <span className="text-red-400">*</span>}
            </label>
            <select
              value={config[f.key] ?? f.default ?? ""}
              onChange={(e) => updateNodeConfig(id, { [f.key]: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none transition-colors"
            >
              {f.options?.map((opt: any) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        ))}

        {/* Inline Text Input (e.g. URL, Variable Name, Trigger Label) */}
        {inlineTextField && (
          <div className="space-y-1 nodrag">
            <label className="text-[10px] font-semibold text-slate-400 flex items-center justify-between">
              <span>{inlineTextField.label}</span>
              <span className="text-[9px] font-mono text-slate-500">{"{{vars}}"}</span>
            </label>
            <input
              type="text"
              value={config[inlineTextField.key] ?? inlineTextField.default ?? ""}
              onChange={(e) => updateNodeConfig(id, { [inlineTextField.key]: e.target.value })}
              placeholder={inlineTextField.placeholder || `Enter ${inlineTextField.label.toLowerCase()}...`}
              className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none font-mono transition-colors placeholder:text-slate-600"
            />
          </div>
        )}

        {/* Inline Textarea Preview (e.g. Prompt or Template) */}
        {inlineTextarea && (
          <div className="space-y-1 nodrag">
            <label className="text-[10px] font-semibold text-slate-400 flex items-center justify-between">
              <span>{inlineTextarea.label}</span>
              <span className="text-[9px] font-mono text-slate-500">{"{{trigger.payload}}"}</span>
            </label>
            <textarea
              rows={2}
              value={config[inlineTextarea.key] ?? inlineTextarea.default ?? ""}
              onChange={(e) => updateNodeConfig(id, { [inlineTextarea.key]: e.target.value })}
              placeholder={inlineTextarea.placeholder || "Enter prompt template or text..."}
              className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none font-mono transition-colors resize-none placeholder:text-slate-600 leading-snug"
            />
          </div>
        )}

        {/* Expand / Options Drawer Trigger */}
        <button
          onClick={() => openInspector(id)}
          className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-[11px] text-slate-300 border border-slate-700/60 hover:border-slate-600 transition-all group nodrag"
        >
          <span className="flex items-center gap-1.5">
            <SlidersHorizontal className="w-3 h-3 text-indigo-400" />
            <span className="font-medium">Edit Tool Options</span>
          </span>
          <span className="text-[9px] font-mono text-slate-500 group-hover:text-slate-300">
            {Object.keys(config).length} configured →
          </span>
        </button>
      </div>

      {/* ── Right Output Handles ── */}
      {data.type === "logic_condition" ? (
        <>
          <div className="absolute -right-3 top-[38%] flex items-center group">
            <Handle
              type="source"
              position={Position.Right}
              id="true"
              className="!w-3 !h-3 !bg-emerald-500 !border-2 !border-slate-900"
            />
            <span className="hidden group-hover:block absolute right-4 px-1.5 py-0.5 rounded bg-slate-950 text-[9px] font-mono text-emerald-400 whitespace-nowrap shadow border border-slate-800 pointer-events-none">
              True
            </span>
          </div>
          <div className="absolute -right-3 top-[62%] flex items-center group">
            <Handle
              type="source"
              position={Position.Right}
              id="false"
              className="!w-3 !h-3 !bg-red-500 !border-2 !border-slate-900"
            />
            <span className="hidden group-hover:block absolute right-4 px-1.5 py-0.5 rounded bg-slate-950 text-[9px] font-mono text-red-400 whitespace-nowrap shadow border border-slate-800 pointer-events-none">
              False
            </span>
          </div>
        </>
      ) : (
        <div className="absolute -right-3 top-1/2 -translate-y-1/2 flex items-center group">
          <Handle
            type="source"
            position={Position.Right}
            className={`!w-3 !h-3 !border-2 ${styles.handleColor}`}
          />
          <span className="hidden group-hover:block absolute right-4 px-1.5 py-0.5 rounded bg-slate-950 text-[9px] font-mono text-slate-300 whitespace-nowrap shadow border border-slate-800 pointer-events-none">
            Output
          </span>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Main Workflow Builder Component
// ─────────────────────────────────────────────────────────────────────

function WorkflowBuilderInner() {
  const params = useParams();
  const workflowId = params?.id as string;
  const router = useRouter();
  const { screenToFlowPosition, fitView, setCenter } = useReactFlow();
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
  const [allNodesList, setAllNodesList] = useState<any[]>([]);

  // ── Modals & Drawers ──
  const [addToolsModalOpen, setAddToolsModalOpen] = useState(false);
  const [toolSearchQuery, setToolSearchQuery] = useState("");
  const [selectedToolCategory, setSelectedToolCategory] = useState<string>("all");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // ── Bottom Panel (Logs / Validation / Variables) ──
  const [bottomTab, setBottomTab] = useState<"logs" | "validation" | "variables">("validation");
  const [bottomOpen, setBottomOpen] = useState(false);

  // ── Validation & Execution ──
  const [validation, setValidation] = useState<any>(null);
  const [currentExec, setCurrentExec] = useState<any>(null);
  const [execNodeStatuses, setExecNodeStatuses] = useState<Record<string, any>>({});

  // ── Step Testing State (Inside Inspector) ──
  const [testingStep, setTestingStep] = useState(false);
  const [stepTestResult, setStepTestResult] = useState<any>(null);

  // ── Left Sidebar (Collapsible Quick Palette) ──
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  // Node actions passed to each custom node
  const updateNodeConfig = useCallback((nodeId: string, newConfig: Record<string, any>) => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === nodeId
          ? {
              ...n,
              data: {
                ...n.data,
                config: { ...((n.data as any).config || {}), ...newConfig },
              },
            }
          : n
      )
    );
  }, []);

  const deleteNode = useCallback((nodeId: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    setSelectedNodeId((prev) => (prev === nodeId ? null : prev));
  }, []);

  const duplicateNode = useCallback((nodeId: string) => {
    setNodes((nds) => {
      const source = nds.find((n) => n.id === nodeId);
      if (!source) return nds;
      const newId = `node_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
      const cloned: Node = {
        ...source,
        id: newId,
        position: { x: source.position.x + 40, y: source.position.y + 40 },
        selected: true,
        data: {
          ...source.data,
          id: newId,
          label: `${(source.data as any).label || (source.data as any).name} (Copy)`,
          config: JSON.parse(JSON.stringify((source.data as any).config || {})),
        },
      };
      return [...nds.map((n) => ({ ...n, selected: false })), cloned];
    });
    toast.success("Node duplicated");
  }, [toast]);

  const openInspector = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);

  const nodeActions = useMemo(
    () => ({
      updateNodeConfig,
      deleteNode,
      duplicateNode,
      openInspector,
    }),
    [updateNodeConfig, deleteNode, duplicateNode, openInspector]
  );

  // Define nodeTypes memoized
  const nodeTypes = useMemo(() => ({
    flowiseNode: FlowiseNode,
    pravahNode: FlowiseNode, // backward compatible with existing saved data
  }), []);

  // ── Load workflow + node registry (ONLY re-runs if workflowId changes) ──
  useEffect(() => {
    if (!workflowId) return;
    Promise.all([
      fetchApi(`/workflows/${workflowId}`),
      fetchApi("/workflows/node-registry"),
    ])
      .then(([wf, registry]: [any, any]) => {
        setWorkflow(wf);
        setWfName(wf.name);
        const byCat = registry.by_category || {};
        setNodeRegistry(byCat);
        const flattened = Object.values(byCat).flat() as any[];
        setAllNodesList(flattened);

        const nodeDefMap = new Map(flattened.map((nd) => [nd.id, nd]));

        setNodes(
          (wf.nodes || []).map((n: any) => {
            const nodeDef = nodeDefMap.get(n.type);
            return {
              id: n.id,
              type: "flowiseNode",
              position: n.position || { x: 100, y: 100 },
              data: {
                id: n.id,
                name: n.name,
                label: n.label || n.name,
                type: n.type,
                category: n.category || nodeDef?.category || "utility",
                config: n.config || {},
                icon: n.icon || nodeDef?.icon,
                color: n.color || nodeDef?.color,
                nodeDef: nodeDef,
              },
            };
          })
        );

        setEdges(
          (wf.edges || []).map((e: any) => ({
            id: e.id || `${e.source}-${e.target}`,
            source: e.source,
            target: e.target,
            sourceHandle: e.sourceHandle || null,
            targetHandle: e.targetHandle || null,
            animated: true,
            style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.8 },
          }))
        );
      })
      .catch(() => toast.error("Failed to load workflow"))
      .finally(() => setLoading(false));
  }, [workflowId]);

  // ── ReactFlow event handlers ──
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
          style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.8 },
        },
        eds
      )
    );
  }, []);

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNodeId(node.id);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // ── Add Node by Def (from click or drag) ──
  const addNodeToCanvas = useCallback(
    (nodeDef: any, targetPos?: { x: number; y: number }) => {
      const newId = `node_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
      const position = targetPos || {
        x: 250 + Math.random() * 80,
        y: 180 + Math.random() * 80,
      };

      // Construct default initial config based on schema
      const initialConfig: Record<string, any> = {};
      for (const f of nodeDef.config_schema || []) {
        if (f.default !== undefined) {
          initialConfig[f.key] = f.default;
        }
      }

      const newNode: Node = {
        id: newId,
        type: "flowiseNode",
        position,
        data: {
          id: newId,
          name: nodeDef.name,
          label: nodeDef.name,
          type: nodeDef.id,
          category: nodeDef.category || "utility",
          config: initialConfig,
          icon: nodeDef.icon,
          color: nodeDef.color,
          nodeDef: nodeDef,
        },
      };

      setNodes((nds) => [...nds, newNode]);
      setSelectedNodeId(newId);
      toast.success(`Added ${nodeDef.name}`);
    },
    [toast]
  );

  // Drag & drop onto canvas
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
      addNodeToCanvas(nodeTypeDef, position);
    },
    [screenToFlowPosition, addNodeToCanvas]
  );

  // ── Auto-layout (Tidy Up) ──
  function handleAutoLayout() {
    setNodes((nds) => {
      const spacingX = 360;
      const spacingY = 220;
      return nds.map((node, idx) => {
        const col = idx % 3;
        const row = Math.floor(idx / 3);
        return {
          ...node,
          position: { x: 100 + col * spacingX, y: 100 + row * spacingY },
        };
      });
    });
    setTimeout(() => fitView({ padding: 0.2 }), 50);
    toast.success("Nodes rearranged");
  }

  // ── Save Workflow ──
  async function handleSave() {
    setSaving(true);
    try {
      const payload = {
        name: wfName || "Untitled Workflow",
        nodes: nodes.map((n) => {
          const d = (n.data || {}) as any;
          return {
            id: n.id,
            type: d.type || (n.type === "flowiseNode" ? "utility" : n.type) || "utility",
            name: d.name || d.label || "Node",
            label: d.label || d.name || "Node",
            category: d.category || "utility",
            config: d.config || {},
            position: {
              x: Number(n.position?.x) || 100,
              y: Number(n.position?.y) || 100,
            },
            icon: d.icon || null,
            color: d.color || null,
          };
        }),
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
      throw e;
    } finally {
      setSaving(false);
    }
  }

  // ── Validate Workflow ──
  async function handleValidate() {
    try {
      await handleSave();
      const result = (await fetchApi(`/workflows/${workflowId}/validate`, {
        method: "POST",
      })) as any;
      setValidation(result);
      setBottomTab("validation");
      setBottomOpen(true);
      if (result.valid) toast.success("Workflow is valid ✓");
    } catch (e: any) {
      toast.error(e.message || "Validation failed");
    }
  }

  // ── Publish Workflow ──
  async function handlePublish() {
    setPublishing(true);
    try {
      await handleSave();
      const result = (await fetchApi(`/workflows/${workflowId}/publish`, {
        method: "POST",
      })) as any;
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

  // ── Execute Workflow ──
  async function handleRun() {
    setExecuting(true);
    setExecNodeStatuses({});
    setBottomTab("logs");
    setBottomOpen(true);
    try {
      await handleSave();
      const result = (await fetchApi(`/workflows/${workflowId}/execute`, {
        method: "POST",
        body: JSON.stringify({ trigger_source: "manual", trigger_payload: {} }),
      })) as any;
      setCurrentExec(result);
      toast.success(`Execution started (${result.execution_id.slice(0, 8)})`);

      const evtSource = new EventSource(
        `/api/v1/workflows/${workflowId}/executions/${result.execution_id}/stream`
      );
      evtSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        setCurrentExec(data);
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

  // Selected node & definition
  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null;
  const selectedNodeDef = selectedNode
    ? allNodesList.find((nd) => nd.id === selectedNode.data.type) || selectedNode.data.nodeDef
    : null;

  // Filtered tools in the "Add Tools / Nodes" library modal
  const filteredTools = useMemo(() => {
    return allNodesList.filter((n) => {
      const matchesCat =
        selectedToolCategory === "all" ||
        (selectedToolCategory === "tools"
          ? ["utility", "data"].includes(n.category)
          : n.category === selectedToolCategory);
      const matchesSearch =
        toolSearchQuery === "" ||
        n.name.toLowerCase().includes(toolSearchQuery.toLowerCase()) ||
        n.description?.toLowerCase().includes(toolSearchQuery.toLowerCase()) ||
        n.id.toLowerCase().includes(toolSearchQuery.toLowerCase());
      return matchesCat && matchesSearch;
    });
  }, [allNodesList, selectedToolCategory, toolSearchQuery]);

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span className="text-sm">Loading Flowise workflow canvas...</span>
        </div>
      </div>
    );
  }

  return (
    <NodeActionsContext.Provider value={nodeActions}>
      <div className="h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* ─────────────────────────────────────────────────────────────
          Top Navigation & Actions Bar
         ───────────────────────────────────────────────────────────── */}
      <div className="h-14 flex-shrink-0 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 flex items-center px-4 gap-3 z-30 justify-between">
        {/* Left: Back + Workflow Name */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => router.push("/dashboard/workflows")}
            className="text-slate-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-slate-800"
            title="Back to workflows"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="w-px h-5 bg-slate-800" />

          <div className="flex items-center gap-2 min-w-0">
            <input
              value={wfName}
              onChange={(e) => setWfName(e.target.value)}
              className="bg-transparent text-white font-bold text-sm focus:outline-none border-b border-transparent hover:border-slate-700 focus:border-indigo-500 pb-0.5 transition-colors min-w-[160px] max-w-sm truncate"
              placeholder="Workflow title..."
            />
            {workflow && (
              <span
                className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${
                  workflow.status === "published"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                {workflow.status}
                {workflow.published_version && ` v${workflow.published_version}`}
              </span>
            )}
          </div>
        </div>

        {/* Center: Prominent Add Node / Tool Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAddToolsModalOpen(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/25 transition-all active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>Add Node / Tool</span>
          </button>

          <button
            onClick={handleAutoLayout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700/80 transition-colors"
            title="Auto-organize workflow canvas"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Organize</span>
          </button>
        </div>

        {/* Right: Validation, Save, Publish, Run */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleValidate}
            className="text-slate-400 hover:text-white text-xs px-3 py-1.5 rounded-xl border border-slate-800 hover:border-slate-700 hover:bg-slate-800/60 transition-all flex items-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Validate</span>
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            className="text-slate-300 hover:text-white text-xs px-3 py-1.5 rounded-xl border border-slate-800 hover:border-slate-700 hover:bg-slate-800 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Save</span>
          </button>

          <button
            onClick={handlePublish}
            disabled={publishing || saving}
            className="text-indigo-300 hover:text-white text-xs px-3 py-1.5 rounded-xl border border-indigo-500/40 hover:border-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            {publishing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
            <span>Publish</span>
          </button>

          <button
            onClick={handleRun}
            disabled={executing || workflow?.status !== "published"}
            className="text-white text-xs px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 transition-all flex items-center gap-1.5 shadow-lg shadow-emerald-600/20 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            title={workflow?.status !== "published" ? "Publish the workflow first before executing" : "Run workflow now"}
          >
            {executing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            <span>Run</span>
          </button>

          <button
            onClick={() => router.push(`/dashboard/workflows/${workflowId}/executions`)}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            title="Execution History"
          >
            <History className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          Main Workspace Area
         ───────────────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* ── Collapsible Left Quick Palette ── */}
        <div
          className={`flex-shrink-0 bg-slate-900/95 border-r border-slate-800 flex flex-col transition-all duration-200 z-10 ${
            sidebarOpen ? "w-64" : "w-0 overflow-hidden border-0"
          }`}
        >
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Wrench className="w-3.5 h-3.5 text-indigo-400" />
              <span>Tool Library</span>
            </span>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-slate-500 hover:text-slate-300 p-1 rounded-md hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>

          <div className="overflow-y-auto flex-1 p-2.5 space-y-4">
            {Object.entries(nodeRegistry).map(([category, catNodes]) => {
              const styles = CATEGORY_STYLES[category] || CATEGORY_STYLES.utility;
              return (
                <div key={category} className="space-y-1.5">
                  <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${styles.badge}`} />
                    <span>{CATEGORY_LABELS[category] || category}</span>
                    <span className="ml-auto text-[9px] text-slate-600 font-mono">({catNodes.length})</span>
                  </div>

                  <div className="space-y-1">
                    {catNodes.map((nodeType: any) => (
                      <div
                        key={nodeType.id}
                        draggable
                        onDragStart={(e) => {
                          e.dataTransfer.setData("application/pravah-node", JSON.stringify(nodeType));
                          e.dataTransfer.effectAllowed = "move";
                        }}
                        onClick={() => addNodeToCanvas(nodeType)}
                        className={`
                          px-2.5 py-2 rounded-xl border cursor-pointer hover:scale-[1.02]
                          bg-slate-950/70 hover:bg-slate-800/90 transition-all flex items-center gap-2.5 group
                          ${styles.border}
                        `}
                      >
                        <div className={`p-1.5 rounded-lg border flex-shrink-0 ${styles.iconColor}`}>
                          {ICON_MAP[nodeType.icon] || <Zap className="w-3.5 h-3.5" />}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-slate-200 truncate group-hover:text-white">
                            {nodeType.name}
                          </p>
                          <p className="text-[10px] text-slate-500 truncate">
                            {nodeType.description}
                          </p>
                        </div>
                        <Plus className="w-3.5 h-3.5 text-slate-600 group-hover:text-indigo-400 ml-auto flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Sidebar Toggle When Hidden */}
        {!sidebarOpen && (
          <button
            onClick={() => setSidebarOpen(true)}
            className="absolute left-2 top-3 z-20 px-2.5 py-1.5 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 rounded-xl shadow-lg flex items-center gap-1.5 text-xs text-slate-300 transition-colors"
          >
            <ChevronRight className="w-3.5 h-3.5" />
            <span>Tools</span>
          </button>
        )}

        {/* ── Center: Infinite Canvas ── */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <div
            ref={reactFlowWrapper}
            className="flex-1 w-full h-full"
            onDragOver={onDragOver}
            onDrop={onDrop}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
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
              minZoom={0.15}
              maxZoom={2.0}
              className="bg-[#090d16]"
              // 100% UNBRANDED - HIDE ALL ATTRIBUTION & WATERMARKS
              proOptions={{ hideAttribution: true }}
              defaultEdgeOptions={{
                animated: true,
                style: { stroke: "#6366f1", strokeWidth: 2, opacity: 0.8 },
              }}
            >
              {/* Dot Grid Background */}
              <Background variant={BackgroundVariant.Dots} gap={24} size={1.2} color="#1e293b" />

              {/* Custom Dark Theme Canvas Controls */}
              <Controls
                className="!bg-slate-900/90 !border-slate-800 !rounded-xl !overflow-hidden !shadow-2xl [&_button]:!bg-slate-900 [&_button]:!text-slate-400 [&_button:hover]:!bg-slate-800 [&_button:hover]:!text-white [&_button]:!border-b [&_button]:!border-slate-800"
              />

              {/* Collapsible MiniMap */}
              <MiniMap
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(51, 65, 85, 0.6)",
                  borderRadius: "12px",
                }}
                nodeColor={(n: any) => {
                  const cat = n.data?.category;
                  if (cat === "trigger") return "#10b981";
                  if (cat === "ai") return "#a855f7";
                  if (cat === "social") return "#06b6d4";
                  if (cat === "logic") return "#f59e0b";
                  return "#3b82f6";
                }}
                nodeStrokeWidth={2}
              />
            </ReactFlow>
          </div>

          {/* ── Bottom Drawer (Execution Logs / Validation / Variables) ── */}
          <div
            className={`border-t border-slate-800 bg-slate-900/95 backdrop-blur-xl transition-all duration-200 flex flex-col z-20 ${
              bottomOpen ? "h-56" : "h-9"
            }`}
          >
            {/* Header bar */}
            <div className="h-9 flex items-center px-4 gap-2 bg-slate-900 border-b border-slate-800 text-xs select-none">
              <button
                onClick={() => {
                  setBottomTab("validation");
                  setBottomOpen(true);
                }}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                  bottomTab === "validation" && bottomOpen
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Validation</span>
                {validation && (
                  <span
                    className={`ml-1 px-1.5 py-0.2 rounded-full text-[9px] ${
                      validation.valid ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"
                    }`}
                  >
                    {validation.valid ? "0" : validation.errors?.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => {
                  setBottomTab("logs");
                  setBottomOpen(true);
                }}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                  bottomTab === "logs" && bottomOpen
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                <span>Execution Logs</span>
                {executing && <Loader2 className="w-3 h-3 animate-spin text-blue-400 ml-1" />}
              </button>

              <button
                onClick={() => {
                  setBottomTab("variables");
                  setBottomOpen(true);
                }}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1.5 ${
                  bottomTab === "variables" && bottomOpen
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Variable className="w-3.5 h-3.5 text-amber-400" />
                <span>Variables</span>
              </button>

              <div className="flex-1" />

              <button
                onClick={() => setBottomOpen((v) => !v)}
                className="text-slate-500 hover:text-slate-300 p-1"
                title={bottomOpen ? "Collapse panel" : "Expand panel"}
              >
                {bottomOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
              </button>
            </div>

            {/* Content */}
            {bottomOpen && (
              <div className="flex-1 overflow-y-auto p-3 text-xs space-y-2">
                {bottomTab === "validation" && (
                  validation ? (
                    <div className="space-y-2">
                      <div className={`flex items-center gap-2 font-bold ${validation.valid ? "text-emerald-400" : "text-red-400"}`}>
                        {validation.valid ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                        <span>{validation.valid ? "Workflow is valid and ready to execute." : `${validation.errors?.length} validation error(s) found:`}</span>
                      </div>
                      {validation.errors?.map((err: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-red-300 bg-red-500/10 border border-red-500/20 rounded-lg px-2.5 py-1.5">
                          <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                          <span>{err}</span>
                        </div>
                      ))}
                      {validation.warnings?.map((w: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-amber-300 bg-amber-500/10 border border-amber-500/20 rounded-lg px-2.5 py-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                          <span>{w}</span>
                        </div>
                      ))}
                      <div className="text-slate-500 text-[11px] pt-1 font-mono">
                        {validation.node_count} nodes · {validation.edge_count} connections · {validation.trigger_count} trigger(s)
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-500">Click &quot;Validate&quot; in the top bar to inspect workflow structure.</p>
                  )
                )}

                {bottomTab === "logs" && (
                  currentExec ? (
                    <div className="space-y-2">
                      <div className={`font-semibold flex items-center gap-2 ${
                        currentExec.status === "completed" ? "text-emerald-400" :
                        currentExec.status === "failed" ? "text-red-400" : "text-blue-400"
                      }`}>
                        {currentExec.status === "running" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                        <span>Execution ID: <span className="font-mono">{currentExec.execution_id?.slice(0, 8) || currentExec.id?.slice(0, 8)}</span></span>
                        <span className="capitalize px-2 py-0.5 rounded bg-slate-800 text-[10px]">{currentExec.status}</span>
                      </div>
                      <div className="space-y-1">
                        {(currentExec.node_executions || []).map((ne: any) => (
                          <div key={ne.node_key} className="flex items-center gap-2 text-slate-300 bg-slate-950/80 border border-slate-800 rounded-lg px-2.5 py-1.5">
                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                              ne.status === "success" ? "bg-emerald-400" :
                              ne.status === "failed" ? "bg-red-400" :
                              ne.status === "running" ? "bg-blue-400 animate-pulse" : "bg-slate-600"
                            }`} />
                            <span className="font-semibold text-white">{ne.node_name}</span>
                            <span className="text-slate-500 font-mono text-[10px]">({ne.node_type})</span>
                            {ne.duration_ms && <span className="ml-auto text-slate-500 font-mono">{ne.duration_ms}ms</span>}
                            {ne.error_message && (
                              <span className="text-red-400 text-xs ml-2">{ne.error_message}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-slate-500">Run the workflow to stream real-time node logs and outputs.</p>
                  )
                )}

                {bottomTab === "variables" && (
                  <div className="space-y-2 text-slate-400 text-xs">
                    <p>
                      Dynamic tokens can be inserted into any tool, URL, or prompt using handlebars syntax:
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-indigo-400">{"{{trigger.payload.text}}"}</span>
                        <p className="text-slate-500 text-[10px] mt-0.5">Payload passed by the starting trigger</p>
                      </div>
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-indigo-400">{"{{nodes.node_key.output}}"}</span>
                        <p className="text-slate-500 text-[10px] mt-0.5">Output returned by a previous node</p>
                      </div>
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-indigo-400">{"{{vars.variable_name}}"}</span>
                        <p className="text-slate-500 text-[10px] mt-0.5">Workflow environment variable</p>
                      </div>
                      <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                        <span className="text-indigo-400">{"{{org.name}}"}</span>
                        <p className="text-slate-500 text-[10px] mt-0.5">Current active organisation context</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Right Panel: Flowise-Style Tool Inspector ── */}
        {selectedNode && (() => {
          const nodeData = (selectedNode.data || {}) as Record<string, any>;
          return (
          <div className="w-84 md:w-96 flex-shrink-0 bg-slate-900 border-l border-slate-800 flex flex-col overflow-hidden z-20 shadow-2xl">
            {/* Inspector Header */}
            <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex-shrink-0">
                  {ICON_MAP[nodeData.icon] || <Wrench className="w-4 h-4" />}
                </div>
                <div className="min-w-0">
                  <h3 className="text-xs font-bold text-white truncate">
                    {String(nodeData.label || nodeData.name || "Node Inspector")}
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">
                    {String(nodeData.type || "")}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedNodeId(null)}
                className="text-slate-500 hover:text-slate-300 p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Inspector Scrollable Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Display Label */}
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Node Label
                </label>
                <input
                  type="text"
                  value={(selectedNode.data.label as string) || ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    setNodes((nds) =>
                      nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, label: val } } : n))
                    );
                  }}
                  className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none transition-colors"
                  placeholder="Custom name for this step..."
                />
              </div>

              {/* Dynamic Variables Inserter Bar */}
              <div className="space-y-1.5 p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-[10px] font-semibold text-slate-400 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-indigo-400" />
                  <span>Insert Variable Pill</span>
                </span>
                <div className="flex flex-wrap gap-1">
                  {["{{trigger.payload}}", "{{trigger.text}}", "{{vars.key}}", "{{org.id}}"].map((pill) => (
                    <button
                      key={pill}
                      type="button"
                      onClick={() => {
                        // Copy to clipboard or notify
                        navigator.clipboard?.writeText(pill);
                        toast.success(`Copied ${pill}`);
                      }}
                      className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 transition-colors"
                    >
                      {pill}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic Schema Fields */}
              {selectedNodeDef?.config_schema?.map((field: any) => {
                const curVal = (selectedNode.data.config as any)?.[field.key] ?? field.default ?? "";

                return (
                  <div key={field.key} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                        <span>{field.label}</span>
                        {field.required && <span className="text-red-400">*</span>}
                      </label>
                      <span className="text-[9px] font-mono text-slate-600">{field.field_type}</span>
                    </div>

                    {field.description && (
                      <p className="text-[10px] text-slate-500 leading-tight">{field.description}</p>
                    )}

                    {/* Field Type: Select */}
                    {field.field_type === "select" ? (
                      <select
                        value={curVal}
                        onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none transition-colors"
                      >
                        {field.options?.map((opt: any) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    ) : field.field_type === "textarea" || field.field_type === "expression" ? (
                      <textarea
                        rows={4}
                        value={curVal}
                        onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                        placeholder={field.placeholder || "Enter expression or template..."}
                        className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-2 text-xs text-white focus:outline-none font-mono transition-colors resize-none placeholder:text-slate-600 leading-relaxed"
                      />
                    ) : field.field_type === "boolean" ? (
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => updateNodeConfig(selectedNode.id, { [field.key]: !curVal })}
                          className={`w-9 h-5 rounded-full transition-colors relative ${
                            curVal ? "bg-indigo-600" : "bg-slate-700"
                          }`}
                        >
                          <span
                            className={`block w-3.5 h-3.5 rounded-full bg-white transition-transform ${
                              curVal ? "translate-x-4.5" : "translate-x-1"
                            }`}
                          />
                        </button>
                        <span className="text-xs text-slate-300">{curVal ? "Enabled" : "Disabled"}</span>
                      </div>
                    ) : field.field_type === "number" ? (
                      <input
                        type="number"
                        value={curVal}
                        onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: Number(e.target.value) })}
                        min={field.min_value}
                        max={field.max_value}
                        placeholder={field.placeholder}
                        className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none font-mono"
                      />
                    ) : (
                      <input
                        type="text"
                        value={curVal}
                        onChange={(e) => updateNodeConfig(selectedNode.id, { [field.key]: e.target.value })}
                        placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}...`}
                        className="w-full bg-slate-950 border border-slate-700 hover:border-slate-600 focus:border-indigo-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none font-mono placeholder:text-slate-600"
                      />
                    )}
                  </div>
                );
              })}

              {/* Node ID & Details */}
              <div className="pt-3 border-t border-slate-800 text-[10px] space-y-1 font-mono text-slate-500">
                <div className="flex justify-between">
                  <span>Node ID</span>
                  <span className="text-slate-400">{selectedNode.id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Category</span>
                  <span className="text-slate-400 capitalize">{String(nodeData.category || "")}</span>
                </div>
              </div>

              {/* Duplicate & Delete Actions */}
              <div className="pt-2 flex gap-2">
                <button
                  onClick={() => duplicateNode(selectedNode.id)}
                  className="flex-1 py-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>Duplicate</span>
                </button>
                <button
                  onClick={() => deleteNode(selectedNode.id)}
                  className="flex-1 py-1.5 rounded-lg border border-red-500/30 hover:bg-red-500/10 text-red-400 text-xs flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Remove</span>
                </button>
              </div>
            </div>
          </div>
          );
        })()}
      </div>

      {/* ─────────────────────────────────────────────────────────────
          Flowise-Style "Add Nodes & Tools" Modal / Dialog
         ───────────────────────────────────────────────────────────── */}
      {addToolsModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header & Search */}
            <div className="p-4 border-b border-slate-800 bg-slate-900/90 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
                    <Plus className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white">Add Nodes & Tools</h3>
                    <p className="text-[11px] text-slate-400">
                      Select any tool, agent, trigger, or logic step to insert into your canvas.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setAddToolsModalOpen(false)}
                  className="text-slate-500 hover:text-slate-300 p-1.5 rounded-lg hover:bg-slate-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Search input */}
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  autoFocus
                  value={toolSearchQuery}
                  onChange={(e) => setToolSearchQuery(e.target.value)}
                  placeholder="Search tools, triggers, AI models (e.g. HTTP, Claude, Tweet, Webhook)..."
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-xl pl-9 pr-3 py-2 text-xs text-white focus:outline-none transition-colors"
                />
              </div>

              {/* Category Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 no-scrollbar">
                {[
                  { id: "all", label: "All Nodes" },
                  { id: "tools", label: "🛠️ Tools & APIs" },
                  { id: "ai", label: "🧠 AI & LLM" },
                  { id: "social", label: "🌐 Social" },
                  { id: "trigger", label: "⚡ Triggers" },
                  { id: "logic", label: "🔀 Logic" },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedToolCategory(tab.id)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                      selectedToolCategory === tab.id
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Modal Node Cards Grid */}
            <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {filteredTools.map((nodeType: any) => {
                const styles = CATEGORY_STYLES[nodeType.category] || CATEGORY_STYLES.utility;
                return (
                  <div
                    key={nodeType.id}
                    onClick={() => {
                      addNodeToCanvas(nodeType);
                      setAddToolsModalOpen(false);
                    }}
                    className={`
                      p-3 rounded-xl border cursor-pointer group transition-all
                      bg-slate-950/70 hover:bg-slate-800/80 hover:scale-[1.01]
                      ${styles.border} flex items-start gap-3
                    `}
                  >
                    <div className={`p-2 rounded-xl border flex-shrink-0 mt-0.5 ${styles.iconColor}`}>
                      {ICON_MAP[nodeType.icon] || <Zap className="w-4 h-4" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5">
                        <h4 className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors truncate">
                          {nodeType.name}
                        </h4>
                        <span className={`text-[8px] uppercase font-bold px-1 rounded border ${styles.badgeBg} ${styles.badge}`}>
                          {nodeType.category}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                        {nodeType.description}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="px-2 py-1 rounded-lg bg-indigo-600/20 text-indigo-300 text-[10px] font-semibold border border-indigo-500/30 group-hover:bg-indigo-600 group-hover:text-white transition-colors flex items-center gap-1 flex-shrink-0"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add</span>
                    </button>
                  </div>
                );
              })}

              {filteredTools.length === 0 && (
                <div className="col-span-2 py-12 text-center text-slate-500">
                  <HelpCircle className="w-8 h-8 mx-auto text-slate-600 mb-2" />
                  <p className="text-sm font-medium">No tools found matching &quot;{toolSearchQuery}&quot;</p>
                  <p className="text-xs text-slate-600 mt-1">Try searching for &quot;HTTP&quot;, &quot;AI&quot;, &quot;Tweet&quot;, or &quot;Condition&quot;</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      </div>
    </NodeActionsContext.Provider>
  );
}

export default function WorkflowBuilderPage() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderInner />
    </ReactFlowProvider>
  );
}
