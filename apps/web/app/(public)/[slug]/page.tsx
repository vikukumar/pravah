"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, FileText, Calendar } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface CMSBlock {
  id: string;
  block_type: string;
  name: string;
  content: {
    heading?: string;
    text?: string;
    items?: string[];
  };
  display_order: number;
}

interface CMSPageData {
  id: string;
  title: string;
  slug: string;
  description: string;
  version: number;
  published_at: string;
  updated_at: string;
  blocks: CMSBlock[];
  seo?: {
    meta_title?: string;
    meta_description?: string;
  };
}

export default function DynamicCMSPage() {
  const params = useParams();
  const slug = Array.isArray(params.slug) ? params.slug.join("/") : params.slug;

  const [page, setPage] = useState<CMSPageData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    setIsLoading(true);
    fetchApi<CMSPageData>(`/cms/pages/${slug}`)
      .then((data) => {
        setPage(data);
        if (data.seo?.meta_title) {
          document.title = `${data.seo.meta_title} | PRAVAH`;
        }
      })
      .catch((err) => {
        setError(err.message || "Page not found");
      })
      .finally(() => setIsLoading(false));
  }, [slug]);

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !page) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-4">
        <h1 className="text-2xl font-bold text-slate-100">Page Not Found</h1>
        <p className="text-xs text-slate-400">The requested legal document or CMS page could not be located.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8">
      <div className="space-y-3 border-b border-slate-800 pb-6">
        <Badge variant="purple">Legal & Compliance Document</Badge>
        <h1 className="text-3xl font-bold text-slate-100">{page.title}</h1>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-indigo-400" /> Version {page.version}.0
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-indigo-400" /> Updated {formatDate(page.updated_at)}
          </span>
        </div>
      </div>

      <div className="space-y-6">
        {page.blocks?.map((block) => (
          <Card key={block.id} className="space-y-3">
            {block.content?.heading && (
              <h2 className="text-base font-semibold text-indigo-300">
                {block.content.heading}
              </h2>
            )}
            {block.content?.text && (
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {block.content.text}
              </p>
            )}
            {block.content?.items && (
              <ul className="space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                {block.content.items.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
