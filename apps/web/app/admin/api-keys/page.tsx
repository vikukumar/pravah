"use client";
import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { Key, CheckCircle, XCircle, Eye, EyeOff, Save, Trash2, RefreshCw, ExternalLink } from "lucide-react";

interface ApiKey { key: string; is_set: boolean; masked_value: string | null; category: string; }

const KEY_META: Record<string, { label: string; desc: string; docUrl: string; placeholder: string }> = {
  OPENROUTER_API_KEY:        { label: "OpenRouter API Key",        desc: "Unified gateway for 400+ AI models", docUrl: "https://openrouter.ai/keys",                    placeholder: "sk-or-v1-..." },
  OPENAI_API_KEY:            { label: "OpenAI Direct API Key",     desc: "Direct GPT-4o, DALL-E 3 access",    docUrl: "https://platform.openai.com/api-keys",           placeholder: "sk-proj-..." },
  ANTHROPIC_API_KEY:         { label: "Anthropic Claude API Key",  desc: "Claude 3.5 Sonnet, Haiku, Opus",    docUrl: "https://console.anthropic.com/settings/keys",    placeholder: "sk-ant-..." },
  CALENDARIFIC_API_KEY:      { label: "Calendarific API Key",      desc: "Indian & global holiday calendar",  docUrl: "https://calendarific.com/api-access",             placeholder: "cal_..." },
  ABSTRACT_HOLIDAYS_API_KEY: { label: "Abstract Holidays API Key", desc: "Holiday data fallback provider",    docUrl: "https://app.abstractapi.com/api/holidays",       placeholder: "..." },
  GOOGLE_CALENDAR_API_KEY:   { label: "Google Calendar API Key",   desc: "Public Google Calendar events",     docUrl: "https://console.cloud.google.com/apis/credentials", placeholder: "AIza..." },
  SENDGRID_API_KEY:          { label: "SendGrid API Key",          desc: "Transactional email delivery",      docUrl: "https://app.sendgrid.com/settings/api_keys",     placeholder: "SG...." },
  MAILGUN_API_KEY:           { label: "Mailgun API Key",           desc: "Email delivery via Mailgun",        docUrl: "https://app.mailgun.com/app/account/security",   placeholder: "key-..." },
};

function ApiKeyRow({ apiKey, onRefresh }: { apiKey: ApiKey; onRefresh: () => void }) {
  const toast = useToast();
  const meta = KEY_META[apiKey.key] || { label: apiKey.key, desc: "", docUrl: "#", placeholder: "Enter key..." };
  const [newValue, setNewValue] = useState("");
  const [show, setShow] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const save = async () => {
    if (!newValue.trim()) { toast.error("Enter a valid API key"); return; }
    setSaving(true);
    try {
      await fetchApi(`/admin/api-keys/${apiKey.key}`, { method: "POST", body: JSON.stringify({ value: newValue }) });
      toast.success(`${meta.label} saved!`);
      setNewValue(""); setExpanded(false); onRefresh();
    } catch (e: any) { toast.error(e.message); } finally { setSaving(false); }
  };

  const remove = async () => {
    if (!confirm(`Remove ${meta.label}? This may break features depending on this key.`)) return;
    setDeleting(true);
    try {
      await fetchApi(`/admin/api-keys/${apiKey.key}`, { method: "DELETE" });
      toast.success("API key removed");
      onRefresh();
    } catch (e: any) { toast.error(e.message); } finally { setDeleting(false); }
  };

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${apiKey.is_set ? "border-slate-700" : "border-slate-800"}`}>
      <div className="flex items-center justify-between p-4 bg-slate-900/30 cursor-pointer" onClick={() => setExpanded(e => !e)}>
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${apiKey.is_set ? "bg-emerald-500/15" : "bg-slate-800"}`}>
            {apiKey.is_set ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-slate-500" />}
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-200">{meta.label}</p>
            <p className="text-[11px] text-slate-500">{meta.desc}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {apiKey.is_set && apiKey.masked_value && (
            <code className="text-[11px] text-slate-400 font-mono hidden sm:block">{apiKey.masked_value}</code>
          )}
          {!apiKey.is_set && <span className="text-[11px] text-amber-400">Not configured</span>}
          <a href={meta.docUrl} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="text-slate-500 hover:text-slate-300">
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {expanded && (
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 space-y-3">
          <div className="relative">
            <input type={show ? "text" : "password"} value={newValue} onChange={(e) => setNewValue(e.target.value)}
              placeholder={apiKey.is_set ? "Enter new key to replace current..." : meta.placeholder}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 pr-10 focus:outline-none focus:border-indigo-500" />
            <button type="button" onClick={() => setShow(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
              {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <div className="flex gap-2">
            <Button onClick={save} disabled={saving || !newValue.trim()} className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs flex-1"
              leftIcon={saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}>
              {saving ? "Saving..." : apiKey.is_set ? "Update Key" : "Save Key"}
            </Button>
            {apiKey.is_set && (
              <Button variant="ghost" onClick={remove} disabled={deleting} className="text-red-400 hover:text-red-300 text-xs"
                leftIcon={<Trash2 className="w-3.5 h-3.5" />}>Remove</Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ApiKeysPage() {
  const toast = useToast();
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try { setKeys(await fetchApi<ApiKey[]>("/admin/api-keys")); } catch { toast.error("Failed to load API keys"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const categories = [...Array.from(new Set(keys.map((k) => k.category)))];
  const configuredCount = keys.filter((k) => k.is_set).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
          <Key className="w-5 h-5 text-amber-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">API Keys & Secrets</h1>
          <p className="text-slate-400 text-sm">{configuredCount}/{keys.length} configured · keys are AES-256 encrypted at rest</p>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Configured", value: configuredCount, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
          { label: "Missing", value: keys.length - configuredCount, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
          { label: "Total Keys", value: keys.length, color: "text-slate-300", bg: "bg-slate-800 border-slate-700" },
        ].map((s) => (
          <Card key={s.label} className={`p-4 text-center border ${s.bg}`}>
            <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-slate-500">{s.label}</p>
          </Card>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : (
        <div className="space-y-6">
          {categories.map((cat) => (
            <div key={cat}>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">{cat}</p>
              <div className="space-y-2">
                {keys.filter((k) => k.category === cat).map((key) => (
                  <ApiKeyRow key={key.key} apiKey={key} onRefresh={load} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
