"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { SocialIcon } from "@/components/ui/social-icon";
import { useToast } from "@/components/ui/toast";
import { useOrganisation } from "@/providers/org-provider";
import { formatDate } from "@/lib/utils";
import {
  FileText,
  Plus,
  Send,
  Calendar,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  Share2,
  Eye,
  AlertTriangle,
  Edit,
  Sparkles,
} from "lucide-react";

export default function ContentPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();

  const [posts, setPosts] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);

  // Composer Modal State
  const [isComposerOpen, setIsComposerOpen] = useState(false);
  const [composerTitle, setComposerTitle] = useState("");
  const [composerBody, setComposerBody] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["x"]);
  const [scheduledAt, setScheduledAt] = useState("");
  const [requireApproval, setRequireApproval] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Review / Approval Action Modal State
  const [approvalModalPost, setApprovalModalPost] = useState<any>(null);
  const [reviewAction, setReviewAction] = useState<"approve" | "reject">("approve");
  const [reviewComments, setReviewComments] = useState("");
  const [isReviewing, setIsReviewing] = useState(false);

  // Delete Dialog State
  const [deletePostId, setDeletePostId] = useState<string | null>(null);

  const fetchPosts = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const endpoint = statusFilter === "all" ? "/content" : `/content?status=${statusFilter}`;
      const data = await fetchApi<any[]>(endpoint);
      setPosts(data);
    } catch {
      setPosts([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [activeOrg, statusFilter]);

  const togglePlatform = (p: string) => {
    if (selectedPlatforms.includes(p)) {
      if (selectedPlatforms.length > 1) {
        setSelectedPlatforms(selectedPlatforms.filter((item) => item !== p));
      }
    } else {
      setSelectedPlatforms([...selectedPlatforms, p]);
    }
  };

  const handleCreatePost = async (publishImmediately: boolean = false) => {
    if (!composerBody.trim()) {
      toast.error("Please enter post text.");
      return;
    }

    setIsSaving(true);
    try {
      const payload: any = {
        title: composerTitle || undefined,
        body: composerBody,
        content_type: "text",
        platforms: selectedPlatforms,
        approval_required: requireApproval,
      };

      if (scheduledAt) {
        payload.scheduled_at = new Date(scheduledAt).toISOString();
      }

      const created = await fetchApi<any>("/content", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (publishImmediately) {
        await fetchApi(`/content/${created.id}/publish-now`, { method: "POST" });
        toast.success("Post Published!", `Dispatched to ${selectedPlatforms.join(", ").toUpperCase()}`);
      } else {
        toast.success("Post Created", `Saved with status: ${created.status}`);
      }

      setIsComposerOpen(false);
      setComposerTitle("");
      setComposerBody("");
      setScheduledAt("");
      fetchPosts();
    } catch (err: any) {
      toast.error("Failed to Create Post", err.message || "Something went wrong.");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePublishNow = async (postId: string) => {
    try {
      await fetchApi(`/content/${postId}/publish-now`, { method: "POST" });
      toast.success("Published!", "Post successfully dispatched to social platforms.");
      fetchPosts();
    } catch (err: any) {
      toast.error("Publishing Failed", err.message || "Failed to publish post.");
    }
  };

  const handleReviewSubmit = async () => {
    if (!approvalModalPost) return;
    setIsReviewing(true);
    try {
      await fetchApi(`/content/${approvalModalPost.id}/approve`, {
        method: "POST",
        body: JSON.stringify({
          action: reviewAction,
          comments: reviewComments,
        }),
      });

      toast.success(
        reviewAction === "approve" ? "Post Approved!" : "Post Rejected",
        "Workflow status updated."
      );
      setApprovalModalPost(null);
      setReviewComments("");
      fetchPosts();
    } catch (err: any) {
      toast.error("Review Failed", err.message || "Could not complete review action.");
    } finally {
      setIsReviewing(false);
    }
  };

  const handleDeletePost = async () => {
    if (!deletePostId) return;
    try {
      await fetchApi(`/content/${deletePostId}`, { method: "DELETE" });
      toast.success("Post Deleted", "The item was removed from the queue.");
      setDeletePostId(null);
      fetchPosts();
    } catch (err: any) {
      toast.error("Delete Failed", err.message || "Could not delete post.");
    }
  };

  const statuses = ["all", "draft", "review", "approved", "scheduled", "published", "failed"];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-indigo-400" /> Content & Multi-Channel Composer
          </h1>
          <p className="text-xs text-slate-400">
            Create, schedule, review, and dispatch multi-platform social posts.
          </p>
        </div>

        <Button variant="glow" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setIsComposerOpen(true)}>
          New Social Post
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {statuses.map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize transition-colors ${
              statusFilter === st
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Posts List */}
      <Card className="p-6 space-y-4">
        {isLoading ? (
          <div className="text-center py-16">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-16 space-y-3">
            <FileText className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-300">No posts in this view</h3>
            <p className="text-xs text-slate-500">Create a new post or generate copy in the AI Studio.</p>
            <Button variant="outline" size="sm" onClick={() => setIsComposerOpen(true)}>
              Create Post
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {posts.map((post) => (
              <div
                key={post.id}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="space-y-2 max-w-2xl">
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        post.status === "published"
                          ? "success"
                          : post.status === "approved"
                          ? "purple"
                          : post.status === "review"
                          ? "warning"
                          : post.status === "failed"
                          ? "danger"
                          : "default"
                      }
                    >
                      {post.status}
                    </Badge>
                    <span className="text-xs text-slate-400">
                      {formatDate(post.created_at)}
                    </span>
                    {post.scheduled_at && (
                      <span className="text-[11px] bg-indigo-950/40 text-indigo-300 border border-indigo-500/20 px-2 py-0.5 rounded flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {formatDate(post.scheduled_at)}
                      </span>
                    )}
                  </div>

                  {post.title && <h4 className="text-xs font-bold text-slate-100">{post.title}</h4>}

                  <p className="text-xs text-slate-300 line-clamp-3 whitespace-pre-wrap leading-relaxed">
                    {post.body}
                  </p>

                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 pt-1">
                    <span>Platforms:</span>
                    {post.platforms.map((p: string) => (
                      <span key={p} className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 text-slate-200 px-2 py-0.5 rounded-lg text-[11px] font-medium">
                        <SocialIcon platform={p} className="w-3.5 h-3.5" />
                        <span className="capitalize">{p}</span>
                      </span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                  {post.status === "review" && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-amber-400 border-amber-500/30"
                      onClick={() => setApprovalModalPost(post)}
                    >
                      Review Post
                    </Button>
                  )}

                  {post.status !== "published" && (
                    <Button
                      variant="glow"
                      size="sm"
                      onClick={() => handlePublishNow(post.id)}
                      rightIcon={<Send className="w-3 h-3" />}
                    >
                      Publish Now
                    </Button>
                  )}

                  <button
                    onClick={() => setDeletePostId(post.id)}
                    className="p-2 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* New Post Composer Modal */}
      <Modal
        isOpen={isComposerOpen}
        onClose={() => setIsComposerOpen(false)}
        title="Compose Social Post"
        description="Write or craft content for multi-platform distribution."
        maxWidth="2xl"
      >
        <div className="space-y-4">
          <Input
            label="Post Title / Campaign Reference (Optional)"
            placeholder="e.g. Weekly Product Launch Update"
            value={composerTitle}
            onChange={(e) => setComposerTitle(e.target.value)}
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">
              Post Content Body <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={5}
              className="w-full bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-2 focus:ring-indigo-500/20"
              placeholder="What would you like to share with your audience?"
              value={composerBody}
              onChange={(e) => setComposerBody(e.target.value)}
              required
            />
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span>{composerBody.length} characters</span>
              {selectedPlatforms.includes("x") && (
                <span className={composerBody.length > 280 ? "text-rose-400 font-semibold" : ""}>
                  X limit: 280 chars
                </span>
              )}
            </div>
          </div>

          {/* Platform targets */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">Target Platforms</label>
            <div className="flex flex-wrap gap-2">
              {[
                { id: "x", name: "X (Twitter)" },
                { id: "linkedin", name: "LinkedIn" },
                { id: "facebook", name: "Facebook" },
                { id: "instagram", name: "Instagram" },
                { id: "youtube", name: "YouTube" },
              ].map((plat) => {
                const isSelected = selectedPlatforms.includes(plat.id);
                return (
                  <button
                    key={plat.id}
                    type="button"
                    onClick={() => togglePlatform(plat.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium border flex items-center gap-2 transition-all ${
                      isSelected
                        ? "bg-indigo-600/20 text-indigo-200 border-indigo-500/60 shadow-md shadow-indigo-600/10"
                        : "bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <SocialIcon platform={plat.id} className="w-4 h-4" />
                    <span>{plat.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Scheduling and Approvals */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <Input
              label="Schedule For (Optional)"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
            />

            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="requireApproval"
                checked={requireApproval}
                onChange={(e) => setRequireApproval(e.target.checked)}
                className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="requireApproval" className="text-xs text-slate-300 cursor-pointer">
                Submit for Team Approval first
              </label>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsComposerOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleCreatePost(false)}
              isLoading={isSaving}
            >
              Save as Draft
            </Button>
            <Button
              variant="glow"
              size="sm"
              onClick={() => handleCreatePost(true)}
              isLoading={isSaving}
              rightIcon={<Send className="w-3.5 h-3.5" />}
            >
              Publish Now
            </Button>
          </div>
        </div>
      </Modal>

      {/* Review Approval Modal */}
      <Modal
        isOpen={!!approvalModalPost}
        onClose={() => setApprovalModalPost(null)}
        title="Review & Approve Content"
        description="Verify post copy before it is scheduled for live distribution."
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 whitespace-pre-wrap">
            {approvalModalPost?.body}
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-300">Decision</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setReviewAction("approve")}
                className={`p-2.5 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-colors ${
                  reviewAction === "approve"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : "bg-slate-900 text-slate-400 border-slate-800"
                }`}
              >
                <CheckCircle2 className="w-4 h-4" /> Approve Post
              </button>
              <button
                type="button"
                onClick={() => setReviewAction("reject")}
                className={`p-2.5 rounded-xl text-xs font-semibold border flex items-center justify-center gap-1.5 transition-colors ${
                  reviewAction === "reject"
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                    : "bg-slate-900 text-slate-400 border-slate-800"
                }`}
              >
                <XCircle className="w-4 h-4" /> Reject Post
              </button>
            </div>
          </div>

          <Input
            label="Reviewer Comments (Optional)"
            placeholder="e.g. Tone is perfect, approved for schedule."
            value={reviewComments}
            onChange={(e) => setReviewComments(e.target.value)}
          />

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setApprovalModalPost(null)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleReviewSubmit} isLoading={isReviewing}>
              Submit Review Decision
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={!!deletePostId}
        onClose={() => setDeletePostId(null)}
        onConfirm={handleDeletePost}
        title="Delete Social Post?"
        message="This will permanently remove the post from your queue and cancel any scheduled publishing."
        confirmLabel="Delete Permanently"
      />
    </div>
  );
}
