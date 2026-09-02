"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { Member, Role } from "@pravah/shared-types";
import { formatDate } from "@/lib/utils";
import {
  Users,
  UserPlus,
  Shield,
  Trash2,
  Mail,
  ShieldCheck,
} from "lucide-react";

export default function TeamPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [members, setMembers] = useState<Member[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Invite Modal
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [isInviting, setIsInviting] = useState(false);

  // Remove Dialog
  const [removeMemberId, setRemoveMemberId] = useState<string | null>(null);

  const fetchData = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const [membersRes, rolesRes] = await Promise.all([
        fetchApi<Member[]>("/organisations/members"),
        fetchApi<Role[]>("/organisations/roles"),
      ]);
      setMembers(membersRes);
      setRoles(rolesRes);
      if (rolesRes.length > 0 && !selectedRoleId) {
        setSelectedRoleId(rolesRes[0].id);
      }
    } catch {
      setMembers([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeOrg]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim() || !selectedRoleId) return;

    setIsInviting(true);
    try {
      await fetchApi("/organisations/members/invite", {
        method: "POST",
        body: JSON.stringify({
          email: inviteEmail,
          role_id: selectedRoleId,
        }),
      });

      toast.success("Invitation Dispatched!", `Sent an invitation token to ${inviteEmail}.`);
      setIsInviteOpen(false);
      setInviteEmail("");
      fetchData();
    } catch (err: any) {
      toast.error("Invite Failed", err.message || "Failed to dispatch invitation.");
    } finally {
      setIsInviting(false);
    }
  };

  const handleRemoveMember = async () => {
    if (!removeMemberId) return;
    try {
      await fetchApi(`/organisations/members/${removeMemberId}`, { method: "DELETE" });
      toast.success("Member Removed", "Workspace access revoked.");
      setRemoveMemberId(null);
      fetchData();
    } catch (err: any) {
      toast.error("Removal Failed", err.message || "Could not remove member.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <Users className="w-6 h-6 text-indigo-400" /> Team Members & RBAC Roles
          </h1>
          <p className="text-xs text-slate-400">
            Manage brand collaborators, approval privileges, and custom role permissions.
          </p>
        </div>

        <Button variant="glow" leftIcon={<UserPlus className="w-4 h-4" />} onClick={() => setIsInviteOpen(true)}>
          Invite Team Member
        </Button>
      </div>

      {/* Members Table */}
      <Card className="p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-sm font-semibold text-slate-200">Active Collaborators ({members.length})</h3>
        </div>

        <div className="divide-y divide-slate-800/60">
          {members.map((m) => {
            const memberEmail = m.email || m.user_email || "";
            const memberName = m.first_name
              ? `${m.first_name} ${m.last_name || ""}`.trim()
              : m.user_name || (memberEmail ? memberEmail.split("@")[0] : "Collaborator");
            const initial = (memberEmail[0] || memberName[0] || "U").toUpperCase();
            const roleName = m.role_name || m.roleName || "member";

            return (
              <div key={m.id} className="py-3 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center font-bold text-indigo-400 text-xs border border-slate-700">
                    {initial}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-100">{memberName}</p>
                    <p className="text-[11px] text-slate-400">{memberEmail || "No email"}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <Badge variant={roleName === "org_owner" ? "purple" : "info"}>
                    {roleName}
                  </Badge>
                  <span className="text-[11px] text-slate-500 hidden sm:inline">
                    Joined {formatDate(m.created_at || m.createdAt)}
                  </span>
                  {roleName !== "org_owner" && (
                    <button
                      onClick={() => setRemoveMemberId(m.id)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Invite Member Modal */}
      <Modal
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        title="Invite New Collaborator"
        description="Assign a role to grant appropriate permissions in this workspace."
      >
        <form onSubmit={handleInvite} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="colleague@company.com"
            leftIcon={<Mail className="w-4 h-4" />}
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">Assign Role</label>
            <select
              className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none"
              value={selectedRoleId}
              onChange={(e) => setSelectedRoleId(e.target.value)}
              required
            >
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.display_name} ({r.name})
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsInviteOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="glow" size="sm" isLoading={isInviting}>
              Send Invitation
            </Button>
          </div>
        </form>
      </Modal>

      {/* Remove Member Dialog */}
      <ConfirmationDialog
        isOpen={!!removeMemberId}
        onClose={() => setRemoveMemberId(null)}
        onConfirm={handleRemoveMember}
        title="Revoke Workspace Access?"
        message="This user will immediately lose access to this brand workspace and all associated content."
        confirmLabel="Revoke Access"
      />
    </div>
  );
}
