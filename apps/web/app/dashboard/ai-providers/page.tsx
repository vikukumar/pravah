"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import {
  Bot,
  Plus,
  Trash2,
  Star,
  CheckCircle2,
  XCircle,
  Loader2,
  ExternalLink,
  Shield,
  Zap,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Server,
  Key,
} from "lucide-react";

interface ProviderModel {
  id: string;
  name: string;
  type: "text" | "image";
  tag: string;
}

interface CatalogEntry {
  id: string;
  name: string;
  badge: string;
  default_uri: string;
  doc_url: string;
  description: string;
  models: ProviderModel[];
}

interface OrgProvider {
  id: string;
  name: string;
  provider_type: string;
  api_endpoint: string;
  has_api_key: boolean;
  masked_api_key: string | null;
  is_default: boolean;
  is_enabled: boolean;
  supports_text: boolean;
  supports_image: boolean;
  supports_vision: boolean;
  created_at: string;
}

type TestStatus = "idle" | "testing" | "success" | "error";

const CAPABILITY_DEFAULTS: Record<string, { text: boolean; image: boolean; vision: boolean }> = {
  openrouter: { text: true, image: true, vision: true },
  openai: { text: true, image: true, vision: true },
  anthropic: { text: true, image: false, vision: true },
  google: { text: true, image: false, vision: true },
  groq: { text: true, image: false, vision: false },
  perplexity: { text: true, image: false, vision: false },
  cohere: { text: true, image: false, vision: false },
  custom: { text: true, image: false, vision: false },
};

