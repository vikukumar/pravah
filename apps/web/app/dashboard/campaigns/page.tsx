"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { Layers, Plus, Calendar, Target, Sparkles } from "lucide-react";

export default function CampaignsPage() {
  const toast = useToast();
  const [campaigns, setCampaigns] = useState<any[]>([
    {
      id: "camp-1",
      name: "Q3 AI Automation Launch",
      objective: "Product Conversions",
      status: "active",
      postCount: 12,
      reach: "48.2K",
      startDate: "2026-09-01",
    },
    {
      id: "camp-2",
      name: "Weekly Founder Insights",
      objective: "Thought Leadership",
      status: "active",
      postCount: 8,
      reach: "32.1K",
      startDate: "2026-08-15",
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [objective, setObjective] = useState("Product Launch");

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const newCamp = {
      id: `camp-${Date.now()}`,
      name,
      objective,
      status: "active",
      postCount: 0,
      reach: "0",
      startDate: new Date().toISOString().split("T")[0],
    };

    setCampaigns([newCamp, ...campaigns]);
    toast.success("Campaign Created!", "You can now associate posts and workflows with this campaign.");
    setIsModalOpen(false);
    setName("");
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {campaigns.map((c) => (
          <Card key={c.id} hoverEffect className="space-y-4 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Badge variant="purple">{c.objective}</Badge>
                <Badge variant="success">{c.status}</Badge>
              </div>

              <h3 className="text-base font-bold text-slate-100">{c.name}</h3>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase">Posts</span>
                  <p className="font-bold text-slate-200">{c.postCount} scheduled</p>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase">Estimated Reach</span>
                  <p className="font-bold text-indigo-300">{c.reach}</p>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Started {c.startDate}</span>
              <Button variant="ghost" size="sm">View Posts →</Button>
            </div>
          </Card>
        ))}
      </div>

      {/* New Campaign Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Strategic Campaign"
        description="Set up a target objective to group posts and measure aggregated reach."
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Campaign Name"
            placeholder="e.g. Q4 Black Friday Launch"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">Campaign Objective</label>
            <select
              className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
            >
              <option value="Product Launch">Product Launch</option>
              <option value="Brand Awareness">Brand Awareness</option>
              <option value="Thought Leadership">Thought Leadership</option>
              <option value="Lead Generation">Lead Generation</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="glow" size="sm">
              Create Campaign
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
