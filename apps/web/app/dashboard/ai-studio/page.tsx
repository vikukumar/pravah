"use client";

import React, { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import {
  Bot,
  Sparkles,
  Send,
  Calendar,
  Image as ImageIcon,
  Copy,
  Check,
  Zap,
  Layers,
  Share2,
  RefreshCw,
  Clock,
  ArrowRight,
} from "lucide-react";

export default function AIStudioPage() {
  const router = useRouter();
  const toast = useToast();
  const { activeOrg } = useOrganisation();

  const [activeTab, setActiveTab] = useState<"text" | "image" | "auto">("auto");

  // Text Generator Form
  const [topic, setTopic] = useState("");
  const [platform, setPlatform] = useState("x");
  const [tone, setTone] = useState("professional");
  const [objective, setObjective] = useState("engagement");
  const [keywords, setKeywords] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Generated Text Result
  const [generatedResult, setGeneratedResult] = useState<any>(null);
  const [isCopied, setIsCopied] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  // Image Generator Form
  const [imagePrompt, setImagePrompt] = useState("");
  const [aspectRatio, setAspectRatio] = useState("1:1");
  const [imageStyle, setImageStyle] = useState("photorealistic");
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<any>(null);

  // Auto Generate & Post Form
  const [autoTopic, setAutoTopic] = useState("");
  const [autoKeywords, setAutoKeywords] = useState("");
  const [autoVoice, setAutoVoice] = useState("professional");
  const [autoCta, setAutoCta] = useState("");
  const [autoPlatforms, setAutoPlatforms] = useState<string[]>(["instagram", "x"]);
  const [autoGenImage, setAutoGenImage] = useState(true);
  const [autoImageStyle, setAutoImageStyle] = useState("photorealistic");
  const [autoAction, setAutoAction] = useState<"draft" | "schedule">("draft");
  const [autoUseHistory, setAutoUseHistory] = useState(false);
  const [autoGenerating, setAutoGenerating] = useState(false);
  const [autoResult, setAutoResult] = useState<any>(null);

  const ALL_PLATFORMS = [
    {
      id: "instagram",
      label: "Instagram",
      icon: (
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
        </svg>
      ),
      gradient: "from-purple-500 via-pink-500 to-orange-400",
    },
    {
      id: "x",
      label: "X / Twitter",
      icon: (
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.736l7.737-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      ),
      gradient: "from-slate-700 to-slate-900",
    },
    {
      id: "facebook",
      label: "Facebook",
      icon: (
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      ),
      gradient: "from-blue-600 to-blue-800",
    },
    {
      id: "linkedin",
      label: "LinkedIn",
      icon: (
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
        </svg>
      ),
      gradient: "from-blue-500 to-blue-700",
    },
    {
      id: "youtube",
      label: "YouTube",
      icon: (
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      ),
      gradient: "from-red-600 to-red-800",
    },
  ];

  const VOICE_OPTIONS = [
    { id: "professional", label: "Professional", desc: "Formal, authoritative" },
    { id: "casual", label: "Casual", desc: "Friendly, conversational" },
    { id: "viral", label: "Viral", desc: "Trending, engaging hooks" },
    { id: "educational", label: "Educational", desc: "Informative, data-driven" },
    { id: "inspirational", label: "Inspirational", desc: "Motivational, emotional" },
  ];

  const togglePlatform = (id: string) => {
    setAutoPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const handleAutoGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!autoTopic.trim()) {
      toast.error("Please enter a topic or keyword.");
      return;
    }
    if (autoPlatforms.length === 0) {
      toast.error("Please select at least one platform.");
      return;
    }

    setAutoGenerating(true);
    setAutoResult(null);
    try {
      const kwList = autoKeywords ? autoKeywords.split(",").map((k) => k.trim()) : undefined;
      const res = await fetchApi<any>("/ai/content/auto-content", {
        method: "POST",
        body: JSON.stringify({
          topic: autoTopic,
          platforms: autoPlatforms,
          account_ids: [],
          brand_voice: autoVoice,
          keywords: kwList,
          call_to_action: autoCta || undefined,
          generate_image: autoGenImage,
          image_style: autoImageStyle,
          action: autoAction,
          use_post_history: autoUseHistory,
        }),
      });
      setAutoResult(res);
      toast.success("Content Generated!", `${res.action === "draft" ? "Saved as draft" : "Scheduled"}: ${res.title}`);
    } catch (err: any) {
      toast.error("Auto-Generate Failed", err.message || "Could not generate content.");
    } finally {
      setAutoGenerating(false);
    }
  };

  const handleViewContent = () => router.push("/dashboard/content");

  const handleGenerateText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      toast.error("Please enter a topic or theme.");
      return;
    }

    setIsGenerating(true);
    try {
      const kwList = keywords ? keywords.split(",").map((k) => k.trim()) : undefined;
      const res = await fetchApi<any>("/ai/generate-text", {
        method: "POST",
        body: JSON.stringify({
          topic,
          platform,
          tone,
          objective,
          keywords: kwList,
        }),
      });

      setGeneratedResult(res);
      toast.success("Content Generated!", `Produced using ${res.provider} (${res.model}).`);
    } catch (err: any) {
      toast.error("Generation Failed", err.message || "Could not generate AI content.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    if (!generatedResult) return;
    navigator.clipboard.writeText(generatedResult.generated_text);
    setIsCopied(true);
    toast.info("Copied to clipboard!");
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleSaveAsDraft = async (publishNow: boolean = false) => {
    if (!generatedResult) return;

    setIsSavingDraft(true);
    try {
      const contentRes = await fetchApi<any>("/content", {
        method: "POST",
        body: JSON.stringify({
          title: topic.substring(0, 60),
          body: generatedResult.generated_text,
          content_type: "text",
          platforms: [platform],
          approval_required: false,
        }),
      });

      if (publishNow) {
        await fetchApi(`/content/${contentRes.id}/publish-now`, { method: "POST" });
        toast.success("Published!", `Dispatched directly to ${platform.toUpperCase()}.`);
      } else {
        toast.success("Saved to Drafts", "Available in your Content & Composer view.");
      }

      router.push("/dashboard/content");
    } catch (err: any) {
      toast.error("Action Failed", err.message || "Could not save content.");
    } finally {
      setIsSavingDraft(false);
    }
  };

  const handleGenerateImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!imagePrompt.trim()) {
      toast.error("Please provide an image prompt.");
      return;
    }

    setIsGeneratingImage(true);
    try {
      const res = await fetchApi<any>("/ai/generate-image", {
        method: "POST",
        body: JSON.stringify({
          prompt: imagePrompt,
          aspect_ratio: aspectRatio,
          style: imageStyle,
        }),
      });

      setGeneratedImage(res);
      toast.success("Visual Asset Created!", "Photorealistic media ready for distribution.");
    } catch (err: any) {
      toast.error("Image Generation Failed", err.message || "Failed to render visual asset.");
    } finally {
      setIsGeneratingImage(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <Bot className="w-6 h-6 text-indigo-400" /> AI Studio & Brand Intelligence
          </h1>
          <p className="text-xs text-slate-400">
            Generate platform-native social copy and visuals aligned with your brand persona.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab("auto")}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "auto" ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Zap className="w-3.5 h-3.5" /> Auto Generate & Post
          </button>
          <button
            onClick={() => setActiveTab("text")}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "text" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" /> Text Generator
          </button>
          <button
            onClick={() => setActiveTab("image")}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "image" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" /> Image Studio
          </button>
        </div>
      </div>

      {activeTab === "auto" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Config Panel */}
          <Card className="lg:col-span-5 space-y-5">
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" /> Auto Generate & Post
              </h3>
              <Badge variant="purple">SEO Optimized</Badge>
            </div>

            <form onSubmit={handleAutoGenerate} className="space-y-4">
              {/* Topic */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Topic / Keyword <span className="text-rose-400">*</span>
                </label>
                <textarea
                  value={autoTopic}
                  onChange={(e) => setAutoTopic(e.target.value)}
                  placeholder="e.g. Diwali offer for our skincare brand, #skincare trending tips..."
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              {/* Platform Selection */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Target Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {ALL_PLATFORMS.map((p) => {
                    const isSelected = autoPlatforms.includes(p.id);
                    const BRAND_COLORS: Record<string, string> = {
                      instagram: "linear-gradient(135deg, #833AB4, #FD1D1D, #F77737)",
                      x:         "linear-gradient(135deg, #1a1a2e, #16213e)",
                      facebook:  "linear-gradient(135deg, #1877F2, #0a5dc7)",
                      linkedin:  "linear-gradient(135deg, #0077B5, #005885)",
                      youtube:   "linear-gradient(135deg, #FF0000, #cc0000)",
                    };
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => togglePlatform(p.id)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all duration-200 ${
                          isSelected
                            ? "border-white/20 text-white shadow-lg scale-105"
                            : "bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200"
                        }`}
                        style={isSelected ? { background: BRAND_COLORS[p.id] } : undefined}
                      >
                        <span
                          className="flex items-center justify-center w-5 h-5 rounded-md"
                          style={{ background: isSelected ? "rgba(255,255,255,0.2)" : undefined }}
                        >
                          <span className={isSelected ? "text-white" : "text-slate-400"}>
                            {p.icon}
                          </span>
                        </span>
                        {p.label}
                        {isSelected && (
                          <span className="w-1.5 h-1.5 rounded-full bg-white/60 ml-0.5" />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Brand Voice */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Brand Voice</label>
                <div className="grid grid-cols-5 gap-1">
                  {VOICE_OPTIONS.map((v) => (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => setAutoVoice(v.id)}
                      title={v.desc}
                      className={`py-1.5 rounded-lg text-[10px] font-semibold border transition-all ${
                        autoVoice === v.id
                          ? "bg-purple-500/20 border-purple-500/60 text-purple-200"
                          : "bg-slate-800/50 border-slate-700 text-slate-500 hover:border-slate-500"
                      }`}
                    >
                      {v.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* SEO Keywords */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">SEO Keywords (optional)</label>
                <input
                  value={autoKeywords}
                  onChange={(e) => setAutoKeywords(e.target.value)}
                  placeholder="skincare, natural, glow, Diwali (comma-separated)"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* CTA */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Call to Action (optional)</label>
                <input
                  value={autoCta}
                  onChange={(e) => setAutoCta(e.target.value)}
                  placeholder="Shop now at our website, Book a free consultation..."
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {/* Image Toggle */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/50 border border-slate-800">
                <div>
                  <p className="text-xs font-medium text-slate-200">Generate Accompanying Image</p>
                  <p className="text-[10px] text-slate-400">Auto-create AI visual using DALL-E / FLUX</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={autoGenImage}
                  onClick={() => setAutoGenImage((v) => !v)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    autoGenImage ? "bg-indigo-600" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                      autoGenImage ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {autoGenImage && (
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-slate-300">Image Style</label>
                  <select
                    value={autoImageStyle}
                    onChange={(e) => setAutoImageStyle(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="photorealistic">Photorealistic</option>
                    <option value="illustration">Illustration / Flat Art</option>
                    <option value="3d render">3D Render</option>
                    <option value="watercolor">Watercolor</option>
                    <option value="minimalist">Minimalist Design</option>
                  </select>
                </div>
              )}

              {/* Post History Context */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/50 border border-slate-800">
                <div>
                  <p className="text-xs font-medium text-slate-200">Use My Post History</p>
                  <p className="text-[10px] text-slate-400">Sync style from your previous posts</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={autoUseHistory}
                  onClick={() => setAutoUseHistory((v) => !v)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    autoUseHistory ? "bg-indigo-600" : "bg-slate-700"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                      autoUseHistory ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Action */}
              <div className="grid grid-cols-2 gap-2">
                {(["draft", "schedule"] as const).map((a) => (
                  <button
                    key={a}
                    type="button"
                    onClick={() => setAutoAction(a)}
                    className={`py-2 rounded-xl text-xs font-semibold border transition-all capitalize ${
                      autoAction === a
                        ? "bg-indigo-500/20 border-indigo-500/60 text-indigo-200"
                        : "bg-slate-800/50 border-slate-700 text-slate-400"
                    }`}
                  >
                    {a === "draft" ? "💾 Save as Draft" : "⏰ Schedule"}
                  </button>
                ))}
              </div>

              <Button
                type="submit"
                variant="glow"
                className="w-full"
                disabled={autoGenerating}
                leftIcon={autoGenerating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              >
                {autoGenerating ? "Generating..." : "Generate & Create Content"}
              </Button>
            </form>
          </Card>

          {/* Result Panel */}
          <div className="lg:col-span-7 space-y-4">
            {autoGenerating && (
              <Card className="p-8 flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <Zap className="w-8 h-8 text-indigo-400 animate-pulse" />
                </div>
                <div className="text-center space-y-1">
                  <p className="text-sm font-semibold text-slate-200">Generating SEO Content...</p>
                  <p className="text-xs text-slate-400">AI is crafting platform-optimized posts{autoGenImage ? " and generating image" : ""}...</p>
                </div>
                <div className="flex gap-1">
                  {[0, 0.2, 0.4].map((d) => (
                    <div key={d} className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: `${d}s` }} />
                  ))}
                </div>
              </Card>
            )}

            {autoResult && !autoGenerating && (
              <>
                {/* Success Banner */}
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <Check className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-emerald-200">Content Created Successfully!</p>
                      <p className="text-[11px] text-slate-400">
                        {autoResult.action === "draft" ? "Saved as draft" : "Scheduled"} • Model: {autoResult.model} • {autoResult.tokens_used} tokens
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleViewContent} rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                    View Content
                  </Button>
                </div>

                {/* Generated image */}
                {autoResult.image_asset?.url && (
                  <Card className="p-4 space-y-3">
                    <h4 className="text-xs font-semibold text-slate-300">Generated Image</h4>
                    <div className="rounded-xl overflow-hidden border border-slate-700">
                      <Image
                        src={autoResult.image_asset.url}
                        alt={autoResult.title}
                        width={640}
                        height={640}
                        className="w-full object-cover max-h-64"
                      />
                    </div>
                  </Card>
                )}

                {/* Platform content breakdown */}
                {autoResult.seo_data?.platforms && (
                  <Card className="p-4 space-y-3">
                    <h4 className="text-xs font-semibold text-slate-300">Platform-Specific Content</h4>
                    <div className="space-y-3">
                      {Object.entries(autoResult.seo_data.platforms).map(([platform, data]: [string, any]) => (
                        <div key={platform} className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-slate-300 uppercase">{platform}</span>
                            <span className="text-[10px] text-slate-500">{data.character_count || data.body?.length || 0} chars</span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{data.body}</p>
                          {data.hashtags?.length > 0 && (
                            <p className="text-[11px] text-indigo-400">
                              #{data.hashtags.join(" #")}
                            </p>
                          )}
                          <button
                            onClick={() => { navigator.clipboard.writeText(data.body); toast.info("Copied!"); }}
                            className="text-[10px] text-slate-500 hover:text-slate-300 flex items-center gap-1 transition-colors"
                          >
                            <Copy className="w-3 h-3" /> Copy
                          </button>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* SEO Meta */}
                {autoResult.seo_data?.meta_description && (
                  <Card className="p-4 space-y-2">
                    <h4 className="text-xs font-semibold text-slate-300">SEO Meta</h4>
                    <p className="text-xs font-bold text-slate-200">{autoResult.seo_data.title}</p>
                    <p className="text-[11px] text-slate-400">{autoResult.seo_data.meta_description}</p>
                    {autoResult.seo_data.suggested_posting_time && (
                      <p className="text-[10px] text-indigo-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Best time: {autoResult.seo_data.suggested_posting_time}
                      </p>
                    )}
                  </Card>
                )}
              </>
            )}

            {!autoResult && !autoGenerating && (
              <Card className="p-8 flex flex-col items-center gap-4 border-dashed">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <Zap className="w-8 h-8 text-indigo-400/50" />
                </div>
                <div className="text-center space-y-2">
                  <p className="text-sm font-semibold text-slate-300">Auto Generate & Post</p>
                  <p className="text-xs text-slate-500 max-w-xs">
                    Enter a topic, select platforms and voice, and let AI generate SEO-optimized content + image in one click.
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-3 w-full max-w-xs text-center">
                  {["ChatGPT", "Gemini", "Claude", "Groq", "Llama", "Mistral"].map((m) => (
                    <span key={m} className="text-[10px] text-slate-500 py-1 px-2 rounded-lg border border-slate-800">{m}</span>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {activeTab === "text" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Form */}
          <Card className="lg:col-span-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-800 pb-3 flex items-center justify-between">
              <span>Prompt Configuration</span>
              <Badge variant="purple">OpenRouter 400+</Badge>
            </h3>

            <form onSubmit={handleGenerateText} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Topic / Core Message <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={3}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="e.g. Announcing our new visual workflow builder with topological execution..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  required
                />
              </div>

              {/* Target Platform */}
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Target Social Platform</label>
                <div className="grid grid-cols-5 gap-1.5">
                  {["x", "linkedin", "facebook", "instagram", "youtube"].map((plat) => (
                    <button
                      key={plat}
                      type="button"
                      onClick={() => setPlatform(plat)}
                      className={`p-2 rounded-xl text-center text-xs font-medium border transition-colors capitalize ${
                        platform === plat
                          ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/50"
                          : "bg-slate-900/40 text-slate-400 border-slate-800 hover:bg-slate-800"
                      }`}
                    >
                      {plat === "x" ? "X" : plat.substring(0, 3)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tone & Objective */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-slate-300">Brand Tone</label>
                  <select
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                  >
                    <option value="professional">Professional</option>
                    <option value="authoritative">Authoritative</option>
                    <option value="casual">Casual & Friendly</option>
                    <option value="enthusiastic">Enthusiastic</option>
                    <option value="humorous">Witty & Humorous</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-slate-300">Campaign Objective</label>
                  <select
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                  >
                    <option value="engagement">Engagement & Shares</option>
                    <option value="thought_leadership">Thought Leadership</option>
                    <option value="conversions">Product Conversion</option>
                    <option value="announcement">Announcement</option>
                  </select>
                </div>
              </div>

              <Input
                label="Target Keywords (comma-separated)"
                placeholder="AI, SaaS, Automation, NextGen"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
              />

              <Button type="submit" variant="glow" className="w-full" isLoading={isGenerating} leftIcon={<Sparkles className="w-4 h-4" />}>
                Generate AI Content
              </Button>
            </form>
          </Card>

          {/* Output & Preview Area */}
          <Card glow className="lg:col-span-7 space-y-4 border-indigo-500/30 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-semibold text-slate-200">Generated Output Preview</span>
                {generatedResult && (
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span>{generatedResult.tokens_used} tokens</span>
                    <span>•</span>
                    <span>${generatedResult.estimated_cost_usd}</span>
                  </div>
                )}
              </div>

              {!generatedResult ? (
                <div className="text-center py-20 space-y-3">
                  <Sparkles className="w-10 h-10 text-slate-600 mx-auto animate-pulse" />
                  <p className="text-xs text-slate-400">
                    Configure your prompt on the left and click &quot;Generate AI Content&quot;.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Output content box */}
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-100 whitespace-pre-wrap leading-relaxed">
                    {generatedResult.generated_text}
                  </div>

                  {/* Hashtags and CTA pills */}
                  {generatedResult.suggested_hashtags?.length > 0 && (
                    <div className="space-y-1.5">
                      <p className="text-[11px] text-slate-400 font-semibold">Suggested Hashtags:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {generatedResult.suggested_hashtags.map((h: string, idx: number) => (
                          <span key={idx} className="bg-indigo-950/50 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded text-[11px]">
                            {h}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action buttons */}
            {generatedResult && (
              <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <Button variant="outline" size="sm" onClick={handleCopy} leftIcon={isCopied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}>
                  {isCopied ? "Copied" : "Copy Copy"}
                </Button>

                <div className="flex items-center gap-2">
                  <Button variant="secondary" size="sm" onClick={() => handleSaveAsDraft(false)} isLoading={isSavingDraft}>
                    Save Draft
                  </Button>
                  <Button variant="glow" size="sm" onClick={() => handleSaveAsDraft(true)} isLoading={isSavingDraft} rightIcon={<Send className="w-3.5 h-3.5" />}>
                    Publish Immediately
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      ) : (
        /* Image Studio */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Card className="lg:col-span-5 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 border-b border-slate-800 pb-3">
              Image Generation Prompt
            </h3>

            <form onSubmit={handleGenerateImage} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Visual Prompt Description <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={4}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="e.g. Ultra high-tech glassmorphism dashboard floating in a dark cyberpunk workspace with neon violet and cyan accents..."
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-slate-300">Aspect Ratio</label>
                  <select
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none"
                    value={aspectRatio}
                    onChange={(e) => setAspectRatio(e.target.value)}
                  >
                    <option value="1:1">1:1 (Square - Feed)</option>
                    <option value="16:9">16:9 (Landscape - X/YT)</option>
                    <option value="9:16">9:16 (Story/Reel)</option>
                    <option value="4:5">4:5 (Portrait - IG)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-slate-300">Style</label>
                  <select
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none"
                    value={imageStyle}
                    onChange={(e) => setImageStyle(e.target.value)}
                  >
                    <option value="photorealistic">Photorealistic</option>
                    <option value="cinematic">Cinematic 3D</option>
                    <option value="minimal">Minimalist Vector</option>
                    <option value="digital_art">Digital Art</option>
                  </select>
                </div>
              </div>

              <Button type="submit" variant="glow" className="w-full" isLoading={isGeneratingImage} leftIcon={<ImageIcon className="w-4 h-4" />}>
                Render Visual Asset
              </Button>
            </form>
          </Card>

          <Card glow className="lg:col-span-7 flex flex-col justify-center items-center p-6 border-indigo-500/30 min-h-[350px]">
            {!generatedImage ? (
              <div className="text-center space-y-3">
                <ImageIcon className="w-12 h-12 text-slate-600 mx-auto animate-pulse" />
                <p className="text-xs text-slate-400">Specify an image prompt to render creative assets.</p>
              </div>
            ) : (
              <div className="space-y-4 w-full text-center">
                <div className="relative w-full h-80 rounded-xl overflow-hidden border border-slate-700 bg-slate-950">
                  <Image
                    src={generatedImage.image_url}
                    alt={generatedImage.prompt}
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 px-2">
                  <span>Dimensions: {generatedImage.dimensions}</span>
                  <span>Cost: ${generatedImage.estimated_cost_usd}</span>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
