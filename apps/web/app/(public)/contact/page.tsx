"use client";

import React, { useState } from "react";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { Mail, Send, User, Building, MessageSquare } from "lucide-react";

export default function ContactPage() {
  const toast = useToast();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    company: "",
    message: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await fetchApi("/cms/forms/submit", {
        method: "POST",
        body: JSON.stringify({
          form_name: "contact_us",
          data: formData,
        }),
      });

      setIsSent(true);
      toast.success("Message Dispatched", "Our solutions architecture team will get back to you shortly.");
    } catch (err: any) {
      toast.error("Submission Failed", err.message || "Could not submit inquiry.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-10">
      <div className="text-center space-y-3">
        <Badge variant="info">Get In Touch</Badge>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-100">Talk to Our Platform Architects</h1>
        <p className="text-xs text-slate-400 max-w-lg mx-auto">
          Need high-volume AI tokens, custom SSO deployment, or enterprise workflow pipelines? We’re here to help.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="space-y-4 md:col-span-1">
          <Card className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-100">Direct Support</h4>
            <p className="text-xs text-slate-400">enterprise@pravah.app</p>
          </Card>
          <Card className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-100">Global Headquarters</h4>
            <p className="text-xs text-slate-400">PRAVAH Technologies Inc.<br />Bangalore & San Francisco</p>
          </Card>
          <Card className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-100">SLA Guarantee</h4>
            <p className="text-xs text-slate-400">99.95% High Availability with 24/7 dedicated support.</p>
          </Card>
        </div>

        <Card className="md:col-span-2 space-y-4">
          {!isSent ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Full Name"
                  placeholder="Vikram Sharma"
                  leftIcon={<User className="w-4 h-4" />}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
                <Input
                  label="Work Email"
                  type="email"
                  placeholder="vikram@agency.com"
                  leftIcon={<Mail className="w-4 h-4" />}
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>

              <Input
                label="Company / Agency Name"
                placeholder="Acme Media Group"
                leftIcon={<Building className="w-4 h-4" />}
                value={formData.company}
                onChange={(e) => setFormData({ ...formData, company: e.target.value })}
              />

              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  How can we help your team? <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={4}
                  className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-2 focus:ring-indigo-500/20"
                  placeholder="Tell us about your social publishing volume, desired workflows, or team size..."
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  required
                />
              </div>

              <Button type="submit" variant="glow" className="w-full" isLoading={isLoading} rightIcon={<Send className="w-4 h-4" />}>
                Submit Inquiry
              </Button>
            </form>
          ) : (
            <div className="text-center py-10 space-y-4">
              <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Inquiry Received</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Thank you for reaching out! A senior platform architect will review your requirements and respond within 24 hours.
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
