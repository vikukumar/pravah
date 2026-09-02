"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { Sliders, Save } from "lucide-react";

export default function AdminSettingsPage() {
  const toast = useToast();
  const [settings, setSettings] = useState<any>({});
  const [appName, setAppName] = useState("PRAVAH");
  const [appUrl, setAppUrl] = useState("https://pravah.app");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchApi<any>("/admin/settings")
      .then((data) => {
        setSettings(data);
        if (data.platform_config) {
          setAppName(data.platform_config.app_name || "PRAVAH");
          setAppUrl(data.platform_config.app_url || "https://pravah.app");
        }
      })
      .catch(() => {});
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await fetchApi("/admin/settings", {
        method: "POST",
        body: JSON.stringify({
          key: "platform_config",
          value: { app_name: appName, app_url: appUrl },
          is_public: true,
        }),
      });
      toast.success("Settings Saved", "Global platform configurations updated.");
    } catch (err: any) {
      toast.error("Save Failed", err.message || "Failed to update platform settings.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-100">Global Platform Configuration</h1>
        <p className="text-xs text-slate-400">Configure global application branding, URLs, and feature thresholds.</p>
      </div>

      <Card className="p-6 space-y-6">
        <form onSubmit={handleSave} className="space-y-4">
          <Input
            label="Application Name"
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
            required
          />

          <Input
            label="Platform Base URL"
            value={appUrl}
            onChange={(e) => setAppUrl(e.target.value)}
            required
          />

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <Button type="submit" variant="glow" size="sm" isLoading={isSaving} leftIcon={<Save className="w-4 h-4" />}>
              Save Platform Configuration
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
