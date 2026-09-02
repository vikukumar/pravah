"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { useAuth } from "@/providers/auth-provider";
import { formatDate } from "@/lib/utils";
import {
  Settings as SettingsIcon,
  Shield,
  Key,
  Smartphone,
  Save,
  Trash2,
  CheckCircle2,
  Lock,
} from "lucide-react";

export default function SettingsPage() {
  const { activeOrg, refreshOrganisations } = useOrganisation();
  const { user, refreshUser } = useAuth();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState<"workspace" | "security">("workspace");

  // Workspace form state
  const [orgName, setOrgName] = useState("");
  const [website, setWebsite] = useState("");
  const [industry, setIndustry] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [isSavingOrg, setIsSavingOrg] = useState(false);

  // Security / 2FA State
  const [twoFactorData, setTwoFactorData] = useState<any>(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [isSettingUp2FA, setIsSettingUp2FA] = useState(false);
  const [sessions, setSessions] = useState<any[]>([]);

  useEffect(() => {
    if (activeOrg) {
      setOrgName(activeOrg.name || "");
      setWebsite(activeOrg.website || "");
      setIndustry(activeOrg.industry || "");
      setTimezone(activeOrg.timezone || "UTC");
    }
  }, [activeOrg]);

  useEffect(() => {
    fetchApi<any[]>("/auth/sessions")
      .then((data) => setSessions(data))
      .catch(() => {});
  }, []);

  const handleSaveWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingOrg(true);
    try {
      await fetchApi("/organisations/active", {
        method: "PATCH",
        body: JSON.stringify({
          name: orgName,
          website,
          industry,
          timezone,
        }),
      });

      toast.success("Settings Saved", "Brand profile updated successfully.");
      refreshOrganisations();
    } catch (err: any) {
      toast.error("Save Failed", err.message || "Failed to update workspace settings.");
    } finally {
      setIsSavingOrg(false);
    }
  };

  const handleStart2FASetup = async () => {
    try {
      const data = await fetchApi<any>("/auth/2fa/setup");
      setTwoFactorData(data);
      setIsSettingUp2FA(true);
    } catch (err: any) {
      toast.error("2FA Setup Error", err.message || "Could not generate TOTP secret.");
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchApi("/auth/2fa/verify", {
        method: "POST",
        body: JSON.stringify({ code: twoFactorCode }),
      });

      toast.success("2FA Enabled!", "Two-factor authentication is now active on your account.");
      setIsSettingUp2FA(false);
      setTwoFactorData(null);
      refreshUser();
    } catch (err: any) {
      toast.error("Verification Failed", err.message || "Invalid authenticator code.");
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await fetchApi(`/auth/sessions/${sessionId}`, { method: "DELETE" });
      toast.success("Session Revoked", "Logged out from selected device.");
      setSessions(sessions.filter((s) => s.id !== sessionId));
    } catch (err: any) {
      toast.error("Revoke Failed", err.message || "Could not revoke session.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <SettingsIcon className="w-6 h-6 text-indigo-400" /> Workspace & Security Settings
          </h1>
          <p className="text-xs text-slate-400">
            Configure brand metadata, multi-factor authentication, and security credentials.
          </p>
        </div>

        <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => setActiveTab("workspace")}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "workspace" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Brand Profile
          </button>
          <button
            onClick={() => setActiveTab("security")}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "security" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Security & 2FA
          </button>
        </div>
      </div>

      {activeTab === "workspace" ? (
        <Card className="p-6 space-y-6">
          <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3">
            Brand Workspace Information
          </h3>

          <form onSubmit={handleSaveWorkspace} className="space-y-4">
            <Input
              label="Brand / Organisation Name"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              required
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Website URL"
                placeholder="https://company.com"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
              />
              <Input
                label="Industry / Category"
                placeholder="SaaS / Technology"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
              />
            </div>

            <Input
              label="Timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            />

            <div className="flex justify-end pt-4 border-t border-slate-800">
              <Button type="submit" variant="glow" size="sm" isLoading={isSavingOrg} leftIcon={<Save className="w-4 h-4" />}>
                Save Changes
              </Button>
            </div>
          </form>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* 2FA Section */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-400" /> Two-Factor Authentication (TOTP)
                </h3>
                <p className="text-xs text-slate-400">
                  Protect your account with Google Authenticator or Authy.
                </p>
              </div>
              <Badge variant={user?.twoFactorEnabled ? "success" : "warning"}>
                {user?.twoFactorEnabled ? "2FA Active" : "Disabled"}
              </Badge>
            </div>

            {!user?.twoFactorEnabled ? (
              <div className="pt-2">
                <Button variant="glow" size="sm" onClick={handleStart2FASetup}>
                  Enable Two-Factor Authentication
                </Button>
              </div>
            ) : (
              <p className="text-xs text-emerald-400">
                ✓ Two-factor authentication is protecting all login attempts.
              </p>
            )}
          </Card>

          {/* Active Sessions */}
          <Card className="p-6 space-y-4">
            <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3">
              Active Sessions ({sessions.length})
            </h3>
            <div className="divide-y divide-slate-800/60">
              {sessions.map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between gap-4 text-xs">
                  <div className="space-y-0.5">
                    <p className="font-semibold text-slate-200">
                      {s.ip_address} • <span className="text-slate-400 font-normal">{s.user_agent.substring(0, 40)}...</span>
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Created on {formatDate(s.created_at)}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleRevokeSession(s.id)}>
                    Revoke
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* 2FA Setup Modal */}
      <Modal
        isOpen={isSettingUp2FA}
        onClose={() => setIsSettingUp2FA(false)}
        title="Set Up Google Authenticator"
        description="Scan the QR code with your authenticator app and enter the 6-digit code."
      >
        {twoFactorData && (
          <form onSubmit={handleVerify2FA} className="space-y-4 text-center">
            {twoFactorData.qr_code_svg && (
              <div
                className="w-48 h-48 mx-auto bg-white p-2 rounded-xl flex items-center justify-center"
                dangerouslySetInnerHTML={{ __html: twoFactorData.qr_code_svg }}
              />
            )}

            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-indigo-300">
              Secret: {twoFactorData.secret}
            </div>

            <Input
              label="Enter 6-Digit Authenticator Code"
              placeholder="123456"
              value={twoFactorCode}
              onChange={(e) => setTwoFactorCode(e.target.value)}
              required
            />

            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsSettingUp2FA(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="glow" size="sm">
                Verify & Activate
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
}
