"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import {
  CreditCard,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Trash2,
  Save,
  RefreshCw,
  ExternalLink,
  IndianRupee,
} from "lucide-react";

interface GatewayConfig {
  key_id?: string;
  masked_key_id?: string;
  masked_secret?: string;
  webhook_secret_set?: boolean;
  is_configured?: boolean;
  is_live_mode?: boolean;
  created_at?: string;
}

interface GatewayStatus {
  razorpay: { is_configured: boolean; is_live_mode: boolean; name: string };
  cashfree: { is_configured: boolean; is_live_mode: boolean; name: string };
}

function FieldRow({
  label, value, onChange, type = "text", placeholder, secret,
}: {
  label: string; value: string; onChange: (v: string) => void;
  type?: string; placeholder?: string; secret?: boolean;
}) {
  const [show, setShow] = useState(false);
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-slate-300">{label}</label>
      <div className="relative">
        <Input
          type={secret && !show ? "password" : type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="bg-slate-900 border-slate-700 text-slate-100 pr-10"
        />
        {secret && (
          <button
            type="button"
            onClick={() => setShow((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
          >
            {show ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>
    </div>
  );
}

function GatewayCard({
  name, logo, docUrl, color, fields, onSave, onClear, existing, children,
}: {
  name: string; logo: string; docUrl: string; color: string;
  fields: { label: string; key: string; secret?: boolean; placeholder?: string }[];
  onSave: (data: Record<string, string>) => Promise<void>;
  onClear: () => Promise<void>;
  existing?: GatewayConfig | null;
  children?: React.ReactNode;
}) {
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);
  const toast = useToast();

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(form);
      toast.success(`${name} configured successfully`);
      setForm({});
    } catch (e: any) {
      toast.error(e.message || `Failed to save ${name} config`);
    } finally {
      setSaving(false);
    }
  };

  const handleClear = async () => {
    if (!confirm(`Remove ${name} configuration? This will disable payment processing.`)) return;
    setClearing(true);
    try {
      await onClear();
      toast.success(`${name} configuration removed`);
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setClearing(false);
    }
  };

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className={`p-4 border-b border-slate-800 flex items-center justify-between`}
        style={{ background: `${color}10`, borderLeft: `3px solid ${color}` }}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
            style={{ background: `${color}20` }}>
            {logo}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-200">{name}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              {existing?.is_configured ? (
                <><CheckCircle className="w-3 h-3 text-emerald-400" />
                  <span className="text-[11px] text-emerald-400">Configured</span>
                  {existing.is_live_mode ? (
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">LIVE</span>
                  ) : (
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">TEST</span>
                  )}
                </>
              ) : (
                <><AlertCircle className="w-3 h-3 text-slate-500" />
                  <span className="text-[11px] text-slate-500">Not configured</span>
                </>
              )}
            </div>
          </div>
        </div>
        <a href={docUrl} target="_blank" rel="noopener noreferrer"
          className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1">
          Docs <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      <div className="p-5 space-y-4">
        {/* Existing masked values */}
        {existing?.is_configured && (
          <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Current Configuration</p>
            {existing.masked_key_id && (
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Key ID</span>
                <code className="text-xs text-indigo-300">{existing.masked_key_id}</code>
              </div>
            )}
            {existing.masked_secret && (
              <div className="flex justify-between">
                <span className="text-xs text-slate-400">Secret</span>
                <code className="text-xs text-slate-500">{existing.masked_secret}</code>
              </div>
            )}
          </div>
        )}

        {/* Input fields */}
        <div className="space-y-3">
          {fields.map((f) => (
            <FieldRow
              key={f.key}
              label={f.label}
              value={form[f.key] || ""}
              onChange={(v) => setForm((p) => ({ ...p, [f.key]: v }))}
              secret={f.secret}
              placeholder={f.placeholder}
            />
          ))}
        </div>

        {children}

        <div className="flex gap-2 pt-2">
          <Button
            onClick={handleSave}
            disabled={saving || fields.some((f) => !form[f.key]?.trim())}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
            leftIcon={saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          >
            {saving ? "Saving..." : existing?.is_configured ? "Update Keys" : "Save Configuration"}
          </Button>
          {existing?.is_configured && (
            <Button
              variant="ghost"
              onClick={handleClear}
              disabled={clearing}
              className="text-red-400 hover:text-red-300 hover:bg-red-500/10 text-xs"
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
            >
              {clearing ? "Removing..." : "Remove"}
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

export default function PaymentGatewaysPage() {
  const toast = useToast();
  const [status, setStatus] = useState<GatewayStatus | null>(null);
  const [razorpay, setRazorpay] = useState<GatewayConfig | null>(null);
  const [cashfree, setCashfree] = useState<GatewayConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [statusData, rzData, cfData] = await Promise.all([
        fetchApi<GatewayStatus>("/admin/payment-gateways/status"),
        fetchApi<GatewayConfig>("/admin/payment-gateways/razorpay").catch(() => null),
        fetchApi<GatewayConfig>("/admin/payment-gateways/cashfree").catch(() => null),
      ]);
      setStatus(statusData);
      setRazorpay(rzData);
      setCashfree(cfData);
    } catch (e: any) {
      toast.error("Failed to load payment gateway config");
    } finally {
      setLoading(false);
    }
  }

  const saveRazorpay = async (data: Record<string, string>) => {
    await fetchApi("/admin/payment-gateways/razorpay", {
      method: "POST",
      body: JSON.stringify(data),
    });
    await loadAll();
  };

  const saveCashfree = async (data: Record<string, string>) => {
    await fetchApi("/admin/payment-gateways/cashfree", {
      method: "POST",
      body: JSON.stringify(data),
    });
    await loadAll();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <CreditCard className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">Payment Gateways</h1>
          <p className="text-slate-400 text-sm">Configure Razorpay and Cashfree for subscription billing</p>
        </div>
      </div>

      {/* Status cards */}
      {status && (
        <div className="grid grid-cols-2 gap-4">
          {(["razorpay", "cashfree"] as const).map((gw) => (
            <div key={gw} className={`p-4 rounded-xl border flex items-center gap-3 ${
              status[gw].is_configured
                ? "bg-emerald-500/5 border-emerald-500/20"
                : "bg-slate-900/50 border-slate-800"
            }`}>
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                status[gw].is_configured ? "bg-emerald-500/20" : "bg-slate-800"
              }`}>
                <IndianRupee className={`w-4 h-4 ${status[gw].is_configured ? "text-emerald-400" : "text-slate-500"}`} />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-200">{status[gw].name}</p>
                <p className={`text-[11px] ${status[gw].is_configured ? "text-emerald-400" : "text-slate-500"}`}>
                  {status[gw].is_configured
                    ? `Active · ${status[gw].is_live_mode ? "Live Mode" : "Test Mode"}`
                    : "Not configured"}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Razorpay */}
        <GatewayCard
          name="Razorpay"
          logo="🔵"
          docUrl="https://dashboard.razorpay.com/app/keys"
          color="#3395FF"
          existing={razorpay}
          fields={[
            { key: "key_id", label: "Key ID", placeholder: "rzp_live_XXXXXXXXXXXX" },
            { key: "key_secret", label: "Key Secret", secret: true, placeholder: "Enter your Razorpay secret" },
            { key: "webhook_secret", label: "Webhook Secret (optional)", secret: true, placeholder: "whsec_..." },
          ]}
          onSave={saveRazorpay}
          onClear={async () => {
            await fetchApi("/admin/payment-gateways/razorpay", { method: "DELETE" });
            await loadAll();
          }}
        >
          <div className="p-2.5 rounded-lg bg-blue-500/5 border border-blue-500/15">
            <p className="text-[10px] text-blue-400/80">
              💡 Use <strong>rzp_test_*</strong> keys for testing, <strong>rzp_live_*</strong> for production.
              Webhook URL: <code className="text-[9px] bg-slate-800 px-1 rounded">/api/webhooks/razorpay</code>
            </p>
          </div>
        </GatewayCard>

        {/* Cashfree */}
        <GatewayCard
          name="Cashfree Payments"
          logo="🟡"
          docUrl="https://merchant.cashfree.com/merchants/developer/api-keys"
          color="#F5A623"
          existing={cashfree}
          fields={[
            { key: "app_id", label: "App ID", placeholder: "CF_APP_XXXXXXXXXXXXX" },
            { key: "secret_key", label: "Secret Key", secret: true, placeholder: "Enter your Cashfree secret key" },
            { key: "webhook_secret", label: "Webhook Secret (optional)", secret: true, placeholder: "whsec_..." },
          ]}
          onSave={saveCashfree}
          onClear={async () => {
            await fetchApi("/admin/payment-gateways/cashfree", { method: "DELETE" });
            await loadAll();
          }}
        >
          <div className="p-2.5 rounded-lg bg-amber-500/5 border border-amber-500/15">
            <p className="text-[10px] text-amber-400/80">
              💡 Switch between <strong>TEST</strong> and <strong>PROD</strong> endpoints in System Settings.
              Webhook URL: <code className="text-[9px] bg-slate-800 px-1 rounded">/api/webhooks/cashfree</code>
            </p>
          </div>
        </GatewayCard>
      </div>
    </div>
  );
}
