"use client";
import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import {
  Package, Plus, Edit3, Trash2, CheckCircle, XCircle, RefreshCw,
  ToggleLeft, ToggleRight, ChevronDown, ChevronUp, Save, X, IndianRupee,
} from "lucide-react";

interface PlanFeatures { social_account_limit: number; page_limit: number; daily_post_limit: number; monthly_post_limit: number; ai_token_limit_monthly: number; image_generation_limit_monthly: number; workflow_limit: number; workflow_execution_limit_monthly: number; member_limit: number; storage_limit_mb: number; analytics_retention_days: number; has_api_access: boolean; has_custom_providers: boolean; has_sso: boolean; has_approval_workflows: boolean; has_automation: boolean; has_advanced_analytics: boolean; }
interface Plan { id: string; name: string; slug: string; description: string; price_monthly: number; price_yearly: number; currency: string; is_free: boolean; is_active: boolean; trial_days: number; razorpay_plan_id_monthly: string; razorpay_plan_id_yearly: string; cashfree_plan_id_monthly: string; cashfree_plan_id_yearly: string; features: PlanFeatures; created_at: string; }

const DEFAULT_FEATURES: PlanFeatures = { social_account_limit: 1, page_limit: 1, daily_post_limit: 5, monthly_post_limit: 30, ai_token_limit_monthly: 50000, image_generation_limit_monthly: 10, workflow_limit: 3, workflow_execution_limit_monthly: 100, member_limit: 1, storage_limit_mb: 500, analytics_retention_days: 30, has_api_access: false, has_custom_providers: false, has_sso: false, has_approval_workflows: false, has_automation: true, has_advanced_analytics: false };
const PLAN_COLORS: Record<string, string> = { Free: "#64748b", Starter: "#6366f1", Pro: "#8b5cf6", Agency: "#ec4899", Enterprise: "#f59e0b" };

function FeatureToggle({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-center justify-between py-1.5 cursor-pointer">
      <span className="text-xs text-slate-300">{label}</span>
      <button type="button" role="switch" aria-checked={value} onClick={() => onChange(!value)}
        className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors ${value ? "bg-indigo-600" : "bg-slate-700"}`}>
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${value ? "translate-x-4" : "translate-x-0"}`} />
      </button>
    </label>
  );
}

function NumberField({ label, value, onChange, suffix }: { label: string; value: number; onChange: (v: number) => void; suffix?: string }) {
  return (
    <div>
      <label className="block text-[10px] text-slate-500 mb-1">{label}</label>
      <div className="flex items-center gap-1">
        <input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))}
          className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-indigo-500" />
        {suffix && <span className="text-[10px] text-slate-500 whitespace-nowrap">{suffix}</span>}
      </div>
    </div>
  );
}

