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

  const [activeTab, setActiveTab] = useState<"text" | "image">("text");

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
