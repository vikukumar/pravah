"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SocialIcon } from "@/components/ui/social-icon";
import { useToast } from "@/components/ui/toast";
import { Shield, Key, Save, CheckCircle2, Lock, Eye, EyeOff, ExternalLink } from "lucide-react";

interface SocialCreds {
  client_id: string;
  client_secret?: string;
  has_secret: boolean;
  redirect_uri: string;
  is_enabled: boolean;
}

export default function AdminSocialKeysPage() {
  const toast = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  const [creds, setCreds] = useState<Record<string, SocialCreds>>({
    x: { client_id: "", has_secret: false, redirect_uri: "", is_enabled: true },
    facebook: { client_id: "", has_secret: false, redirect_uri: "", is_enabled: true },
    instagram: { client_id: "", has_secret: false, redirect_uri: "", is_enabled: true },
    linkedin: { client_id: "", has_secret: false, redirect_uri: "", is_enabled: true },
    youtube: { client_id: "", has_secret: false, redirect_uri: "", is_enabled: true },
  });

  const [newSecrets, setNewSecrets] = useState<Record<string, string>>({
    x: "",
    facebook: "",
    instagram: "",
    linkedin: "",
    youtube: "",
  });

  const fetchCredentials = async () => {
    setIsLoading(true);
    try {
      const data = await fetchApi<Record<string, SocialCreds>>("/admin/social/credentials");
      setCreds(data);
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCredentials();
  }, []);

  const handleFieldChange = (provider: string, field: string, value: any) => {
    setCreds((prev) => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        [field]: value,
      },
    }));
  };

  const handleSecretChange = (provider: string, value: string) => {
    setNewSecrets((prev) => ({
      ...prev,
      [provider]: value,
    }));
  };

  const toggleShowSecret = (provider: string) => {
    setShowSecrets((prev) => ({
      ...prev,
      [provider]: !prev[provider],
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload: Record<string, any> = {};

      for (const [provider, data] of Object.entries(creds)) {
        payload[provider] = {
          client_id: data.client_id,
          redirect_uri: data.redirect_uri,
          is_enabled: data.is_enabled,
        };
        if (newSecrets[provider]?.trim()) {
          payload[provider].client_secret = newSecrets[provider].trim();
        }
      }

      await fetchApi("/admin/social/credentials", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      toast.success("Credentials Saved!", "All social OAuth keys and secrets have been encrypted and stored.");
      setNewSecrets({ x: "", facebook: "", instagram: "", linkedin: "", youtube: "" });
      fetchCredentials();
    } catch (err: any) {
      toast.error("Save Failed", err.message || "Failed to update OAuth credentials.");
    } finally {
      setIsSaving(false);
    }
  };

  const providers = [
    {
      id: "x",
      name: "X (Twitter)",
      desc: "Requires OAuth 2.0 Client ID & Client Secret from Twitter Developer Portal.",
      docUrl: "https://developer.x.com/en/portal/dashboard",
    },
    {
      id: "facebook",
      name: "Meta Facebook Pages",
      desc: "Requires App ID & App Secret from Meta for Developers with Pages permissions.",
      docUrl: "https://developers.facebook.com/apps/",
    },
    {
      id: "instagram",
      name: "Instagram Business",
      desc: "Configured via Meta App with Instagram Graph API permissions.",
      docUrl: "https://developers.facebook.com/docs/instagram-api",
    },
    {
      id: "linkedin",
      name: "LinkedIn Pages & Profiles",
      desc: "Requires Client ID & Client Secret with Share on LinkedIn and Sign In with LinkedIn.",
      docUrl: "https://www.linkedin.com/developers/apps",
    },
    {
      id: "youtube",
      name: "Google YouTube Data API",
      desc: "Requires OAuth 2.0 Client ID & Client Secret from Google Cloud Console.",
      docUrl: "https://console.cloud.google.com/apis/credentials",
    },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
          <Shield className="w-6 h-6 text-indigo-400" /> Social Media OAuth Application Keys & Secrets
        </h1>
        <p className="text-xs text-slate-400">
          Configure third-party developer app client IDs and client secrets. All secrets are stored with AES-256 Fernet encryption at rest.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        <div className="space-y-4">
          {providers.map((p) => {
            const current = creds[p.id] || { client_id: "", has_secret: false, redirect_uri: "", is_enabled: true };
            const isSecretVisible = showSecrets[p.id];

            return (
              <Card key={p.id} className="p-6 space-y-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center p-2">
                      <SocialIcon platform={p.id} className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-slate-100">{p.name}</h3>
                        <Badge variant={current.has_secret ? "success" : "warning"}>
                          {current.has_secret ? "Secret Active" : "No Secret"}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-slate-400">{p.desc}</p>
                    </div>
                  </div>

                  <a
                    href={p.docUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 shrink-0"
                  >
                    Developer Console <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Client ID / App ID"
                    placeholder="Enter Client ID"
                    value={current.client_id}
                    onChange={(e) => handleFieldChange(p.id, "client_id", e.target.value)}
                  />

                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-slate-300">
                      Client Secret / App Secret
                    </label>
                    <div className="relative">
                      <input
                        type={isSecretVisible ? "text" : "password"}
                        placeholder={current.has_secret ? "•••••••••••••••• (Configured — enter new to replace)" : "Enter Client Secret"}
                        value={newSecrets[p.id] || ""}
                        onChange={(e) => handleSecretChange(p.id, e.target.value)}
                        className="w-full bg-slate-900/80 border border-slate-800 rounded-xl px-3.5 py-2.5 pr-10 text-xs text-slate-100 placeholder:text-slate-500 font-mono focus:outline-none focus:border-indigo-500/60"
                      />
                      <button
                        type="button"
                        onClick={() => toggleShowSecret(p.id)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                      >
                        {isSecretVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="pt-2">
                  <Input
                    label="OAuth Callback / Redirect URI"
                    value={current.redirect_uri || `https://pravah.app/api/v1/social/callback/${p.id}`}
                    onChange={(e) => handleFieldChange(p.id, "redirect_uri", e.target.value)}
                  />
                </div>
              </Card>
            );
          })}
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" variant="glow" isLoading={isSaving} leftIcon={<Save className="w-4 h-4" />}>
            Save All OAuth Credentials
          </Button>
        </div>
      </form>
    </div>
  );
}
