"use client";

import React, { Suspense, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { Lock, KeyRound, ArrowRight } from "lucide-react";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();

  const tokenParam = searchParams.get("token") || "";
  const [token, setToken] = useState(tokenParam);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setIsLoading(true);
    try {
      await fetchApi("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          token,
          password,
          confirm_password: confirmPassword,
        }),
      });

      toast.success("Password Updated!", "Please log in with your new password.");
      router.push("/login");
    } catch (err: any) {
      toast.error("Reset Failed", err.message || "Invalid or expired token.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Reset Token"
          placeholder="Paste token from reset email"
          leftIcon={<KeyRound className="w-4 h-4" />}
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
        />
        <Input
          label="New Password"
          type="password"
          placeholder="••••••••"
          leftIcon={<Lock className="w-4 h-4" />}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Input
          label="Confirm New Password"
          type="password"
          placeholder="••••••••"
          leftIcon={<Lock className="w-4 h-4" />}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
        <Button type="submit" variant="primary" className="w-full" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>
          Save New Password
        </Button>
      </form>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col justify-center items-center p-4 relative">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block relative w-44 h-11 mb-1">
            <Image src="/images/pravah_horizontal_logo.png" alt="PRAVAH" fill className="object-contain" priority />
          </Link>
          <h1 className="text-2xl font-bold text-slate-100">Set New Password</h1>
          <p className="text-xs text-slate-400">Choose a secure password for your account.</p>
        </div>

        <Suspense fallback={<div className="text-center py-6 text-xs text-slate-400">Loading form...</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}

