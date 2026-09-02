"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { Layers, Plus, Calendar, Loader2, Trash2 } from "lucide-react";

interface Campaign {
  id: string;
  name: string;
  description?: string;
  objective: string;
  status: string;
  post_count: number;
  start_date?: string;
  end_date?: string;
  created_at?: string;
}

export default function CampaignsPage() {
  const toast = useToast();
  const { activeOrg } = useOrganisation();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [objective, setObjective] = useState("Brand Awareness");

  const fetchCampaigns = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const data = await fetchApi<Campaign[]>("/campaigns");
      setCampaigns(data);
    } catch {
      toast.error("Load Failed", "Could not load campaigns from server.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, [activeOrg]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSaving(true);
    try {
      await fetchApi("/campaigns", {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), description, objective }),
      });
      toast.success("Campaign Created!", "Your campaign has been saved.");
      setIsModalOpen(false);
      setName("");
      setDescription("");
      fetchCampaigns();
    } catch (err: any) {
      toast.error("Create Failed", err.message || "Could not create campaign.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string, campaignName: string) => {
    try {
      await fetchApi(`/campaigns/${id}`, { method: "DELETE" });
      toast.success("Deleted", `Campaign "${campaignName}" has been removed.`);
      setCampaigns((prev) => prev.filter((c) => c.id !== id));
    } catch (err: any) {
      toast.error("Delete Failed", err.message || "Could not delete campaign.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-indigo-400" /> Multi-Post Campaigns
          </h1>
          <p className="text-xs text-slate-400">
            Group scheduled posts and visual workflows under coordinated strategic campaigns.
          </p>
        </div>
        <Button variant="glow" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsModalOpen(true)}>
          New Campaign
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
        </div>
      ) : campaigns.length === 0 ? (
        <Card className="py-16 flex flex-col items-center text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center">
            <Layers className="w-7 h-7 text-slate-500" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-slate-200">No Campaigns Yet</h3>
            <p className="text-xs text-slate-400 max-w-sm">
              Create your first campaign to group posts and measure coordinated reach.
            </p>
          </div>
          <Button variant="glow" size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsModalOpen(true)}>
            Create Campaign
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {campaigns.map((c) => (
            <Card key={c.id} hoverEffect className="space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="purple">{c.objective}</Badge>
                  <Badge variant={c.status === "active" ? "success" : "default"}>{c.status}</Badge>
                </div>
                <h3 className="text-base font-bold text-slate-100">{c.name}</h3>
                {c.description && (
                  <p className="text-xs text-slate-400 line-clamp-2">{c.description}</p>
                )}
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase">Posts</span>
                    <p className="font-bold text-slate-200">{c.post_count} scheduled</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase">Started</span>
                    <p className="font-bold text-slate-200">
                      {c.start_date ? new Date(c.start_date).toLocaleDateString() : "—"}
                    </p>
                  </div>
                </div>
              </div>
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-2">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}
                </span>
                <button
                  onClick={() => handleDelete(c.id, c.name)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
                  title="Delete campaign"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Strategic Campaign"
        description="Set up a target objective to group posts and measure aggregated reach."
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Campaign Name"
            placeholder="e.g. Q4 Product Launch"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="Description (optional)"
            placeholder="Brief campaign goal or strategy"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300">Objective</label>
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option>Brand Awareness</option>
              <option>Product Conversions</option>
              <option>Thought Leadership</option>
              <option>Community Engagement</option>
              <option>Lead Generation</option>
              <option>Customer Retention</option>
            </select>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <Button type="submit" variant="glow" isLoading={isSaving} className="flex-1">
              {isSaving ? "Creating..." : "Create Campaign"}
            </Button>
            <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
