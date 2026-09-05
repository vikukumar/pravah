"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { SocialIcon } from "@/components/ui/social-icon";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { formatDate } from "@/lib/utils";
import {
  Share2,
  Plus,
  Trash2,
  Bot,
  Loader2,
  AlertTriangle,
  ShieldCheck,
} from "lucide-react";

interface SocialAccount {
  id: string;
  provider: string;
  account_id: string;
  account_name: string;
  username?: string;
  profile_image_url?: string;
  is_connected: boolean;
  health_status: string;
  last_sync_at?: string;
  pages_count?: number;
  created_at: string;
}

interface AvailableProvider {
  id: string;
  name: string;
  display_name: string;
  icon_url: string;
  configured: boolean;
  supports_pages: boolean;
}

interface OAuthUrlResponse {
  configured: boolean;
  provider: string;
  authorization_url: string | null;
  message?: string;
  state: string | null;
}

export default function SocialAccountsPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [providers, setProviders] = useState<AvailableProvider[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [connectingProvider, setConnectingProvider] = useState<string | null>(null);

  // Profile Summary Modal
  const [selectedSummary, setSelectedSummary] = useState<any>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);

  // Connect Modal
  const [connectModalOpen, setConnectModalOpen] = useState(false);
  const [disconnectAccountId, setDisconnectAccountId] = useState<string | null>(null);
  const [removeAccountId, setRemoveAccountId] = useState<string | null>(null);

  // History
  const [showHistory, setShowHistory] = useState(false);
  const [historyAccounts, setHistoryAccounts] = useState<any[]>([]);

  // Post sync
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);

  // OAuth popup reference
  const oauthPopupRef = useRef<Window | null>(null);
  const oauthPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const [accRes, provRes] = await Promise.all([
        fetchApi<SocialAccount[]>("/social/accounts"),
        fetchApi<AvailableProvider[]>("/social/providers/available"),
      ]);
      setAccounts(accRes);
      setProviders(provRes);
    } catch {
      setAccounts([]);
      setProviders([]);
    } finally {
      setIsLoading(false);
    }
  }, [activeOrg]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Listen for OAuth popup postMessage
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      const { type, provider, account_name, error } = event.data || {};

      if (type === "SOCIAL_OAUTH_SUCCESS") {
        setConnectingProvider(null);
        toast.success("Account Connected!", `${provider.toUpperCase()} account "${account_name}" linked successfully.`);
        setConnectModalOpen(false);
        fetchData();
        if (oauthPollRef.current) clearInterval(oauthPollRef.current);
      } else if (type === "SOCIAL_OAUTH_ERROR") {
        setConnectingProvider(null);
        toast.error("Connection Failed", error || "OAuth authorization was denied or failed.");
        if (oauthPollRef.current) clearInterval(oauthPollRef.current);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => {
      window.removeEventListener("message", handleMessage);
      if (oauthPollRef.current) clearInterval(oauthPollRef.current);
    };
  }, [fetchData, toast]);

  const handleConnectProvider = async (providerName: string) => {
    setConnectingProvider(providerName);

    try {
      // Build callback URL pointing to our OAuth callback endpoint
      const callbackUrl = `${window.location.origin}/api/v1/social/callback/${providerName}`;

      const result = await fetchApi<OAuthUrlResponse>(
        `/social/oauth-url?provider=${providerName}&redirect_uri=${encodeURIComponent(callbackUrl)}`
      );

      if (!result.configured || !result.authorization_url) {
        toast.error(
          "Provider Not Configured",
          result.message || `${providerName} credentials have not been set up by the administrator.`
        );
        setConnectingProvider(null);
        return;
      }

      // Open real OAuth authorization URL in popup window
      const popupWidth = 600;
      const popupHeight = 700;
      const left = window.screenX + (window.outerWidth - popupWidth) / 2;
      const top = window.screenY + (window.outerHeight - popupHeight) / 2;

      const popup = window.open(
        result.authorization_url,
        `oauth_${providerName}`,
        `width=${popupWidth},height=${popupHeight},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes,resizable=yes`
      );

      if (!popup) {
        toast.error(
          "Popup Blocked",
          "Please allow popups for this site to connect your social account."
        );
        setConnectingProvider(null);
        return;
      }

      oauthPopupRef.current = popup;

      // Poll for popup close (fallback if postMessage not received)
      oauthPollRef.current = setInterval(() => {
        if (popup.closed) {
          clearInterval(oauthPollRef.current!);
          setConnectingProvider(null);
          // Refresh data in case connection succeeded
          fetchData();
        }
      }, 500);

    } catch (err: any) {
      setConnectingProvider(null);
      toast.error("Connection Error", err.message || "Could not initiate OAuth flow.");
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
      await fetchApi(`/social/accounts/${disconnectAccountId}/disconnect`, { method: "POST" });
      toast.success("Account Disconnected", "Tokens invalidated. Account history preserved. You can reconnect anytime.");
      setDisconnectAccountId(null);
      fetchData();
    } catch (err: any) {
      toast.error("Disconnect Failed", err.message || "Failed to disconnect account.");
    }
  };

  const handleRemoveAccount = async () => {
    if (!removeAccountId) return;
    try {
      await fetchApi(`/social/accounts/${removeAccountId}`, { method: "DELETE" });
      toast.success("Account Removed", "Account hidden from workspace. Full history preserved in backend.");
      setRemoveAccountId(null);
      fetchData();
    } catch (err: any) {
      toast.error("Remove Failed", err.message || "Failed to remove account.");
    }
  };

  const handleSyncPosts = async (accountId: string) => {
    setSyncingAccountId(accountId);
    try {
      const res = await fetchApi<any>(`/social/accounts/${accountId}/sync-posts`, { method: "POST" });
      if (res.skipped) {
        toast.info("Sync Skipped", res.reason);
      } else {
        toast.success("Posts Synced", `Fetched ${res.synced} new posts. Total cached: ${res.total_cached || 0}.`);
      }
    } catch (err: any) {
      toast.error("Sync Failed", err.message || "Could not sync posts.");
    } finally {
      setSyncingAccountId(null);
    }
  };

  const handleViewHistory = async () => {
    setShowHistory(true);
    try {
      const data = await fetchApi<any[]>("/social/accounts/history");
      setHistoryAccounts(data);
    } catch {
      setHistoryAccounts([]);
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
            Connect via official OAuth 2.0. Tokens are AES-256 encrypted at rest.
          </p>
        </div>
        <Button variant="glow" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setConnectModalOpen(true)}>
          Connect Social Account
        </Button>
      </div>

      {/* Accounts List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          <div className="col-span-full flex justify-center py-16">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : accounts.length === 0 ? (
          <Card className="col-span-full text-center py-16 space-y-3">
            <Share2 className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-200">No social channels connected yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              {providers.length === 0
                ? "No social platforms are currently available. The administrator has not configured any social media integrations yet."
                : `Connect your ${providers.map((p) => p.display_name).join(", ")} account${providers.length > 1 ? "s" : ""} to get started.`}
            </p>
            {providers.length > 0 && (
              <Button variant="outline" size="sm" onClick={() => setConnectModalOpen(true)}>
                Connect Channels
              </Button>
            )}
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
                    {acc.health_status === "healthy" ? "Active" : acc.health_status}
                  </Badge>
                </div>

                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1.5 text-xs">
                  <div className="flex justify-between text-[11px] text-slate-400">
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
                    <span>Token Security</span>
                    <span className="text-emerald-400 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" /> AES-256 Encrypted
                    </span>
                  </div>
                  {acc.pages_count !== undefined && acc.pages_count > 0 && (
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Linked Pages</span>
                      <span className="text-slate-200">{acc.pages_count}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Bot className="w-3.5 h-3.5 text-indigo-400" />}
                  onClick={() => handleViewProfileSummary(acc.id)}
                  isLoading={isLoadingSummary}
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
        onClose={() => {
          setConnectModalOpen(false);
          setConnectingProvider(null);
        }}
        title="Connect Social Channel"
        description="Select a platform to connect via official OAuth 2.0 authorization."
      >
        <div className="space-y-3 pt-2">
          {providers.length === 0 ? (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <p className="text-xs text-amber-300">
                No social platforms have been configured by the administrator. Contact your admin to enable social media integrations.
              </p>
            </div>
          ) : (
            providers.map((prov) => (
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
                      Official OAuth 2.0 • Encrypted storage
                    </p>
                  </div>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleConnectProvider(prov.name)}
                  isLoading={connectingProvider === prov.name}
                  disabled={connectingProvider !== null}
                >
                  {connectingProvider === prov.name ? "Authorizing..." : "Connect"}
                </Button>
              </div>
            ))
          )}
        </div>
      </Modal>

      {/* Profile Summary Modal */}
      <Modal
        isOpen={!!selectedSummary}
        onClose={() => setSelectedSummary(null)}
        title="AI Brand Profile Intelligence"
        description="Autonomous profile signals synthesized from account data."
        maxWidth="lg"
      >
        {selectedSummary && (
          <div className="space-y-4 text-xs">
            {selectedSummary.brand_identity && (
              <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-1">
                <span className="text-[10px] uppercase font-bold text-indigo-400">Brand Identity</span>
                <p className="text-slate-200">{selectedSummary.brand_identity}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Tone of Voice</span>
                <p className="text-slate-200">{selectedSummary.tone || "Pending analysis"}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Category</span>
                <p className="text-slate-200">{selectedSummary.business_category || "General"}</p>
              </div>
            </div>

            {selectedSummary.content_themes?.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] uppercase font-semibold text-slate-400">Content Themes</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedSummary.content_themes.map((t: string, idx: number) => (
                    <span key={idx} className="bg-slate-800 px-2 py-0.5 rounded text-[11px] text-slate-200">{t}</span>
                  ))}
                </div>
              </div>
            )}

            {selectedSummary.description && (
              <p className="text-slate-400 text-[11px] leading-relaxed">{selectedSummary.description}</p>
            )}
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
