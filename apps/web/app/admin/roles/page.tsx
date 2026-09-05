"use client";
import React, { useEffect, useState, useCallback } from "react";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { Shield, CheckCircle, XCircle, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";

interface Permission { id: string; name: string; module: string; description: string; }
interface Role { id: string; name: string; display_name: string; description: string; is_system: boolean; permissions: Permission[]; }
interface PermsByModule { by_module: Record<string, Permission[]>; total: number; }

const MODULE_COLORS: Record<string, string> = { ai: "#8b5cf6", workflow: "#6366f1", content: "#06b6d4", social: "#f59e0b", analytics: "#10b981", billing: "#ec4899", settings: "#64748b", audit: "#94a3b8", organisation: "#3b82f6", member: "#f97316", role: "#a855f7", campaign: "#14b8a6", media: "#84cc16" };

export default function RolesPage() {
  const toast = useToast();
  const [roles, setRoles] = useState<Role[]>([]);
  const [allPerms, setAllPerms] = useState<PermsByModule>({ by_module: {}, total: 0 });
  const [loading, setLoading] = useState(true);
  const [editRole, setEditRole] = useState<Role | null>(null);
  const [selectedPerms, setSelectedPerms] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [rolesData, permsData] = await Promise.all([
        fetchApi<Role[]>("/admin/roles"),
        fetchApi<PermsByModule>("/admin/permissions"),
      ]);
      setRoles(rolesData);
      setAllPerms(permsData);
      // Expand all modules by default
      setExpandedModules(new Set(Object.keys(permsData.by_module)));
    } catch { toast.error("Failed to load roles"); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const startEdit = (role: Role) => {
    setEditRole(role);
    setSelectedPerms(new Set(role.permissions.map((p) => p.name)));
  };

  const savePermissions = async () => {
    if (!editRole) return;
    setSaving(true);
    try {
      await fetchApi(`/admin/roles/${editRole.id}/permissions`, {
        method: "PUT",
        body: JSON.stringify({ permissions: Array.from(selectedPerms) }),
      });
      toast.success(`Permissions updated for ${editRole.display_name}`);
      setEditRole(null);
      load();
    } catch (e: any) { toast.error(e.message); } finally { setSaving(false); }
  };

  const toggleModule = (mod: string) => {
    setExpandedModules((prev) => { const n = new Set(prev); n.has(mod) ? n.delete(mod) : n.add(mod); return n; });
  };

  const toggleModuleAll = (mod: string, perms: Permission[]) => {
    const modPerms = perms.map((p) => p.name);
    const allSelected = modPerms.every((p) => selectedPerms.has(p));
    setSelectedPerms((prev) => {
      const n = new Set(prev);
      modPerms.forEach((p) => allSelected ? n.delete(p) : n.add(p));
      return n;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">Roles & Permissions</h1>
          <p className="text-slate-400 text-sm">{allPerms.total} permissions across {roles.length} system roles</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Role List */}
          <div className="space-y-3">
            {roles.map((role) => (
              <Card key={role.id} className={`cursor-pointer transition-all hover:border-slate-600 ${editRole?.id === role.id ? "border-purple-500/60 bg-purple-500/5" : ""}`} onClick={() => startEdit(role)}>
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-bold text-white">{role.display_name}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">{role.description}</p>
                    </div>
                    {role.is_system && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-slate-700 text-slate-400 border border-slate-600">System</span>}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {Object.keys(MODULE_COLORS).filter((mod) => role.permissions.some((p) => p.module === mod)).map((mod) => (
                      <span key={mod} className="text-[9px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: `${MODULE_COLORS[mod]}20`, color: MODULE_COLORS[mod], border: `1px solid ${MODULE_COLORS[mod]}30` }}>{mod}</span>
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-500 mt-2">{role.permissions.length} permissions</p>
                </div>
              </Card>
            ))}
          </div>

          {/* Permission Editor */}
          <div className="lg:col-span-2">
            {editRole ? (
              <Card className="overflow-hidden sticky top-4">
                <div className="flex items-center justify-between p-4 border-b border-slate-800">
                  <div>
                    <h3 className="text-sm font-bold text-white">Edit: {editRole.display_name}</h3>
                    <p className="text-[11px] text-slate-400">{selectedPerms.size} permissions selected</p>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={savePermissions} disabled={saving} className="bg-purple-600 hover:bg-purple-500 text-white text-xs" leftIcon={saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}>
                      {saving ? "Saving..." : "Save Changes"}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => setEditRole(null)} className="text-slate-400 text-xs"><XCircle className="w-4 h-4" /></Button>
                  </div>
                </div>

                <div className="overflow-y-auto max-h-[60vh] p-4 space-y-3">
                  {Object.entries(allPerms.by_module).map(([mod, perms]) => {
                    const isExpanded = expandedModules.has(mod);
                    const modSelected = perms.filter((p) => selectedPerms.has(p.name)).length;
                    const color = MODULE_COLORS[mod] || "#64748b";
                    return (
                      <div key={mod} className="rounded-xl border border-slate-800 overflow-hidden">
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={() => toggleModule(mod)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              toggleModule(mod);
                            }
                          }}
                          className="w-full flex items-center justify-between p-3 hover:bg-slate-800/40 transition-colors cursor-pointer select-none"
                        >
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full" style={{ background: color }} />
                            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{mod}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: `${color}20`, color }}>
                              {modSelected}/{perms.length}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={(e) => { e.stopPropagation(); toggleModuleAll(mod, perms); }} className="text-[10px] text-slate-500 hover:text-slate-300 px-2 py-0.5 rounded border border-slate-700 hover:border-slate-500">
                              {modSelected === perms.length ? "None" : "All"}
                            </button>
                            {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="border-t border-slate-800 bg-slate-900/30 divide-y divide-slate-800/50">
                            {perms.map((perm) => (
                              <label key={perm.name} className="flex items-center justify-between px-4 py-2 cursor-pointer hover:bg-slate-800/30">
                                <div>
                                  <p className="text-xs font-medium text-slate-300">{perm.name}</p>
                                  <p className="text-[10px] text-slate-500">{perm.description}</p>
                                </div>
                                <input type="checkbox" checked={selectedPerms.has(perm.name)} onChange={(e) => {
                                  const n = new Set(selectedPerms);
                                  e.target.checked ? n.add(perm.name) : n.delete(perm.name);
                                  setSelectedPerms(n);
                                }} className="w-4 h-4 rounded accent-purple-600 cursor-pointer" />
                              </label>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center py-20 text-slate-500">
                <div className="text-center">
                  <Shield className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Select a role on the left to edit its permissions</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
