"use client";
import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { Bell, Mail, Save, RefreshCw, Send, CheckCircle, Eye, EyeOff } from "lucide-react";

interface EmailSettings { smtp_host: string; smtp_port: string; smtp_user: string; smtp_from_name: string; smtp_from_email: string; smtp_use_tls: string; email_provider: string; sendgrid_api_key: string; mailgun_api_key: string; mailgun_domain: string; email_enabled: string; }

function SecretInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input type={show ? "text" : "password"} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 pr-10 focus:outline-none focus:border-indigo-500" />
      <button type="button" onClick={() => setShow(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200">
        {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
      </button>
    </div>
  );
}

function TextField({ label, value, onChange, type = "text", placeholder, hint }: { label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string; hint?: string }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-slate-300">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500" />
      {hint && <p className="text-[10px] text-slate-500">{hint}</p>}
    </div>
  );
}

export default function NotificationsPage() {
  const toast = useToast();
  const [settings, setSettings] = useState<EmailSettings>({ smtp_host: "", smtp_port: "587", smtp_user: "", smtp_from_name: "Pravah", smtp_from_email: "", smtp_use_tls: "true", email_provider: "smtp", sendgrid_api_key: "", mailgun_api_key: "", mailgun_domain: "", email_enabled: "true" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const [testing, setTesting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchApi<EmailSettings>("/admin/email-settings");
      setSettings(prev => ({ ...prev, ...data }));
      setTestEmail("");
    } catch { toast.error("Failed to load email settings"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async () => {
    setSaving(true);
    try {
      await fetchApi("/admin/email-settings", { method: "POST", body: JSON.stringify(settings) });
      toast.success("Email settings saved!");
    } catch (e: any) { toast.error(e.message); } finally { setSaving(false); }
  };

  const sendTest = async () => {
    if (!testEmail) { toast.error("Enter a test email address"); return; }
    setTesting(true);
    try {
      await fetchApi("/admin/email-settings/test", { method: "POST", body: JSON.stringify({ to_email: testEmail }) });
      toast.success("Test email sent!");
    } catch (e: any) { toast.error(e.message); } finally { setTesting(false); }
  };

  const upd = (key: keyof EmailSettings) => (v: string) => setSettings(p => ({ ...p, [key]: v }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
            <Bell className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Email & Notifications</h1>
            <p className="text-slate-400 text-sm">Configure outbound email for platform notifications</p>
          </div>
        </div>
        <Button onClick={save} disabled={saving} className="bg-indigo-600 hover:bg-indigo-500 text-white" leftIcon={saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}>
          {saving ? "Saving..." : "Save Settings"}
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Provider Selection */}
          <Card className="p-5 space-y-5 lg:col-span-2">
            <div className="flex items-center gap-2 mb-1">
              <Mail className="w-4 h-4 text-blue-400" />
              <h2 className="text-sm font-bold text-white">Email Provider</h2>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {(["smtp", "sendgrid", "mailgun"] as const).map((provider) => (
                <button key={provider} type="button" onClick={() => upd("email_provider")(provider)}
                  className={`p-3 rounded-xl border text-xs font-semibold capitalize transition-all ${settings.email_provider === provider ? "bg-blue-600/20 border-blue-500/60 text-blue-300" : "bg-slate-900/50 border-slate-700 text-slate-400 hover:border-slate-500"}`}>
                  {provider === "smtp" ? "📮 Custom SMTP" : provider === "sendgrid" ? "📧 SendGrid" : "📬 Mailgun"}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <button type="button" role="switch" aria-checked={settings.email_enabled === "true"} onClick={() => upd("email_enabled")(settings.email_enabled === "true" ? "false" : "true")}
                  className={`relative inline-flex h-5 w-9 rounded-full border-2 border-transparent transition-colors ${settings.email_enabled === "true" ? "bg-blue-600" : "bg-slate-700"}`}>
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${settings.email_enabled === "true" ? "translate-x-4" : "translate-x-0"}`} />
                </button>
                <span className="text-xs text-slate-300">Enable email delivery</span>
              </label>
            </div>
          </Card>

          {/* SMTP Config */}
          {settings.email_provider === "smtp" && (
            <Card className="p-5 space-y-4">
              <h2 className="text-sm font-bold text-white flex items-center gap-2"><span>📮</span> SMTP Configuration</h2>
              <TextField label="SMTP Host" value={settings.smtp_host} onChange={upd("smtp_host")} placeholder="smtp.gmail.com" />
              <div className="grid grid-cols-2 gap-3">
                <TextField label="Port" value={settings.smtp_port} onChange={upd("smtp_port")} placeholder="587" />
                <div className="space-y-1.5">
                  <label className="block text-xs font-medium text-slate-300">Use TLS</label>
                  <select value={settings.smtp_use_tls} onChange={(e) => upd("smtp_use_tls")(e.target.value)} className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500">
                    <option value="true">Yes (STARTTLS)</option>
                    <option value="false">No</option>
                    <option value="ssl">SSL/TLS</option>
                  </select>
                </div>
              </div>
              <TextField label="SMTP Username" value={settings.smtp_user} onChange={upd("smtp_user")} placeholder="your@email.com" />
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">SMTP Password</label>
                <SecretInput value="" onChange={() => {}} placeholder="Enter to update password" />
              </div>
            </Card>
          )}

          {/* SendGrid Config */}
          {settings.email_provider === "sendgrid" && (
            <Card className="p-5 space-y-4">
              <h2 className="text-sm font-bold text-white flex items-center gap-2"><span>📧</span> SendGrid Configuration</h2>
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">SendGrid API Key</label>
                <SecretInput value={settings.sendgrid_api_key} onChange={upd("sendgrid_api_key")} placeholder="SG.xxxxxxxxxxxxxx" />
                <p className="text-[10px] text-slate-500">Get from <a href="https://app.sendgrid.com/settings/api_keys" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">SendGrid API Keys</a></p>
              </div>
            </Card>
          )}

          {/* Mailgun Config */}
          {settings.email_provider === "mailgun" && (
            <Card className="p-5 space-y-4">
              <h2 className="text-sm font-bold text-white flex items-center gap-2"><span>📬</span> Mailgun Configuration</h2>
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Mailgun API Key</label>
                <SecretInput value={settings.mailgun_api_key} onChange={upd("mailgun_api_key")} placeholder="key-xxxxxxxxxxxx" />
              </div>
              <TextField label="Mailgun Domain" value={settings.mailgun_domain} onChange={upd("mailgun_domain")} placeholder="mail.yourdomain.com" />
            </Card>
          )}

          {/* Sender Identity */}
          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-white">Sender Identity</h2>
            <TextField label="From Name" value={settings.smtp_from_name} onChange={upd("smtp_from_name")} placeholder="Pravah Platform" />
            <TextField label="From Email" value={settings.smtp_from_email} onChange={upd("smtp_from_email")} placeholder="noreply@yourdomain.com" type="email" hint="This is the address users will receive emails from" />
          </Card>

          {/* Test Email */}
          <Card className="p-5 lg:col-span-2">
            <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2"><Send className="w-4 h-4 text-blue-400" /> Send Test Email</h2>
            <div className="flex gap-3">
              <input type="email" value={testEmail} onChange={(e) => setTestEmail(e.target.value)} placeholder="Enter recipient email address..." className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-blue-500" />
              <Button onClick={sendTest} disabled={testing || !testEmail} className="bg-blue-600 hover:bg-blue-500 text-white whitespace-nowrap" leftIcon={testing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}>
                {testing ? "Sending..." : "Send Test"}
              </Button>
            </div>
            <p className="text-[10px] text-slate-500 mt-2">Save your configuration first, then send a test email to verify delivery is working.</p>
          </Card>
        </div>
      )}
    </div>
  );
}
