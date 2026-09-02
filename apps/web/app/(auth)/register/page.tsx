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
import { Lock, Mail, User, Phone, ArrowRight } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const toast = useToast();

  const [formData, setFormData] = useState({
    firstName: "",
    middleName: "",
    lastName: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (field: string, val: string) => {
    setFormData((prev) => ({ ...prev, [field]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      toast.error("Validation Error", "Passwords do not match.");
      return;
    }
    if (formData.password.length < 8) {
      toast.error("Validation Error", "Password must be at least 8 characters.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetchApi<any>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          first_name: formData.firstName,
          middle_name: formData.middleName || undefined,
          last_name: formData.lastName || undefined,
          email: formData.email,
          phone: formData.phone || undefined,
          password: formData.password,
          confirm_password: formData.confirmPassword,
        }),
      });

      login(res.tokens.access_token, res.tokens.refresh_token, res.tokens.user);
      localStorage.setItem("pravah_active_org_id", res.organisation_id);

      toast.success("Account Created!", "Welcome to PRAVAH. Your 30-day Free Trial is active.");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error("Registration Failed", err.message || "Could not register account.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col justify-center items-center p-4 relative">
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-indigo-600/10 blur-[130px] pointer-events-none rounded-full" />

      <div className="max-w-lg w-full relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-block relative w-44 h-11 mb-1">
            <Image src="/images/pravah_horizontal_logo.png" alt="PRAVAH" fill className="object-contain" priority />
          </Link>
          <h1 className="text-2xl font-bold text-slate-100">Create Your Free Account</h1>
          <p className="text-xs text-slate-400">Get started with AI-driven social media automation in minutes.</p>
        </div>

        <Card className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="First Name"
                placeholder="Pooja"
                leftIcon={<User className="w-4 h-4" />}
                value={formData.firstName}
                onChange={(e) => handleInputChange("firstName", e.target.value)}
                required
              />
              <Input
                label="Last Name"
                placeholder="Verma"
                value={formData.lastName}
                onChange={(e) => handleInputChange("lastName", e.target.value)}
              />
            </div>

            <Input
              label="Email Address"
              type="email"
              placeholder="pooja@company.com"
              leftIcon={<Mail className="w-4 h-4" />}
              value={formData.email}
              onChange={(e) => handleInputChange("email", e.target.value)}
              required
            />

            <Input
              label="Phone Number (Optional)"
              placeholder="+1 (555) 000-0000"
              leftIcon={<Phone className="w-4 h-4" />}
              value={formData.phone}
              onChange={(e) => handleInputChange("phone", e.target.value)}
            />

            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                leftIcon={<Lock className="w-4 h-4" />}
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
                required
              />
              <Input
                label="Confirm Password"
                type="password"
                placeholder="••••••••"
                leftIcon={<Lock className="w-4 h-4" />}
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                required
              />
            </div>

            <Button type="submit" variant="glow" className="w-full" isLoading={isLoading} rightIcon={<ArrowRight className="w-4 h-4" />}>
              Create Account & Start Free
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-slate-400">
          Already have an account?{" "}
          <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
