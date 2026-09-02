"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Node,
  Edge,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
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
  Play,
  Save,
  Plus,
  Bot,
  Sparkles,
  Share2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Layers,
  History,
  X,
  ChevronRight,
} from "lucide-react";

// Custom React Flow Node Component
function CustomWorkflowNode({ data }: any) {
  const isTrigger = data.category === "trigger";
  const isAI = data.category === "ai";
  const isAction = data.category === "social";
  const isLogic = data.category === "logic";

  return (
    <div
      className={`min-w-[180px] p-3 rounded-xl border bg-slate-900/90 backdrop-blur-md shadow-xl transition-all ${
        isTrigger
          ? "border-emerald-500/50 shadow-emerald-500/10"
          : isAI
          ? "border-purple-500/50 shadow-purple-500/10"
          : isAction
          ? "border-cyan-500/50 shadow-cyan-500/10"
          : "border-slate-700 shadow-slate-900/50"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-indigo-500 w-2.5 h-2.5" />

      <div className="flex items-center gap-2 pb-1.5 border-b border-slate-800">
        {isTrigger && <Clock className="w-3.5 h-3.5 text-emerald-400" />}
        {isAI && <Bot className="w-3.5 h-3.5 text-purple-400" />}
        {isAction && <Share2 className="w-3.5 h-3.5 text-cyan-400" />}
        {isLogic && <Layers className="w-3.5 h-3.5 text-amber-400" />}
        <span className="text-[11px] font-bold text-slate-200 truncate">{data.name}</span>
      </div>

      <div className="pt-1.5 text-[10px] text-slate-400">
        Type: <span className="font-mono text-slate-300">{data.type}</span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-indigo-500 w-2.5 h-2.5" />
    </div>
  );
}

const nodeTypes = {
  customNode: CustomWorkflowNode,
};

export default function WorkflowsPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [workflows, setWorkflows] = useState<any[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<any>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Execution & Logs Drawer State
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [executionLogs, setExecutionLogs] = useState<any[]>([]);

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState("");
  const [newWorkflowDesc, setNewWorkflowDesc] = useState("");

  const fetchWorkflows = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const data = await fetchApi<any[]>("/workflows");
      setWorkflows(data);
      if (data.length > 0 && !activeWorkflow) {
        selectWorkflow(data[0]);
      }
    } catch {
      setWorkflows([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, [activeOrg]);

  const selectWorkflow = (wf: any) => {
    setActiveWorkflow(wf);
    const flowNodes: Node[] = (wf.nodes || []).map((n: any) => ({
      id: n.id,
      type: "customNode",
      position: n.position || { x: 250, y: 100 },
      data: {
        id: n.id,
        name: n.name,
        type: n.type,
        category: n.category,
        config: n.config,
      },
    }));

    const flowEdges: Edge[] = (wf.edges || []).map((e: any) => ({
      id: e.id || `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      animated: true,
      style: { stroke: "#6366f1", strokeWidth: 2 },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  };

  const onNodesChange = useCallback(
    (changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (params: any) =>
      setEdges((eds) =>
        addEdge({ ...params, animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } }, eds)
      ),
    []
  );

  const handleAddNode = (category: string, nodeType: string, name: string) => {
    const id = `node-${Date.now()}`;
    const newNode: Node = {
      id,
      type: "customNode",
      position: { x: 250 + nodes.length * 30, y: 150 + nodes.length * 50 },
      data: {
        id,
        name,
        type: nodeType,
        category,
        config: {},
      },
    };
    setNodes((nds) => [...nds, newNode]);
    toast.info("Node Added", `Added ${name} to canvas.`);
  };

  const handleSaveWorkflow = async () => {
    if (!activeWorkflow) return;
    try {
      const payloadNodes = nodes.map((n) => ({
        id: n.id,
        name: n.data.name,
        type: n.data.type,
        category: n.data.category,
        config: n.data.config || {},
        position: n.position,
      }));

      const payloadEdges = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      }));

      await fetchApi("/workflows", {
        method: "POST",
        body: JSON.stringify({
          name: activeWorkflow.name,
          description: activeWorkflow.description,
          is_active: true,
          nodes: payloadNodes,
          edges: payloadEdges,
        }),
      });

      toast.success("Workflow Saved!", "Pipeline configuration updated successfully.");
      fetchWorkflows();
    } catch (err: any) {
      toast.error("Save Failed", err.message || "Failed to save workflow.");
    }
  };

  const handleExecuteWorkflow = async () => {
    if (!activeWorkflow) return;
    setIsExecuting(true);
    try {
      const res = await fetchApi<any>(`/workflows/${activeWorkflow.id}/execute`, {
        method: "POST",
        body: JSON.stringify({ trigger_payload: { source: "web_runner" } }),
      });

      setExecutionResult(res);
      toast.success(
        "Workflow Executed!",
        `Finished in ${res.duration_ms}ms with status: ${res.status}`
      );
    } catch (err: any) {
      toast.error("Execution Failed", err.message || "Pipeline encountered a runtime error.");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleOpenLogs = async () => {
    if (!activeWorkflow) return;
    try {
      const logs = await fetchApi<any[]>(`/workflows/${activeWorkflow.id}/executions`);
      setExecutionLogs(logs);
      setIsLogsOpen(true);
    } catch {
      toast.error("Logs Error", "Could not load execution history.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 h-[calc(100vh-8rem)] flex flex-col">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shrink-0">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <WorkflowIcon className="w-6 h-6 text-indigo-400" /> Visual No-Code Automation Engine
          </h1>
          <p className="text-xs text-slate-400">
            Build autonomous DAG publishing pipelines with AI nodes, conditional logic, and official triggers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" leftIcon={<History className="w-4 h-4" />} onClick={handleOpenLogs}>
            Execution Logs
          </Button>
          <Button variant="secondary" size="sm" leftIcon={<Save className="w-4 h-4" />} onClick={handleSaveWorkflow}>
            Save DAG
          </Button>
          <Button variant="glow" size="sm" leftIcon={<Play className="w-4 h-4" />} onClick={handleExecuteWorkflow} isLoading={isExecuting}>
            Test Run Pipeline
          </Button>
        </div>
      </div>

      {/* Main Canvas + Toolbox Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-0">
        {/* Node Library Toolbox Sidebar */}
        <Card className="lg:col-span-3 p-4 flex flex-col justify-between space-y-4 overflow-y-auto">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-slate-200">Node Toolbox</span>
              <span className="text-[10px] text-slate-500">Click to Add</span>
            </div>

            {/* Triggers */}
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-bold text-emerald-400">1. Triggers</span>
              <div className="space-y-1">
                <button
                  onClick={() => handleAddNode("trigger", "trigger_manual", "Manual Trigger")}
                  className="w-full p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-emerald-500/50 text-left text-xs text-slate-300 flex items-center gap-2 transition-colors"
                >
                  <Clock className="w-3.5 h-3.5 text-emerald-400" /> Manual Launch
                </button>
                <button
                  onClick={() => handleAddNode("trigger", "trigger_schedule", "Daily 9AM Schedule")}
                  className="w-full p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-emerald-500/50 text-left text-xs text-slate-300 flex items-center gap-2 transition-colors"
                >
                  <Clock className="w-3.5 h-3.5 text-emerald-400" /> Cron Schedule
                </button>
              </div>
            </div>

            {/* AI Generation Nodes */}
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-bold text-purple-400">2. AI Intelligence</span>
              <div className="space-y-1">
                <button
                  onClick={() => handleAddNode("ai", "ai_generate_text", "AI Text Writer")}
                  className="w-full p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/50 text-left text-xs text-slate-300 flex items-center gap-2 transition-colors"
                >
                  <Bot className="w-3.5 h-3.5 text-purple-400" /> OpenRouter Text
                </button>
                <button
                  onClick={() => handleAddNode("ai", "ai_generate_image", "AI Creative Banner")}
                  className="w-full p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/50 text-left text-xs text-slate-300 flex items-center gap-2 transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Image Generator
                </button>
              </div>
            </div>

            {/* Actions / Publishing */}
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-bold text-cyan-400">3. Social Distribution</span>
              <div className="space-y-1">
                <button
                  onClick={() => handleAddNode("social", "social_publish_x", "Publish to X")}
                  className="w-full p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 text-left text-xs text-slate-300 flex items-center gap-2 transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5 text-cyan-400" /> Dispatch to X
                </button>
                <button
                  onClick={() => handleAddNode("social", "social_publish_linkedin", "Publish to LinkedIn")}
                  className="w-full p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 text-left text-xs text-slate-300 flex items-center gap-2 transition-colors"
                >
                  <Share2 className="w-3.5 h-3.5 text-cyan-400" /> Dispatch to LinkedIn
                </button>
              </div>
            </div>
          </div>

          {/* Workflow selector */}
          <div className="pt-2 border-t border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Active Workflow</span>
            <p className="text-xs font-bold text-indigo-300 truncate">
              {activeWorkflow?.name || "Daily AI News Broadcast"}
            </p>
          </div>
        </Card>

        {/* React Flow Canvas */}
        <div className="lg:col-span-9 rounded-2xl border border-slate-800 bg-[#060a14] overflow-hidden relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1e293b" gap={20} size={1} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
          </ReactFlow>

          {/* Real-time Execution Inspector Overlay */}
          {executionResult && (
            <div className="absolute bottom-4 right-4 max-w-sm w-full glass-panel rounded-xl p-3 border-indigo-500/40 shadow-2xl z-20 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Execution Result
                </span>
                <button
                  onClick={() => setExecutionResult(null)}
                  className="text-slate-500 hover:text-slate-300"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="space-y-1 text-[11px] text-slate-400">
                <p>Status: <span className="text-emerald-400 font-bold uppercase">{executionResult.status}</span></p>
                <p>Duration: <span className="text-slate-200">{executionResult.duration_ms} ms</span></p>
                <p>Nodes executed: <span className="text-slate-200">{executionResult.node_executions?.length || 0}</span></p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Execution Logs Drawer */}
      <Modal
        isOpen={isLogsOpen}
        onClose={() => setIsLogsOpen(false)}
        title="Pipeline Execution History"
        description="Detailed node-by-node execution traces and error telemetry."
        maxWidth="xl"
      >
        <div className="space-y-3 max-h-[60vh] overflow-y-auto">
          {executionLogs.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-6">No historical runs recorded yet.</p>
          ) : (
            executionLogs.map((log) => (
              <div key={log.id} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={log.status === "completed" ? "success" : "danger"}>
                      {log.status}
                    </Badge>
                    <span className="text-slate-400 text-[11px]">{formatDate(log.started_at)}</span>
                  </div>
                  <span className="font-mono text-[11px] text-indigo-300">{log.duration_ms} ms</span>
                </div>

                <div className="space-y-1 border-t border-slate-800/60 pt-2">
                  {log.node_executions?.map((ne: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>• {ne.node_name} ({ne.node_type})</span>
                      <span className="text-emerald-400 font-mono">{ne.status} ({ne.duration_ms}ms)</span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </Modal>
    </div>
  );
}
