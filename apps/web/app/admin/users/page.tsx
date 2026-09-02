"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { formatDate } from "@/lib/utils";
import { Users, Shield, CheckCircle2, XCircle } from "lucide-react";

export default function AdminUsersPage() {
  const toast = useToast();
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await fetchApi<any[]>("/admin/users");
      setUsers(data);
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleUserActive = async (userId: string) => {
    try {
      const res = await fetchApi<any>(`/admin/users/${userId}/toggle-active`, { method: "PATCH" });
      toast.success("User Updated", res.message);
      fetchUsers();
    } catch (err: any) {
      toast.error("Update Failed", err.message || "Failed to toggle user status.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100">All Platform Users</h1>
        <p className="text-xs text-slate-400">View registered platform users, super administrators, and active states.</p>
      </div>

      <Card className="p-6 space-y-4">
        <div className="divide-y divide-slate-800/60">
          {users.map((u) => (
            <div key={u.id} className="py-3 flex items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-indigo-400">
                  {(u.email ? u.email[0] : u.first_name ? u.first_name[0] : "U").toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold text-slate-200">
                    {u.first_name} {u.last_name || ""}
                  </p>
                  <p className="text-[11px] text-slate-400">{u.email}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {u.is_super_admin && <Badge variant="purple">Super Admin</Badge>}
                <Badge variant={u.is_active ? "success" : "danger"}>
                  {u.is_active ? "Active" : "Suspended"}
                </Badge>
                <span className="text-slate-500 text-[11px] hidden sm:inline">
                  {formatDate(u.created_at)}
                </span>
                {!u.is_super_admin && (
                  <Button variant="outline" size="sm" onClick={() => handleToggleUserActive(u.id)}>
                    {u.is_active ? "Suspend" : "Activate"}
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
