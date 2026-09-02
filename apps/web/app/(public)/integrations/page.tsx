"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SocialIcon } from "@/components/ui/social-icon";
import { SocialProvider } from "@pravah/shared-types";
import { ArrowRight, Check, Share2, Bot, Layers } from "lucide-react";

export default function IntegrationsPage() {
  const [providers, setProviders] = useState<SocialProvider[]>([]);

  useEffect(() => {
    fetchApi<SocialProvider[]>("/social/providers")
      .then((data) => setProviders(data))
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <Badge variant="info">Ecosystem & Platforms</Badge>
        <h1 className="text-4xl font-extrabold text-slate-100">Official Social & AI Integrations</h1>
        <p className="text-xs sm:text-sm text-slate-400">
          Connect your accounts with zero friction using official OAuth 2.0 authorization flows.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {providers.map((p) => (
          <Card key={p.id} hoverEffect className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center p-2">
                  <SocialIcon platform={p.name} className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-slate-100">{p.display_name}</h3>
              </div>
              <Badge variant={p.is_enabled ? "success" : "default"}>
                {p.is_enabled ? "Active" : "Coming Soon"}
              </Badge>
            </div>
            <p className="text-xs text-slate-400">
              Max character limit: <span className="font-mono text-indigo-300">{p.max_char_limit.toLocaleString()}</span> chars
            </p>

            <div className="space-y-2 text-xs text-slate-300 pt-2 border-t border-slate-800">
              <p className="font-semibold text-slate-200">Supported Formats:</p>
              <div className="flex flex-wrap gap-1.5">
                {p.supports_text && <span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">Text</span>}
                {p.supports_image && <span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">Images</span>}
                {p.supports_video && <span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">Videos</span>}
                {p.supports_carousel && <span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">Carousels</span>}
                {p.supports_pages && <span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">Brand Pages</span>}
                {p.supports_analytics && <span className="bg-slate-800 px-2 py-0.5 rounded text-[11px]">Metrics API</span>}
              </div>
            </div>
          </Card>
        ))}

        <Card hoverEffect className="space-y-4 border-indigo-500/30 bg-indigo-950/20">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-100">OpenRouter (400+ AI Models)</h3>
            <Badge variant="purple">AI Provider</Badge>
          </div>
          <p className="text-xs text-slate-400">
            Access Claude 3.5 Sonnet, GPT-4o, Llama 3 70B, Gemini 1.5 Pro, and Mistral through unified routing.
          </p>
          <div className="text-xs text-indigo-300 font-semibold pt-2">
            ✓ Automated Brand Voice Injection & Metering
          </div>
        </Card>
      </div>

      <div className="text-center pt-6">
        <Link href="/register">
          <Button variant="glow" size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
            Connect Your Accounts Free
          </Button>
        </Link>
      </div>
    </div>
  );
}
