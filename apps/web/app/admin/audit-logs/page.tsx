"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { FileText } from "lucide-react";

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchApi<any[]>("/admin/audit-logs")
      .then((data) => setLogs(data))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100">System Audit Trail</h1>
        <p className="text-xs text-slate-400">Immutable chronological record of administrative and sensitive actions.</p>
      </div>

      <Card className="p-6 space-y-4">
        {logs.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-8">No audit records logged yet.</p>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {logs.map((log) => (
              <div key={log.id} className="py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-indigo-300">{log.action}</span>
                    <Badge variant={log.result === "success" ? "success" : "danger"}>
                      {log.result}
                    </Badge>
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Actor: <span className="text-slate-200">{log.actor_email || "System/API"}</span> • IP: {log.ip_address || "127.0.0.1"}
                  </p>
                </div>

                <span className="text-[11px] text-slate-500 font-mono">
                  {formatDate(log.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
