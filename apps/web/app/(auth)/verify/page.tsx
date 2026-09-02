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
import { Mail, KeyRound, ArrowRight } from "lucide-react";

export default function VerifyEmailPage() {
  const router = useRouter();
  const toast = useToast();

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await fetchApi("/auth/verify-otp", {
        method: "POST",
        body: JSON.stringify({ email, code, otp_type: "verify_email" }),
      });
      toast.success("Email Verified!", "Your email has been verified. You can now access all features.");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error("Verification Failed", err.message || "Invalid OTP code.");
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
          <h1 className="text-2xl font-bold text-slate-100">Verify Email Address</h1>
          <p className="text-xs text-slate-400">Enter the 6-digit OTP code dispatched to your email.</p>
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
              label="Verification Code (OTP)"
              placeholder="123456"
              leftIcon={<KeyRound className="w-4 h-4" />}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
            <Button type="submit" variant="primary" className="w-full" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>
              Verify Email
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