function PlanEditor({ plan, onSave, onClose }: { plan: Partial<Plan> | null; onSave: () => void; onClose: () => void }) {
  const toast = useToast();
  const isNew = !plan?.id;
  const [form, setForm] = useState({ name: plan?.name || "", description: plan?.description || "", price_monthly: plan?.price_monthly || 0, price_yearly: plan?.price_yearly || 0, currency: plan?.currency || "INR", trial_days: plan?.trial_days || 14, is_free: plan?.is_free ?? false, is_active: plan?.is_active ?? true, razorpay_plan_id_monthly: plan?.razorpay_plan_id_monthly || "", razorpay_plan_id_yearly: plan?.razorpay_plan_id_yearly || "", cashfree_plan_id_monthly: plan?.cashfree_plan_id_monthly || "", cashfree_plan_id_yearly: plan?.cashfree_plan_id_yearly || "" });
  const [feats, setFeats] = useState<PlanFeatures>(plan?.features || DEFAULT_FEATURES);
  const [saving, setSaving] = useState(false);
  const [showGateway, setShowGateway] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...form, features: feats };
      if (isNew) await fetchApi("/admin/plans", { method: "POST", body: JSON.stringify(payload) });
      else await fetchApi(`/admin/plans/${plan!.id}`, { method: "PUT", body: JSON.stringify(payload) });
      toast.success(isNew ? "Plan created!" : "Plan updated!");
      onSave();
    } catch (e: any) { toast.error(e.message); } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0f1629] border border-slate-700/60 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b border-slate-800 sticky top-0 bg-[#0f1629] z-10">
          <h2 className="text-sm font-bold text-white">{isNew ? "Create New Plan" : `Edit Plan: ${plan?.name}`}</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400"><X className="w-4 h-4" /></button>
        </div>

        <div className="p-5 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Plan Name *</label>
              <input value={form.name} onChange={(e) => setForm(p => ({ ...p, name: e.target.value }))} placeholder="e.g. Pro, Agency, Enterprise" className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Description</label>
              <textarea value={form.description} onChange={(e) => setForm(p => ({ ...p, description: e.target.value }))} rows={2} className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Monthly Price (₹)</label>
              <input type="number" value={form.price_monthly} onChange={(e) => setForm(p => ({ ...p, price_monthly: Number(e.target.value) }))} className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Yearly Price (₹)</label>
              <input type="number" value={form.price_yearly} onChange={(e) => setForm(p => ({ ...p, price_yearly: Number(e.target.value) }))} className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Trial Days</label>
              <input type="number" value={form.trial_days} onChange={(e) => setForm(p => ({ ...p, trial_days: Number(e.target.value) }))} className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Currency</label>
              <select value={form.currency} onChange={(e) => setForm(p => ({ ...p, currency: e.target.value }))} className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500">
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>
            <div className="col-span-2 flex gap-6">
              <FeatureToggle label="Free Plan" value={form.is_free} onChange={(v) => setForm(p => ({ ...p, is_free: v }))} />
              <FeatureToggle label="Active (Visible to users)" value={form.is_active} onChange={(v) => setForm(p => ({ ...p, is_active: v }))} />
            </div>
          </div>

          {/* Quotas */}
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Usage Quotas</p>
            <div className="grid grid-cols-3 gap-3">
              <NumberField label="Social Accounts" value={feats.social_account_limit} onChange={(v) => setFeats(p => ({ ...p, social_account_limit: v }))} />
              <NumberField label="Pages" value={feats.page_limit} onChange={(v) => setFeats(p => ({ ...p, page_limit: v }))} />
              <NumberField label="Team Members" value={feats.member_limit} onChange={(v) => setFeats(p => ({ ...p, member_limit: v }))} />
              <NumberField label="Daily Posts" value={feats.daily_post_limit} onChange={(v) => setFeats(p => ({ ...p, daily_post_limit: v }))} />
              <NumberField label="Monthly Posts" value={feats.monthly_post_limit} onChange={(v) => setFeats(p => ({ ...p, monthly_post_limit: v }))} />
              <NumberField label="Storage" value={feats.storage_limit_mb} onChange={(v) => setFeats(p => ({ ...p, storage_limit_mb: v }))} suffix="MB" />
              <NumberField label="AI Tokens/mo" value={feats.ai_token_limit_monthly} onChange={(v) => setFeats(p => ({ ...p, ai_token_limit_monthly: v }))} />
              <NumberField label="Image Gen/mo" value={feats.image_generation_limit_monthly} onChange={(v) => setFeats(p => ({ ...p, image_generation_limit_monthly: v }))} />
              <NumberField label="Workflows" value={feats.workflow_limit} onChange={(v) => setFeats(p => ({ ...p, workflow_limit: v }))} />
              <NumberField label="Workflow Runs/mo" value={feats.workflow_execution_limit_monthly} onChange={(v) => setFeats(p => ({ ...p, workflow_execution_limit_monthly: v }))} />
              <NumberField label="Analytics Retention" value={feats.analytics_retention_days} onChange={(v) => setFeats(p => ({ ...p, analytics_retention_days: v }))} suffix="days" />
            </div>
          </div>

          {/* Feature Flags */}
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Feature Flags</p>
            <div className="grid grid-cols-2 gap-x-8 divide-y divide-slate-800/50">
              <FeatureToggle label="API Access" value={feats.has_api_access} onChange={(v) => setFeats(p => ({ ...p, has_api_access: v }))} />
              <FeatureToggle label="Custom AI Providers" value={feats.has_custom_providers} onChange={(v) => setFeats(p => ({ ...p, has_custom_providers: v }))} />
              <FeatureToggle label="SSO Login" value={feats.has_sso} onChange={(v) => setFeats(p => ({ ...p, has_sso: v }))} />
              <FeatureToggle label="Approval Workflows" value={feats.has_approval_workflows} onChange={(v) => setFeats(p => ({ ...p, has_approval_workflows: v }))} />
              <FeatureToggle label="Automation" value={feats.has_automation} onChange={(v) => setFeats(p => ({ ...p, has_automation: v }))} />
              <FeatureToggle label="Advanced Analytics" value={feats.has_advanced_analytics} onChange={(v) => setFeats(p => ({ ...p, has_advanced_analytics: v }))} />
            </div>
          </div>

          {/* Gateway IDs */}
          <div>
            <button type="button" onClick={() => setShowGateway(!showGateway)} className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200">
              {showGateway ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} Payment Gateway Plan IDs
            </button>
            {showGateway && (
              <div className="mt-3 grid grid-cols-2 gap-3">
                {[["razorpay_plan_id_monthly", "Razorpay Monthly Plan ID"], ["razorpay_plan_id_yearly", "Razorpay Yearly Plan ID"], ["cashfree_plan_id_monthly", "Cashfree Monthly Plan ID"], ["cashfree_plan_id_yearly", "Cashfree Yearly Plan ID"]].map(([key, label]) => (
                  <div key={key}>
                    <label className="block text-[10px] text-slate-500 mb-1">{label}</label>
                    <input value={(form as any)[key]} onChange={(e) => setForm(p => ({ ...p, [key]: e.target.value }))} placeholder="plan_..." className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500" />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 p-5 border-t border-slate-800 sticky bottom-0 bg-[#0f1629]">
          <Button onClick={handleSave} disabled={saving || !form.name.trim()} className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white" leftIcon={saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}>
            {saving ? "Saving..." : isNew ? "Create Plan" : "Update Plan"}
          </Button>
          <Button variant="ghost" onClick={onClose} className="text-slate-400 hover:text-slate-200">Cancel</Button>
        </div>
      </div>
    </div>
  );
}

export default function PlansPage() {
  const toast = useToast();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [editPlan, setEditPlan] = useState<Partial<Plan> | null | undefined>(undefined);

  const load = useCallback(async () => {
    setLoading(true);
    try { setPlans(await fetchApi<Plan[]>("/admin/plans")); } catch { toast.error("Failed to load plans"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleActive = async (plan: Plan) => {
    await fetchApi(`/admin/plans/${plan.id}`, { method: "PUT", body: JSON.stringify({ is_active: !plan.is_active }) });
    toast.success(`Plan ${plan.is_active ? "deactivated" : "activated"}`);
    load();
  };

  const deletePlan = async (plan: Plan) => {
    if (!confirm(`Deactivate plan "${plan.name}"? Existing subscribers will not be affected.`)) return;
    await fetchApi(`/admin/plans/${plan.id}`, { method: "DELETE" });
    toast.success("Plan deactivated");
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Package className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Subscription Plans</h1>
            <p className="text-slate-400 text-sm">{plans.length} plans · manage pricing, features, and gateway IDs</p>
          </div>
        </div>
        <Button onClick={() => setEditPlan({})} className="bg-indigo-600 hover:bg-indigo-500 text-white" leftIcon={<Plus className="w-4 h-4" />}>New Plan</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {plans.map((plan) => {
            const color = PLAN_COLORS[plan.name] || "#6366f1";
            return (
              <Card key={plan.id} className={`overflow-hidden transition-all ${!plan.is_active ? "opacity-50" : ""}`}>
                <div className="p-4 border-b border-slate-800" style={{ borderLeft: `3px solid ${color}` }}>
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-white">{plan.name}</h3>
                        {plan.is_free && <Badge variant="info" className="text-[10px]">Free</Badge>}
                        {!plan.is_active && <Badge className="text-[10px] bg-red-500/20 text-red-400 border-red-500/30">Inactive</Badge>}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{plan.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold" style={{ color }}>{plan.currency === "INR" ? "₹" : "$"}{plan.price_monthly}<span className="text-xs text-slate-500">/mo</span></p>
                      <p className="text-[10px] text-slate-500">{plan.currency === "INR" ? "₹" : "$"}{plan.price_yearly}/yr</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 space-y-2">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
                    {[["Social Accounts", plan.features?.social_account_limit], ["Team Members", plan.features?.member_limit], ["Monthly Posts", plan.features?.monthly_post_limit], ["AI Tokens/mo", plan.features?.ai_token_limit_monthly?.toLocaleString()], ["Workflows", plan.features?.workflow_limit], ["Storage", `${plan.features?.storage_limit_mb}MB`]].map(([label, val]) => (
                      <div key={String(label)} className="flex justify-between">
                        <span className="text-slate-500">{label}</span>
                        <span className="text-slate-300 font-medium">{val}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex flex-wrap gap-1 pt-1">
                    {plan.features?.has_api_access && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/20">API Access</span>}
                    {plan.features?.has_custom_providers && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/20">Custom AI</span>}
                    {plan.features?.has_sso && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/20">SSO</span>}
                    {plan.features?.has_advanced_analytics && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">Adv. Analytics</span>}
                    {plan.trial_days > 0 && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/20">{plan.trial_days}d Trial</span>}
                  </div>

                  <div className="flex gap-2 pt-2 border-t border-slate-800">
                    <Button variant="ghost" size="sm" className="flex-1 text-xs text-slate-400 hover:text-slate-200" leftIcon={<Edit3 className="w-3.5 h-3.5" />} onClick={() => setEditPlan(plan)}>Edit</Button>
                    <Button variant="ghost" size="sm" className="text-xs text-slate-500 hover:text-slate-200" onClick={() => toggleActive(plan)}>
                      {plan.is_active ? <ToggleRight className="w-4 h-4 text-indigo-400" /> : <ToggleLeft className="w-4 h-4" />}
                    </Button>
                    <Button variant="ghost" size="sm" className="text-xs text-red-500 hover:text-red-400" onClick={() => deletePlan(plan)}><Trash2 className="w-3.5 h-3.5" /></Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {editPlan !== undefined && (
        <PlanEditor plan={editPlan} onSave={() => { setEditPlan(undefined); load(); }} onClose={() => setEditPlan(undefined)} />
      )}
    </div>
  );
}
