"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import {
  LayoutTemplate,
  ChevronLeft,
  Plus,
  Bot,
  Zap,
  Clock,
  Sparkles,
  Share2,
  GitBranch,
  Loader2,
  CheckCircle2,
} from "lucide-react";

interface WorkflowTemplateItem {
  id: string;
  name: string;
  description?: string;
  category?: string;
  icon?: string;
  color?: string;
  tags?: string[];
  is_admin_template: boolean;
  usage_count: number;
  node_count: number;
  plan_requirements?: string[];
}

const BUILTIN_TEMPLATES = [
  {
    id: "builtin_daily_ai_post",
    name: "AI Daily Social Publisher",
    description: "Generates platform-optimized daily updates on a 9:00 AM schedule, validates char limits and spam patterns, and auto-publishes to connected social accounts.",
    category: "publishing",
    node_count: 4,
    tags: ["AI", "Scheduling", "Auto-Publish"],
    color: "#6366f1",
  },
  {
    id: "builtin_content_approval_gate",
    name: "AI Content Draft & Approval Pipeline",
    description: "Generates weekly topical drafts, requests reviewer approval in the internal workspace queue, and publishes immediately upon approval decision.",
    category: "governance",
    node_count: 5,
    tags: ["AI", "Approvals", "Governance"],
    color: "#f97316",
  },
  {
    id: "builtin_best_time_recommender",
    name: "Smart Peak-Hour Publisher",
    description: "Analyzes past audience engagement signals to pick the optimal posting window, waits until peak time, then broadcasts across multi-channel networks.",
    category: "analytics",
    node_count: 4,
    tags: ["Best Time", "Analytics", "Multi-Channel"],
    color: "#8b5cf6",
  },
  {
    id: "builtin_webhook_syndication",
    name: "CMS & Blog Webhook Syndicator",
    description: "Triggered via inbound webhook when a new blog post is published. Uses AI to craft tailored social snippets for X, LinkedIn, and Instagram.",
    category: "integration",
    node_count: 5,
    tags: ["Webhook", "CMS", "Syndication"],
    color: "#06b6d4",
  },
];

export default function WorkflowTemplatesPage() {
  const router = useRouter();
  const toast = useToast();

  const [templates, setTemplates] = useState<WorkflowTemplateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [instantiatingId, setInstantiatingId] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadTemplates() {
    setLoading(true);
    try {
      const data = await fetchApi("/workflows/templates");
      setTemplates(Array.isArray(data) && data.length > 0 ? data : (BUILTIN_TEMPLATES as any));
    } catch {
      setTemplates(BUILTIN_TEMPLATES as any);
    } finally {
      setLoading(false);
    }
  }

  async function handleUseTemplate(template: WorkflowTemplateItem) {
    setInstantiatingId(template.id);
    try {
      // If template exists on backend, clone it; otherwise create standard workflow with sample graph
      let wf: any;
      if (template.id.startsWith("builtin_")) {
        wf = await fetchApi("/workflows", {
          method: "POST",
          body: JSON.stringify({
            name: template.name,
            description: template.description,
            nodes: [
              {
                id: "trigger_1",
                type: "trigger_schedule",
                name: "Daily Schedule",
                category: "trigger",
                config: { cron_expression: "0 9 * * 1-5" },
                position: { x: 250, y: 50 },
              },
              {
                id: "ai_1",
                type: "ai_generate_text",
                name: "Generate Post",
                category: "ai",
                config: { topic: "Industry innovation and company highlights", platform: "x", tone: "professional" },
                position: { x: 250, y: 200 },
              },
              {
                id: "validate_1",
                type: "social_content_validation",
                name: "Validate Content",
                category: "social",
                config: { platform: "x", check_spam: true },
                position: { x: 250, y: 350 },
              },
              {
                id: "publish_1",
                type: "social_publish",
                name: "Publish to X",
                category: "social",
                config: { platform: "x" },
                position: { x: 250, y: 500 },
              },
            ],
            edges: [
              { source: "trigger_1", target: "ai_1" },
              { source: "ai_1", target: "validate_1" },
              { source: "validate_1", target: "publish_1" },
            ],
          }),
        });
      } else {
        wf = await fetchApi(`/workflows/from-template/${template.id}`, { method: "POST" });
      }
      toast.success(`Workflow created from template "${template.name}"`);
      router.push(`/dashboard/workflows/${wf.id}`);
    } catch (e: any) {
      toast.error(e.message || "Failed to use template");
    } finally {
      setInstantiatingId(null);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => router.push("/dashboard/workflows")}
          className="text-slate-500 hover:text-slate-200 p-2 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
              <LayoutTemplate className="w-5 h-5 text-indigo-400" />
            </div>
            Workflow Templates
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Jumpstart your social media automation with pre-configured, production-grade recipes.
          </p>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-48 rounded-2xl bg-slate-800/50 animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl">
          {templates.map((tpl) => (
            <Card
              key={tpl.id}
              className="bg-slate-900/80 border-slate-700/60 hover:border-indigo-500/40 transition-all p-6 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center text-white"
                      style={{ backgroundColor: tpl.color || "#6366f1" }}
                    >
                      <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-base leading-tight">
                        {tpl.name}
                      </h3>
                      <span className="text-xs text-indigo-400 uppercase tracking-wider font-semibold">
                        {tpl.category || "Automation"}
                      </span>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-slate-400 mb-4 leading-relaxed">
                  {tpl.description}
                </p>

                {tpl.tags && (
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {tpl.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 font-medium"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                <span className="text-xs text-slate-500 flex items-center gap-1.5">
                  <GitBranch className="w-3.5 h-3.5" />
                  {tpl.node_count} pre-built steps
                </span>

                <Button
                  onClick={() => handleUseTemplate(tpl)}
                  disabled={instantiatingId === tpl.id}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs gap-1.5 px-3 py-1.5"
                >
                  {instantiatingId === tpl.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Plus className="w-3.5 h-3.5" />
                  )}
                  Use Template
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
