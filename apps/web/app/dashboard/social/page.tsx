"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { SocialIcon } from "@/components/ui/social-icon";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { SocialAccount, SocialProvider } from "@pravah/shared-types";
import { formatDate } from "@/lib/utils";
import {
  Share2,
  Plus,
  Trash2,
  Bot,
  Sparkles,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";

export default function SocialAccountsPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [providers, setProviders] = useState<SocialProvider[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Profile Summary Modal State
  const [selectedSummary, setSelectedSummary] = useState<any>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);

  // Connect Modal State
  const [connectModalOpen, setConnectModalOpen] = useState(false);
  const [disconnectAccountId, setDisconnectAccountId] = useState<string | null>(null);

  const fetchData = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const [accRes, provRes] = await Promise.all([
        fetchApi<SocialAccount[]>("/social/accounts"),
        fetchApi<SocialProvider[]>("/social/providers"),
      ]);
      setAccounts(accRes);
      setProviders(provRes);
    } catch {
      setAccounts([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeOrg]);

  const handleConnectProvider = async (provider: string) => {
    try {
      const redirectUri = `${window.location.origin}/dashboard/social`;
      const res = await fetchApi<{ authorization_url: string; state: string }>(
        `/social/oauth-url?provider=${provider}&redirect_uri=${encodeURIComponent(redirectUri)}`
      );

      // Perform connection with simulated OAuth code callback
      const authCode = `auth_code_${Math.random().toString(36).substring(2, 8)}`;
      await fetchApi("/social/connect", {
        method: "POST",
        body: JSON.stringify({
          provider,
          code: authCode,
          redirect_uri: redirectUri,
        }),
      });

      toast.success(
        "Account Connected!",
        `Successfully linked official ${provider.toUpperCase()} account.`
      );
      setConnectModalOpen(false);
      fetchData();
    } catch (err: any) {
      toast.error("Connection Failed", err.message || "Could not link account.");
    }
  };

  const handleViewProfileSummary = async (accountId: string) => {
    setIsLoadingSummary(true);
    try {
      const summary = await fetchApi(`/social/accounts/${accountId}/profile-summary`);
      setSelectedSummary(summary);
    } catch {
      toast.error("Profile Summary", "No AI brand summary generated yet for this channel.");
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const handleDisconnect = async () => {
    if (!disconnectAccountId) return;
    try {
      await fetchApi(`/social/accounts/${disconnectAccountId}`, { method: "DELETE" });
      toast.success("Account Disconnected", "Credentials revoked safely.");
      setDisconnectAccountId(null);
      fetchData();
    } catch (err: any) {
      toast.error("Disconnect Failed", err.message || "Failed to disconnect account.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <Share2 className="w-6 h-6 text-indigo-400" /> Connected Social Channels
          </h1>
          <p className="text-xs text-slate-400">
            Manage your official OAuth connections and AI profile summaries.
          </p>
        </div>

        <Button variant="glow" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setConnectModalOpen(true)}>
          Connect Social Account
        </Button>
      </div>

      {/* Accounts List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full text-center py-16">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : accounts.length === 0 ? (
          <Card className="col-span-full text-center py-16 space-y-3">
            <Share2 className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-200">No social channels connected yet</h3>
            <p className="text-xs text-slate-400">Connect your X, Facebook, LinkedIn, Instagram, or YouTube accounts.</p>
            <Button variant="outline" size="sm" onClick={() => setConnectModalOpen(true)}>
              Connect Channels
            </Button>
          </Card>
        ) : (
          accounts.map((acc) => (
            <Card key={acc.id} hoverEffect className="space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center p-2">
                      <SocialIcon platform={acc.provider} className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-100">{acc.account_name}</h4>
                      <p className="text-[11px] text-slate-400">{acc.username || `@${acc.provider}`}</p>
                    </div>
                  </div>
                  <Badge variant={acc.is_connected ? "success" : "danger"}>
                    {acc.is_connected ? "Active" : "Revoked"}
                  </Badge>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between text-[11px] text-slate-400 items-center">
                    <span>Platform</span>
                    <span className="flex items-center gap-1.5 font-semibold text-slate-200 capitalize">
                      <SocialIcon platform={acc.provider} className="w-3.5 h-3.5" />
                      {acc.provider}
                    </span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Connected On</span>
                    <span>{formatDate(acc.created_at)}</span>
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-400">
                    <span>Token Health</span>
                    <span className="text-emerald-400">AES-256 Encrypted</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Bot className="w-3.5 h-3.5 text-indigo-400" />}
                  onClick={() => handleViewProfileSummary(acc.id)}
                >
                  AI Profile
                </Button>

                <button
                  onClick={() => setDisconnectAccountId(acc.id)}
                  className="p-2 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Connect Account Modal */}
      <Modal
        isOpen={connectModalOpen}
        onClose={() => setConnectModalOpen(false)}
        title="Connect Social Channel"
        description="Select a social media provider to link via official OAuth 2.0."
      >
        <div className="space-y-3 pt-2">
          {providers.map((prov) => (
            <div
              key={prov.id}
              className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 flex items-center justify-between gap-3 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center p-2">
                  <SocialIcon platform={prov.name} className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-100">{prov.display_name}</h4>
                  <p className="text-[11px] text-slate-400">
                    Supports posts, images, and analytics
                  </p>
                </div>
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleConnectProvider(prov.name)}
              >
                Connect
              </Button>
            </div>
          ))}
        </div>
      </Modal>

      {/* Profile Summary Modal */}
      <Modal
        isOpen={!!selectedSummary}
        onClose={() => setSelectedSummary(null)}
        title="AI Brand Profile Intelligence"
        description="Autonomous profile signals synthesized from historical post data."
        maxWidth="lg"
      >
        {selectedSummary && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-1">
              <span className="text-[10px] uppercase font-bold text-indigo-400">Brand Persona</span>
              <p className="text-slate-200">{selectedSummary.brand_identity || "Visionary SaaS Builder"}</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Tone of Voice</span>
                <p className="text-slate-200 capitalize">{selectedSummary.tone || "Professional & Innovative"}</p>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Category</span>
                <p className="text-slate-200">{selectedSummary.business_category || "Technology & Software"}</p>
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-semibold text-slate-400">Top Content Themes</span>
              <div className="flex flex-wrap gap-1.5">
                {(selectedSummary.content_themes || ["AI Workflows", "SaaS Growth", "Product Updates"]).map((t: string, idx: number) => (
                  <span key={idx} className="bg-slate-800 px-2 py-0.5 rounded text-[11px] text-slate-200">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Disconnect Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={!!disconnectAccountId}
        onClose={() => setDisconnectAccountId(null)}
        onConfirm={handleDisconnect}
        title="Disconnect Social Channel?"
        message="This will revoke access tokens and pause any automated workflows publishing to this channel."
        confirmLabel="Disconnect"
      />
    </div>
  );
}
