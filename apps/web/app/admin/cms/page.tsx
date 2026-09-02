"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { useToast } from "@/components/ui/toast";
import { formatDate } from "@/lib/utils";
import { FileText, Plus, Edit, ExternalLink, ShieldCheck, Check } from "lucide-react";

export default function AdminCMSPage() {
  const toast = useToast();
  const [pages, setPages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Edit / Create Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedPage, setSelectedPage] = useState<any>(null);
  const [pageTitle, setPageTitle] = useState("");
  const [pageSlug, setPageSlug] = useState("");
  const [pageDesc, setPageDesc] = useState("");
  const [isPublished, setIsPublished] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const fetchPages = async () => {
    setIsLoading(true);
    try {
      const data = await fetchApi<any[]>("/admin/cms/pages");
      setPages(data);
    } catch {
      //
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPages();
  }, []);

  const handleOpenEdit = (page?: any) => {
    if (page) {
      setSelectedPage(page);
      setPageTitle(page.title);
      setPageSlug(page.slug);
      setPageDesc(page.description || "");
      setIsPublished(page.is_published);
    } else {
      setSelectedPage(null);
      setPageTitle("");
      setPageSlug("");
      setPageDesc("");
      setIsPublished(true);
    }
    setIsEditModalOpen(true);
  };

  const handleSavePage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pageTitle.trim() || !pageSlug.trim()) return;

    setIsSaving(true);
    try {
      await fetchApi("/admin/cms/pages", {
        method: "POST",
        body: JSON.stringify({
          title: pageTitle,
          slug: pageSlug,
          description: pageDesc,
          is_published: isPublished,
        }),
      });

      toast.success("Page Saved!", `CMS page '${pageTitle}' has been updated.`);
      setIsEditModalOpen(false);
      fetchPages();
    } catch (err: any) {
      toast.error("Save Failed", err.message || "Could not save CMS page.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-400" /> CMS & Legal Compliance Pages
          </h1>
          <p className="text-xs text-slate-400">
            Manage dynamic database-driven pages, legal compliance policies, and terms of service.
          </p>
        </div>

        <Button variant="glow" size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => handleOpenEdit()}>
          Create New Page
        </Button>
      </div>

      <Card className="p-6 space-y-4">
        <div className="divide-y divide-slate-800/60">
          {pages.map((p) => (
            <div key={p.id} className="py-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <span className="font-bold text-slate-100 text-sm">{p.title}</span>
                  <span className="font-mono text-[11px] text-indigo-400">/{p.slug}</span>
                  {p.is_system && <Badge variant="purple" className="text-[10px]">System Policy</Badge>}
                  <Badge variant={p.is_published ? "success" : "default"}>
                    {p.is_published ? "Published" : "Draft"}
                  </Badge>
                </div>
                <p className="text-slate-400 text-[11px]">
                  Blocks: {p.blocks_count} • Version: v{p.version} • Updated: {formatDate(p.updated_at || p.created_at)}
                </p>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <Link
                  href={`/${p.slug}`}
                  target="_blank"
                  className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white flex items-center gap-1.5 text-xs transition-colors"
                >
                  View Live <ExternalLink className="w-3.5 h-3.5" />
                </Link>
                <Button variant="outline" size="sm" leftIcon={<Edit className="w-3.5 h-3.5" />} onClick={() => handleOpenEdit(p)}>
                  Edit
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Edit Page Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title={selectedPage ? `Edit ${selectedPage.title}` : "Create New CMS Page"}
        description="Configure dynamic page slug, metadata, and visibility."
      >
        <form onSubmit={handleSavePage} className="space-y-4">
          <Input
            label="Page Title"
            placeholder="e.g. Terms of Service"
            value={pageTitle}
            onChange={(e) => setPageTitle(e.target.value)}
            required
          />

          <Input
            label="URL Slug"
            placeholder="e.g. terms"
            value={pageSlug}
            onChange={(e) => setPageSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-_]/g, "-"))}
            required
            disabled={selectedPage?.is_system}
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">Page Description</label>
            <textarea
              rows={3}
              placeholder="Brief description for SEO and listing..."
              value={pageDesc}
              onChange={(e) => setPageDesc(e.target.value)}
              className="w-full bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="is_published"
              checked={isPublished}
              onChange={(e) => setIsPublished(e.target.checked)}
              className="rounded bg-slate-900 border-slate-800 text-indigo-600 focus:ring-0"
            />
            <label htmlFor="is_published" className="text-xs text-slate-300 cursor-pointer">
              Publish page and make publicly accessible
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="glow" size="sm" isLoading={isSaving}>
              Save Page
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
