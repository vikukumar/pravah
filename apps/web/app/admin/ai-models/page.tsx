"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import {
  Bot,
  Sparkles,
  Key,
  Save,
  Server,
  ShieldCheck,
  Eye,
  EyeOff,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  PlayCircle,
  RotateCcw,
  Layers,
  Cpu,
} from "lucide-react";

interface AIProviderItem {
  id: string;
  name: string;
  badge: string;
  default_uri: string;
  doc_url: string;
  description: string;
  models: { id: string; name: string; type: "text" | "image"; tag: string }[];
}

export default function AdminAIModelsPage() {
  const toast = useToast();
  const [catalog, setCatalog] = useState<AIProviderItem[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string>("openrouter");
  const [activeProvider, setActiveProvider] = useState<string>("openrouter");

  // Form State for Selected Provider
  const [baseUri, setBaseUri] = useState<string>("");
  const [apiKey, setApiKey] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectedImageModel, setSelectedImageModel] = useState<string>("");
  const [showKey, setShowKey] = useState<boolean>(false);

  // Testing & Saving States
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Stored configs map
  const [storedConfigs, setStoredConfigs] = useState<Record<string, any>>({});

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [catalogData, configData] = await Promise.all([
        fetchApi<AIProviderItem[]>("/admin/ai/catalog"),
        fetchApi<any>("/admin/ai/providers"),
      ]);

      setCatalog(catalogData);
      setActiveProvider(configData.active_provider || "openrouter");
      setStoredConfigs(configData.providers_config || {});

      // Setup default active provider selection
      const initialProv = catalogData.find((p) => p.id === (configData.active_provider || "openrouter")) || catalogData[0];
      if (initialProv) {
        setSelectedProviderId(initialProv.id);
        const existing = configData.providers_config?.[initialProv.id] || {};
        setBaseUri(existing.base_uri || initialProv.default_uri);
        setSelectedModel(configData.default_text_model || initialProv.models[0]?.id || "");
        setSelectedImageModel(configData.default_image_model || "stabilityai/stable-diffusion-xl");
      }
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const selectedProvider = catalog.find((p) => p.id === selectedProviderId) || catalog[0];

  // When switching selected provider in tab, sync form fields
  const handleSelectProvider = (prov: AIProviderItem) => {
    setSelectedProviderId(prov.id);
    setTestResult(null);
    setShowKey(false);
    const existing = storedConfigs[prov.id] || {};
    setBaseUri(existing.base_uri || prov.default_uri);
    setApiKey(""); // Keep clean for user input
    if (prov.models.length > 0) {
      setSelectedModel(existing.default_model || prov.models[0].id);
    }
  };

  const handleResetToDefaultUri = () => {
    if (selectedProvider) {
      setBaseUri(selectedProvider.default_uri);
      toast.info("URI Reset", `Set to default: ${selectedProvider.default_uri}`);
    }
  };

  const handleTestConnection = async () => {
    if (!apiKey.trim() && !storedConfigs[selectedProviderId]?.configured) {
      toast.error("API Key Required", "Please enter an API key to test the connection.");
      return;
    }

    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await fetchApi<any>("/admin/ai/test-connection", {
        method: "POST",
        body: JSON.stringify({
          provider_id: selectedProviderId,
          base_uri: baseUri,
          api_key: apiKey.trim(),
        }),
      });

      setTestResult({
        status: res.status,
        message: res.message,
      });

      if (res.status === "success") {
        toast.success("Connection Verified!", res.message);
      } else {
        toast.info("Connection Notice", res.message);
      }
    } catch (err: any) {
      setTestResult({
        status: "error",
        message: err.message || "Failed to reach endpoint.",
      });
      toast.error("Test Failed", err.message || "Connection failed.");
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const updatedConfigs = {
        ...storedConfigs,
        [selectedProviderId]: {
          base_uri: baseUri,
          default_model: selectedModel,
          configured: apiKey.trim() ? true : (storedConfigs[selectedProviderId]?.configured || false),
          updated_at: new Date().toISOString(),
        },
      };

      const payload: any = {
        active_provider: selectedProviderId,
        providers_config: updatedConfigs,
        default_text_model: selectedModel,
        default_image_model: selectedImageModel,
      };

      if (selectedProviderId === "openrouter" && apiKey.trim()) {
        payload.openrouter_api_key = apiKey.trim();
      }

      await fetchApi("/admin/ai/providers", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      toast.success("Provider Configured!", `${selectedProvider?.name} is now saved and active.`);
      setActiveProvider(selectedProviderId);
      setStoredConfigs(updatedConfigs);
      setApiKey("");
    } catch (err: any) {
      toast.error("Save Failed", err.message || "Could not save AI provider.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
          <Bot className="w-6 h-6 text-indigo-400" /> AI Provider & Model Routing Matrix
        </h1>
        <p className="text-xs text-slate-400">
          Select an AI provider, configure custom or default API endpoints, verify credentials, and manage model routing.
        </p>
      </div>

      {/* Step 1: Choose AI Provider */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" /> 1. Select AI Provider
          </h3>
          <span className="text-[11px] text-slate-400">
            Active Global Provider: <strong className="text-emerald-400 uppercase">{activeProvider}</strong>
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {catalog.map((prov) => {
            const isSelected = selectedProviderId === prov.id;
            const isActive = activeProvider === prov.id;

            return (
              <button
                key={prov.id}
                type="button"
                onClick={() => handleSelectProvider(prov)}
                className={`p-3 rounded-2xl border text-left flex flex-col justify-between transition-all ${
                  isSelected
                    ? "bg-indigo-600/20 border-indigo-500 text-white shadow-lg shadow-indigo-600/10 scale-[1.02]"
                    : "bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-700"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold truncate">{prov.name.split("(")[0]}</span>
                  </div>
                  <Badge variant={isActive ? "success" : "purple"} className="text-[9px] px-1.5 py-0">
                    {isActive ? "Active" : prov.badge}
                  </Badge>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Step 2: Configure Selected Provider */}
      {selectedProvider && (
        <Card className="p-6 space-y-6 border-indigo-500/30">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2.5">
                <h2 className="text-lg font-bold text-slate-100">{selectedProvider.name}</h2>
                <Badge variant={activeProvider === selectedProvider.id ? "success" : "purple"}>
                  {activeProvider === selectedProvider.id ? "Active Provider" : selectedProvider.badge}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 max-w-2xl">{selectedProvider.description}</p>
            </div>

            <a
              href={selectedProvider.doc_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 shrink-0 px-3 py-1.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 transition-colors"
            >
              Get API Key & Docs <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>

          <form onSubmit={handleSaveProvider} className="space-y-5">
            {/* Base URI with Default Option */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-medium text-slate-300">
                  Provider Base URI / Endpoint
                </label>
                <button
                  type="button"
                  onClick={handleResetToDefaultUri}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3" /> Use Official Default URI
                </button>
              </div>

              <div className="relative">
                <input
                  type="text"
                  value={baseUri}
                  onChange={(e) => setBaseUri(e.target.value)}
                  placeholder={selectedProvider.default_uri}
                  required
                  className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-indigo-500/60"
                />
              </div>
              <p className="text-[11px] text-slate-500">
                Default: <span className="font-mono text-slate-400">{selectedProvider.default_uri}</span>
              </p>
            </div>

            {/* API Key */}
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-slate-300">
                {selectedProvider.name} API Key / Secret Token
              </label>
              <div className="relative">
                <input
                  type={showKey ? "text" : "password"}
                  placeholder={
                    storedConfigs[selectedProvider.id]?.configured
                      ? "•••••••••••••••• (Active — enter new key to replace)"
                      : "Paste API Key..."
                  }
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 pr-10 text-xs text-slate-100 font-mono placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-[11px] text-slate-500">
                All credentials are encrypted with AES-256 Fernet encryption at rest.
              </p>
            </div>

            {/* Model Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Default Text Model</label>
                <div className="space-y-2">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none"
                  >
                    {selectedProvider.models
                      .filter((m) => m.type === "text")
                      .map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} ({m.tag})
                        </option>
                      ))}
                  </select>
                  <input
                    type="text"
                    placeholder="Or type custom model identifier (e.g. meta-llama/llama-3.3-70b-instruct)"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-slate-900/60 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 font-mono placeholder:text-slate-600 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Default Image Generator</label>
                <select
                  value={selectedImageModel}
                  onChange={(e) => setSelectedImageModel(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none"
                >
                  <option value="stabilityai/stable-diffusion-xl">Stable Diffusion XL 1.0 (OpenRouter)</option>
                  <option value="black-forest-labs/flux-1-schnell">FLUX.1 Schnell (Together / OpenRouter)</option>
                  <option value="dall-e-3">OpenAI DALL-E 3</option>
                </select>
              </div>
            </div>

            {/* Test Connection Result Box */}
            {testResult && (
              <div
                className={`p-3.5 rounded-xl border flex items-center gap-3 text-xs ${
                  testResult.status === "success"
                    ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-300"
                    : testResult.status === "warning"
                    ? "bg-amber-950/30 border-amber-500/30 text-amber-300"
                    : "bg-rose-950/30 border-rose-500/30 text-rose-300"
                }`}
              >
                {testResult.status === "success" ? (
                  <CheckCircle2 className="w-5 h-5 shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 shrink-0" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}

            {/* Actions Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-800">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleTestConnection}
                isLoading={isTesting}
                leftIcon={<PlayCircle className="w-4 h-4 text-indigo-400" />}
              >
                Test Connection & Verify Key
              </Button>

              <Button
                type="submit"
                variant="glow"
                isLoading={isSaving}
                leftIcon={<Save className="w-4 h-4" />}
              >
                Save & Set as Active Provider
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}
