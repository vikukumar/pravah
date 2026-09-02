"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { Mail, ArrowRight, ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await fetchApi("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setIsSubmitted(true);
      toast.success("Request Dispatched", "If this email exists, password reset instructions have been sent.");
    } catch (err: any) {
      toast.error("Error", err.message || "Failed to process password reset.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col justify-center items-center p-4 relative">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block relative w-44 h-11 mb-1">
            <Image src="/images/pravah_horizontal_logo.png" alt="PRAVAH" fill className="object-contain" priority />
          </Link>
          <h1 className="text-2xl font-bold text-slate-100">Reset Password</h1>
          <p className="text-xs text-slate-400">Enter your email to receive recovery instructions.</p>
        </div>

        <Card className="space-y-4">
          {!isSubmitted ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Registered Email Address"
                type="email"
                placeholder="you@company.com"
                leftIcon={<Mail className="w-4 h-4" />}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Button type="submit" variant="primary" className="w-full" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>
                Send Reset Link
              </Button>
            </form>
          ) : (
            <div className="text-center space-y-3 py-3">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                <Mail className="w-6 h-6" />
              </div>
              <p className="text-xs text-slate-300">
                Check your inbox! We sent a password reset token to <span className="font-semibold text-slate-100">{email}</span>.
              </p>
            </div>
          )}

          <div className="pt-2 text-center">
            <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Login
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
