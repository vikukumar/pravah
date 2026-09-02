"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/providers/auth-provider";
import { Lock, Mail, ShieldCheck, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const toast = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [requires2FA, setRequires2FA] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const payload: any = { email, password };
      if (twoFactorCode) {
        payload.two_factor_code = twoFactorCode;
      }

      const res = await fetchApi<any>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (res.requires_two_factor) {
        setRequires2FA(true);
        toast.info("Two-Factor Authentication", "Please enter the 6-digit code from your authenticator app.");
        setIsLoading(false);
        return;
      }

      login(res.access_token, res.refresh_token, res.user);
      toast.success("Welcome back!", "Successfully signed in.");

      if (res.user?.isSuperAdmin) {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      toast.error("Sign In Failed", err.message || "Invalid credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col justify-center items-center p-4 relative">
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-indigo-600/10 blur-[130px] pointer-events-none rounded-full" />

      <div className="max-w-md w-full relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block relative w-44 h-11 mb-1">
            <Image src="/images/pravah_horizontal_logo.png" alt="PRAVAH" fill className="object-contain" priority />
          </Link>
          <h1 className="text-2xl font-bold text-slate-100">Welcome Back</h1>
          <p className="text-xs text-slate-400">Sign in to manage your AI social media workflows</p>
        </div>

        <Card className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email Address"
              type="email"
              placeholder="you@company.com"
              leftIcon={<Mail className="w-4 h-4" />}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              leftIcon={<Lock className="w-4 h-4" />}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {requires2FA && (
              <div className="p-3 bg-indigo-950/30 border border-indigo-500/30 rounded-xl space-y-2 animate-in fade-in duration-200">
                <Input
                  label="2FA Authenticator Code"
                  placeholder="6-digit code or recovery code"
                  leftIcon={<ShieldCheck className="w-4 h-4 text-indigo-400" />}
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="flex items-center justify-between text-xs">
              <Link href="/forgot-password" className="text-indigo-400 hover:text-indigo-300">
                Forgot password?
              </Link>
            </div>

            <Button type="submit" variant="primary" className="w-full" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>
              {requires2FA ? "Verify & Sign In" : "Sign In"}
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-slate-400">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-medium">
            Start 30-Day Free Trial
          </Link>
        </p>
      </div>
    </div>
  );
}
