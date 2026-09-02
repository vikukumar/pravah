"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { Building } from "lucide-react";

export default function AdminOrganisationsPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchApi<any[]>("/admin/organisations")
      .then((data) => setOrgs(data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100">All Brand Workspaces</h1>
        <p className="text-xs text-slate-400">Multi-tenant organisation boundaries, publishing flags, and subscription levels.</p>
      </div>

      <Card className="p-6 space-y-4">
        <div className="divide-y divide-slate-800/60">
          {orgs.map((o) => (
            <div key={o.id} className="py-3 flex items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-950/50 border border-indigo-500/30 flex items-center justify-center font-bold text-indigo-400">
                  <Building className="w-4 h-4" />
                </div>
                <div>
                  <p className="font-semibold text-slate-200">{o.name}</p>
                  <p className="text-[11px] text-slate-400 font-mono">slug: {o.slug}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant={o.subscription_status === "active" ? "success" : "default"}>
                  Sub: {o.subscription_status}
                </Badge>
                {o.publishing_paused && <Badge variant="danger">Publishing Paused</Badge>}
                <span className="text-slate-500 text-[11px] hidden sm:inline">
                  Created {formatDate(o.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