export default function AIProvidersPage() {
  const toast = useToast();
  const { activeOrg } = useOrganisation();

  const [orgProviders, setOrgProviders] = useState<OrgProvider[]>([]);
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [testStatus, setTestStatus] = useState<Record<string, TestStatus>>({});

  // Add Modal state
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [selectedCatalogId, setSelectedCatalogId] = useState<string>("");
  const [selectedEntry, setSelectedEntry] = useState<CatalogEntry | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [customUri, setCustomUri] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [expandedProviders, setExpandedProviders] = useState<Record<string, boolean>>({});

  const fetchData = useCallback(async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const [providersData, catalogData] = await Promise.all([
        fetchApi<OrgProvider[]>("/ai/providers"),
        fetchApi<CatalogEntry[]>("/ai/providers/catalog"),
      ]);
      setOrgProviders(providersData);
      setCatalog(catalogData);
    } catch {
      toast.error("Load Failed", "Could not load AI provider configuration.");
    } finally {
      setIsLoading(false);
    }
  }, [activeOrg]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelectCatalog = (catalogId: string) => {
    setSelectedCatalogId(catalogId);
    const entry = catalog.find((c) => c.id === catalogId) || null;
    setSelectedEntry(entry);
    setCustomUri(entry?.default_uri || "");
    setSelectedModel(entry?.models?.[0]?.id || "");
    setApiKey("");
    setShowApiKey(false);
  };

  const handleAddProvider = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCatalogId || !apiKey.trim()) return;

    setIsSaving(true);
    try {
      const caps = CAPABILITY_DEFAULTS[selectedCatalogId] || { text: true, image: false, vision: false };
      await fetchApi("/ai/providers", {
        method: "POST",
        body: JSON.stringify({
          provider_type: selectedCatalogId,
          api_key: apiKey.trim(),
          api_endpoint: customUri.trim() || selectedEntry?.default_uri,
          supports_text: caps.text,
          supports_image: caps.image,
          supports_vision: caps.vision,
        }),
      });
      toast.success("Provider Added!", `${selectedEntry?.name || selectedCatalogId} is now active for your workspace.`);
      setAddModalOpen(false);
      setApiKey("");
      setSelectedCatalogId("");
      setSelectedEntry(null);
      fetchData();
    } catch (err: any) {
      toast.error("Failed to Add Provider", err.message || "Could not save provider configuration.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async (providerId: string) => {
    setTestStatus((prev) => ({ ...prev, [providerId]: "testing" }));
    try {
      const result = await fetchApi<{ status: string; message?: string }>(`/ai/providers/${providerId}/test`, {
        method: "POST",
      });
      if (result.status === "success") {
        setTestStatus((prev) => ({ ...prev, [providerId]: "success" }));
        toast.success("Connection Verified!", result.message || "Provider is responding correctly.");
      } else {
        setTestStatus((prev) => ({ ...prev, [providerId]: "error" }));
        toast.error("Connection Failed", result.message || "Provider test returned an error.");
      }
    } catch (err: any) {
      setTestStatus((prev) => ({ ...prev, [providerId]: "error" }));
      toast.error("Test Failed", err.message || "Could not reach provider.");
    } finally {
      setTimeout(() => setTestStatus((prev) => ({ ...prev, [providerId]: "idle" })), 4000);
    }
  };

  const handleSetDefault = async (providerId: string) => {
    try {
      await fetchApi(`/ai/providers/${providerId}/set-default`, { method: "POST" });
      toast.success("Default Updated", "This provider will now be used for all AI generation.");
      fetchData();
    } catch (err: any) {
      toast.error("Failed", err.message || "Could not set default provider.");
    }
  };

  const handleToggleEnabled = async (provider: OrgProvider) => {
    try {
      await fetchApi(`/ai/providers/${provider.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_enabled: !provider.is_enabled }),
      });
      fetchData();
    } catch (err: any) {
      toast.error("Failed", err.message || "Could not update provider.");
    }
  };

  const handleDelete = async (provider: OrgProvider) => {
    try {
      await fetchApi(`/ai/providers/${provider.id}`, { method: "DELETE" });
      toast.success("Removed", `${provider.name} has been removed from your workspace.`);
      fetchData();
    } catch (err: any) {
      toast.error("Delete Failed", err.message || "Could not remove provider.");
    }
  };

  const toggleExpand = (id: string) =>
    setExpandedProviders((prev) => ({ ...prev, [id]: !prev[id] }));

  const getTestIcon = (status: TestStatus) => {
    if (status === "testing") return <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />;
    if (status === "success") return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
    if (status === "error") return <XCircle className="w-3.5 h-3.5 text-rose-400" />;
    return <Zap className="w-3.5 h-3.5" />;
  };

  const configuredProviderIds = new Set(orgProviders.map((p) => p.provider_type));

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <Bot className="w-6 h-6 text-indigo-400" /> AI Providers
          </h1>
          <p className="text-xs text-slate-400 max-w-xl">
            Configure your own AI API keys (BYOA). Your providers override the platform defaults —
            all keys are AES-256 encrypted at rest and never exposed in plaintext.
          </p>
        </div>
        <Button variant="glow" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setAddModalOpen(true)}>
          Add Provider
        </Button>
      </div>

      {/* Resolution Chain Banner */}
      <div className="flex items-center gap-2 p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-xs text-indigo-300">
        <Server className="w-4 h-4 text-indigo-400 shrink-0" />
        <span className="font-semibold">Resolution Chain:</span>
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-200 font-bold">Your Org Providers</span>
          <ChevronRight className="w-3 h-3 text-indigo-500" />
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">Admin Platform Default</span>
          <ChevronRight className="w-3 h-3 text-slate-600" />
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">Environment Fallback</span>
        </div>
      </div>

      {/* Configured Providers */}
      {isLoading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : orgProviders.length === 0 ? (
        <Card className="py-14 flex flex-col items-center text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center">
            <Key className="w-7 h-7 text-slate-500" />
          </div>
          <div className="space-y-1.5">
            <h3 className="text-sm font-semibold text-slate-200">No Workspace AI Providers Yet</h3>
            <p className="text-xs text-slate-400 max-w-md">
              Add your own API key to use any supported AI provider. Your workspace providers take
              priority over the platform default and are private to your organisation.
            </p>
          </div>
          <Button variant="glow" size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setAddModalOpen(true)}>
            Add Your First Provider
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {orgProviders.map((prov) => {
            const expanded = expandedProviders[prov.id];
            const ts = testStatus[prov.id] || "idle";
            return (
              <Card key={prov.id} className={`space-y-0 ${!prov.is_enabled ? "opacity-60" : ""}`}>
                {/* Card Header */}
                <div className="flex items-center justify-between gap-3 p-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-indigo-950/50 border border-indigo-500/20 flex items-center justify-center shrink-0">
                      <Bot className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-sm font-bold text-slate-100 truncate">{prov.name}</h4>
                        {prov.is_default && (
                          <Badge variant="success" className="text-[10px] py-0 flex items-center gap-1">
                            <Star className="w-2.5 h-2.5" /> Default
                          </Badge>
                        )}
                        <Badge variant={prov.is_enabled ? "purple" : "default"} className="text-[10px] py-0">
                          {prov.provider_type}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {prov.api_endpoint}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleTest(prov.id)}
                      disabled={ts === "testing"}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-semibold transition-colors"
                      title="Test connection"
                    >
                      {getTestIcon(ts)}
                      <span>{ts === "testing" ? "Testing…" : ts === "success" ? "Online" : ts === "error" ? "Failed" : "Test"}</span>
                    </button>
                    <button
                      onClick={() => toggleExpand(prov.id)}
                      className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
                    >
                      {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {expanded && (
                  <div className="px-4 pb-4 space-y-4 border-t border-slate-800 pt-4">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-center">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Text Generation</span>
                        <p className={prov.supports_text ? "text-emerald-400 text-xs font-bold" : "text-slate-600 text-xs"}>
                          {prov.supports_text ? "✓ Supported" : "✗ Disabled"}
                        </p>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-center">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Image Generation</span>
                        <p className={prov.supports_image ? "text-emerald-400 text-xs font-bold" : "text-slate-600 text-xs"}>
                          {prov.supports_image ? "✓ Supported" : "✗ Disabled"}
                        </p>
                      </div>
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-center">
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Vision / Multimodal</span>
                        <p className={prov.supports_vision ? "text-emerald-400 text-xs font-bold" : "text-slate-600 text-xs"}>
                          {prov.supports_vision ? "✓ Supported" : "✗ Disabled"}
                        </p>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-3">
                      <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-[11px] font-semibold text-slate-300">Encrypted API Key</p>
                        <p className="text-[11px] text-slate-500 font-mono truncate">
                          {prov.masked_api_key || "•••••••••••••••"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      {!prov.is_default && (
                        <Button
                          variant="outline"
                          size="sm"
                          leftIcon={<Star className="w-3.5 h-3.5 text-amber-400" />}
                          onClick={() => handleSetDefault(prov.id)}
                        >
                          Set as Default
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggleEnabled(prov)}
                      >
                        {prov.is_enabled ? "Disable" : "Enable"}
                      </Button>
                      <button
                        onClick={() => handleDelete(prov)}
                        className="ml-auto p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
                        title="Remove provider"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Provider Modal */}
      <Modal
        isOpen={addModalOpen}
        onClose={() => {
          setAddModalOpen(false);
          setSelectedCatalogId("");
          setSelectedEntry(null);
          setApiKey("");
        }}
        title="Add AI Provider"
        description="Connect your own API key. Overrides the platform default for your workspace."
        maxWidth="lg"
      >
        <form onSubmit={handleAddProvider} className="space-y-5">
          {/* Provider Selector Grid */}
          {!selectedCatalogId ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Select Provider</label>
              <div className="grid grid-cols-2 gap-2.5 max-h-80 overflow-y-auto pr-1">
                {catalog.map((entry) => {
                  const alreadyAdded = configuredProviderIds.has(entry.id);
                  return (
                    <button
                      key={entry.id}
                      type="button"
                      onClick={() => !alreadyAdded && handleSelectCatalog(entry.id)}
                      disabled={alreadyAdded}
                      className={`p-3.5 rounded-xl border text-left transition-all ${
                        alreadyAdded
                          ? "border-slate-800 bg-slate-900/30 opacity-50 cursor-not-allowed"
                          : "border-slate-800 bg-slate-900/60 hover:border-indigo-500/60 hover:bg-slate-900 cursor-pointer"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] font-bold text-slate-100 leading-tight">{entry.name}</span>
                        <Badge variant="purple" className="text-[9px] py-0 shrink-0 ml-1">
                          {alreadyAdded ? "Added" : entry.badge}
                        </Badge>
                      </div>
                      <p className="text-[10px] text-slate-400 line-clamp-2">{entry.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <>
              {/* Back + selected provider info */}
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-slate-100">{selectedEntry?.name}</p>
                  <p className="text-[11px] text-slate-400">{selectedEntry?.description}</p>
                </div>
                <button
                  type="button"
                  onClick={() => { setSelectedCatalogId(""); setSelectedEntry(null); }}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300 shrink-0 mt-0.5"
                >
                  ← Change
                </button>
              </div>

              {/* API Key field */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                  <span>API Key</span>
                  {selectedEntry?.doc_url && (
                    <a
                      href={selectedEntry.doc_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-[11px]"
                    >
                      Get key <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={`Paste your ${selectedEntry?.name || "provider"} API key`}
                    required
                    className="w-full px-3 py-2.5 pr-20 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] text-slate-400 hover:text-slate-200 px-2 py-1"
                  >
                    {showApiKey ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              {/* API Endpoint (collapsible for non-custom) */}
              {selectedCatalogId === "custom" && (
                <Input
                  label="API Endpoint (Base URL)"
                  value={customUri}
                  onChange={(e) => setCustomUri(e.target.value)}
                  placeholder="http://localhost:11434/v1"
                />
              )}

              {selectedCatalogId !== "custom" && customUri !== selectedEntry?.default_uri && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
                  <span className="font-semibold text-slate-300">Endpoint: </span>{customUri || selectedEntry?.default_uri}
                </div>
              )}

              {/* Models preview */}
              {selectedEntry?.models && selectedEntry.models.length > 0 && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Available Models</label>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedEntry.models.map((m) => (
                      <span
                        key={m.id}
                        className={`px-2 py-0.5 rounded text-[11px] border ${
                          m.type === "image"
                            ? "bg-pink-950/30 border-pink-500/20 text-pink-300"
                            : "bg-indigo-950/30 border-indigo-500/20 text-indigo-300"
                        }`}
                      >
                        {m.name} · {m.tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-[11px] text-emerald-300">
                <Shield className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                Your API key is encrypted with AES-256 before being stored. It is never logged or transmitted in plaintext.
              </div>

              <div className="flex gap-3">
                <Button type="submit" variant="glow" isLoading={isSaving} className="flex-1">
                  {isSaving ? "Saving…" : "Save Provider"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setAddModalOpen(false)}>
                  Cancel
                </Button>
              </div>
            </>
          )}
        </form>
      </Modal>
    </div>
  );
}
