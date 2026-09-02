"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/providers/auth-provider";
import {
  CheckCircle2,
  Shield,
  Server,
  User,
  Key,
  CreditCard,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Lock,
} from "lucide-react";

export default function SetupWizardPage() {
  const router = useRouter();
  const { login } = useAuth();
  const toast = useToast();

  const [isChecking, setIsChecking] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    appName: "PRAVAH",
    appUrl: typeof window !== "undefined" ? window.location.origin : "http://localhost:3000",
    timezone: "UTC",
    locale: "en",
    currency: "USD",
    // Super admin
    firstName: "",
    middleName: "",
    lastName: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    // Platform features
    enableSSO: true,
    enable2FA: true,
    enablePublicRegistration: true,
  });

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const res = await fetchApi<{ is_initialized: boolean }>("/setup/status");
      if (res.is_initialized) {
        setIsInitialized(true);
      }
    } catch {
      // Backend not yet ready or offline
    } finally {
      setIsChecking(false);
    }
  };

  const handleInputChange = (field: string, val: any) => {
    setFormData((prev) => ({ ...prev, [field]: val }));
  };

  const handleFinishSetup = async () => {
    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (formData.password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    setIsLoading(true);
    try {
      const payload = {
        system: {
          app_name: formData.appName,
          app_url: formData.appUrl,
          timezone: formData.timezone,
          locale: formData.locale,
          currency: formData.currency,
        },
        super_admin: {
          first_name: formData.firstName,
          middle_name: formData.middleName || undefined,
          last_name: formData.lastName || undefined,
          email: formData.email,
          phone: formData.phone || undefined,
          password: formData.password,
          confirm_password: formData.confirmPassword,
        },
      };

      const res = await fetchApi<{ tokens: any; default_organisation_id: string }>(
        "/setup/initialize",
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );

      login(
        res.tokens.access_token,
        res.tokens.refresh_token,
        res.tokens.user
      );
      localStorage.setItem("pravah_active_org_id", res.default_organisation_id);

      toast.success("Platform initialized successfully!", "Welcome to PRAVAH Super Admin Dashboard.");
      router.push("/admin");
    } catch (err: any) {
      toast.error("Setup Failed", err.message || "Could not complete setup wizard.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#080c14] text-slate-300">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm">Inspecting PRAVAH deployment state...</p>
        </div>
      </div>
    );
  }

  const handleResetSetup = async () => {
    setIsLoading(true);
    try {
      await fetchApi("/setup/reset", { method: "POST" });
      toast.success("Database Reset", "You may now run through the initial setup wizard.");
      setIsInitialized(false);
      setCurrentStep(1);
    } catch (err: any) {
      toast.error("Reset Failed", err.message || "Could not reset setup.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-[#080c14]">
        <Card className="max-w-md w-full text-center py-8 space-y-4">
          <div className="w-14 h-14 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl flex items-center justify-center mx-auto">
            <Lock className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-100">Platform Already Initialized</h2>
          <p className="text-xs text-slate-400">
            PRAVAH has already completed first-run setup. You can log in with your Super Administrator credentials, or reset to run the Setup Wizard from scratch.
          </p>
          <div className="pt-2 space-y-2">
            <Button variant="primary" onClick={() => router.push("/login")} className="w-full">
              Proceed to Login
            </Button>
            <Button variant="outline" onClick={handleResetSetup} isLoading={isLoading} className="w-full text-xs">
              Reset & Run Setup Wizard
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const steps = [
    { num: 1, title: "System Info", icon: Server },
    { num: 2, title: "Super Admin", icon: User },
    { num: 3, title: "Security & 2FA", icon: Shield },
    { num: 4, title: "Free Plan & Launch", icon: Sparkles },
  ];

  return (
    <div className="min-h-screen bg-[#080c14] flex flex-col justify-center items-center p-4 selection:bg-indigo-500/30">
      {/* Background glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-indigo-600/10 blur-[140px] pointer-events-none rounded-full" />

      <div className="max-w-xl w-full relative z-10 space-y-6">
        {/* Header Logo */}
        <div className="text-center space-y-2">
          <div className="inline-block relative w-48 h-12 mb-2">
            <Image
              src="/images/pravah_horizontal_logo.png"
              alt="PRAVAH"
              fill
              className="object-contain"
              priority
            />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">First-Run Platform Setup</h1>
          <p className="text-xs text-slate-400">Configure your production instance in 4 quick steps.</p>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-between glass-panel rounded-xl p-3">
          {steps.map((s, idx) => {
            const Icon = s.icon;
            const isDone = currentStep > s.num;
            const isCurrent = currentStep === s.num;
            return (
              <div key={s.num} className="flex items-center gap-2">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-semibold transition-all ${
                    isDone
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : isCurrent
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  {isDone ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>
                <span
                  className={`text-xs hidden sm:inline ${
                    isCurrent ? "font-semibold text-slate-100" : "text-slate-400"
                  }`}
                >
                  {s.title}
                </span>
                {idx < steps.length - 1 && <div className="w-4 h-[1px] bg-slate-800 hidden sm:block" />}
              </div>
            );
          })}
        </div>

        {/* Step 1: System Info */}
        {currentStep === 1 && (
          <Card className="space-y-4">
            <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3">
              Step 1: System Configuration
            </h3>
            <Input
              label="Application Name"
              value={formData.appName}
              onChange={(e) => handleInputChange("appName", e.target.value)}
              required
            />
            <Input
              label="Application URL"
              value={formData.appUrl}
              onChange={(e) => handleInputChange("appUrl", e.target.value)}
              required
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Default Timezone"
                value={formData.timezone}
                onChange={(e) => handleInputChange("timezone", e.target.value)}
                required
              />
              <Input
                label="Default Currency"
                value={formData.currency}
                onChange={(e) => handleInputChange("currency", e.target.value)}
                required
              />
            </div>
            <div className="flex justify-end pt-3">
              <Button variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />} onClick={() => setCurrentStep(2)}>
                Next: Super Admin
              </Button>
            </div>
          </Card>
        )}

        {/* Step 2: Super Administrator */}
        {currentStep === 2 && (
          <Card className="space-y-4">
            <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3">
              Step 2: Create Super Administrator
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="First Name"
                value={formData.firstName}
                onChange={(e) => handleInputChange("firstName", e.target.value)}
                required
              />
              <Input
                label="Last Name"
                value={formData.lastName}
                onChange={(e) => handleInputChange("lastName", e.target.value)}
              />
            </div>
            <Input
              label="Admin Email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange("email", e.target.value)}
              required
            />
            <Input
              label="Phone (Optional)"
              value={formData.phone}
              onChange={(e) => handleInputChange("phone", e.target.value)}
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Master Password"
                type="password"
                value={formData.password}
                onChange={(e) => handleInputChange("password", e.target.value)}
                required
              />
              <Input
                label="Confirm Password"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
                required
              />
            </div>
            <div className="flex justify-between pt-3">
              <Button variant="outline" leftIcon={<ArrowLeft className="w-4 h-4" />} onClick={() => setCurrentStep(1)}>
                Back
              </Button>
              <Button
                variant="primary"
                rightIcon={<ArrowRight className="w-4 h-4" />}
                onClick={() => {
                  if (!formData.firstName || !formData.email || !formData.password) {
                    toast.error("Please fill in all required fields.");
                    return;
                  }
                  setCurrentStep(3);
                }}
              >
                Next: Security Policies
              </Button>
            </div>
          </Card>
        )}

        {/* Step 3: Security & Policies */}
        {currentStep === 3 && (
          <Card className="space-y-4">
            <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3">
              Step 3: Security Policies & Features
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer">
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Two-Factor Authentication (TOTP)</h4>
                  <p className="text-[11px] text-slate-400">Enforce Google Authenticator / Authy support</p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enable2FA}
                  onChange={(e) => handleInputChange("enable2FA", e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer">
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Enterprise SSO Architecture</h4>
                  <p className="text-[11px] text-slate-400">Support Google, GitHub, Microsoft, OIDC identity</p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enableSSO}
                  onChange={(e) => handleInputChange("enableSSO", e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer">
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Public Registration</h4>
                  <p className="text-[11px] text-slate-400">Allow new users to sign up from the public homepage</p>
                </div>
                <input
                  type="checkbox"
                  checked={formData.enablePublicRegistration}
                  onChange={(e) => handleInputChange("enablePublicRegistration", e.target.checked)}
                  className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                />
              </label>
            </div>
            <div className="flex justify-between pt-3">
              <Button variant="outline" leftIcon={<ArrowLeft className="w-4 h-4" />} onClick={() => setCurrentStep(2)}>
                Back
              </Button>
              <Button variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />} onClick={() => setCurrentStep(4)}>
                Next: Launch
              </Button>
            </div>
          </Card>
        )}

        {/* Step 4: Default Free Plan & Initialization */}
        {currentStep === 4 && (
          <Card className="space-y-4">
            <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3">
              Step 4: Default Free Plan & Initialization
            </h3>
            <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-300">Default Free Plan (Auto-Seeded)</span>
                <span className="text-[11px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-medium">
                  30 Days
                </span>
              </div>
              <ul className="text-xs text-slate-300 space-y-1">
                <li>• 1 Connected Social Account</li>
                <li>• 1 Post per Day</li>
                <li>• Full AI Studio Text Generation</li>
                <li>• Visual Workflow Builder Access</li>
              </ul>
            </div>
            <p className="text-xs text-slate-400">
              Clicking below will initialize the database, seed permissions, create your Super Admin account, and lock the setup wizard.
            </p>
            <div className="flex justify-between pt-3">
              <Button variant="outline" leftIcon={<ArrowLeft className="w-4 h-4" />} onClick={() => setCurrentStep(3)} disabled={isLoading}>
                Back
              </Button>
              <Button variant="glow" onClick={handleFinishSetup} isLoading={isLoading}>
                Complete Setup & Launch
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
