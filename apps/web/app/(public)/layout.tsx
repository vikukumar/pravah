"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/auth-provider";
import { Sparkles, Menu, X, ArrowRight, Shield } from "lucide-react";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-[#080c14]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="relative w-36 h-9">
              <Image
                src="/images/pravah_horizontal_logo.png"
                alt="PRAVAH"
                fill
                className="object-contain"
                priority
              />
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <Link href="/features" className="hover:text-indigo-400 transition-colors">
              Features
            </Link>
            <Link href="/integrations" className="hover:text-indigo-400 transition-colors">
              Integrations
            </Link>
            <Link href="/pricing" className="hover:text-indigo-400 transition-colors">
              Pricing
            </Link>
            <Link href="/about" className="hover:text-indigo-400 transition-colors">
              About
            </Link>
            <Link href="/blog" className="hover:text-indigo-400 transition-colors">
              Blog
            </Link>
            <Link href="/contact" className="hover:text-indigo-400 transition-colors">
              Contact
            </Link>
          </nav>

          {/* Actions */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <Link href={user?.isSuperAdmin ? "/admin" : "/dashboard"}>
                <Button variant="glow" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  {user?.isSuperAdmin ? "Admin Panel" : "Go to Dashboard"}
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign In
                  </Button>
                </Link>
                <Link href="/register">
                  <Button variant="glow" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    Start Free Trial
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden text-slate-400 hover:text-slate-200 p-2"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden border-b border-slate-800 bg-[#0d1322] px-4 py-4 space-y-3">
            <Link href="/features" className="block text-sm text-slate-300 py-1" onClick={() => setMobileMenuOpen(false)}>
              Features
            </Link>
            <Link href="/integrations" className="block text-sm text-slate-300 py-1" onClick={() => setMobileMenuOpen(false)}>
              Integrations
            </Link>
            <Link href="/pricing" className="block text-sm text-slate-300 py-1" onClick={() => setMobileMenuOpen(false)}>
              Pricing
            </Link>
            <Link href="/about" className="block text-sm text-slate-300 py-1" onClick={() => setMobileMenuOpen(false)}>
              About
            </Link>
            <Link href="/blog" className="block text-sm text-slate-300 py-1" onClick={() => setMobileMenuOpen(false)}>
              Blog
            </Link>
            <Link href="/contact" className="block text-sm text-slate-300 py-1" onClick={() => setMobileMenuOpen(false)}>
              Contact
            </Link>
            <div className="pt-2 flex flex-col gap-2">
              <Link href="/login">
                <Button variant="outline" size="sm" className="w-full">
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
                <Button variant="glow" size="sm" className="w-full">
                  Start Free Trial
                </Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#060910] pt-16 pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
            <div className="col-span-2 space-y-4">
              <div className="relative w-36 h-9">
                <Image
                  src="/images/pravah_horizontal_logo.png"
                  alt="PRAVAH"
                  fill
                  className="object-contain"
                />
              </div>
              <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
                प्रवाह — The AI social media operating system. Multi-tenant brand intelligence, visual automation workflows, and official platform publishing.
              </p>
              <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full w-fit">
                <Shield className="w-3.5 h-3.5" /> Official API Integrations & Encrypted Secrets
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Product</h4>
              <ul className="space-y-2 text-xs text-slate-400">
                <li><Link href="/features" className="hover:text-indigo-400 transition-colors">AI Studio</Link></li>
                <li><Link href="/features" className="hover:text-indigo-400 transition-colors">Visual Workflows</Link></li>
                <li><Link href="/integrations" className="hover:text-indigo-400 transition-colors">Social Connect</Link></li>
                <li><Link href="/pricing" className="hover:text-indigo-400 transition-colors">Pricing Plans</Link></li>
                <li><Link href="/features" className="hover:text-indigo-400 transition-colors">Best Time Engine</Link></li>
              </ul>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Company</h4>
              <ul className="space-y-2 text-xs text-slate-400">
                <li><Link href="/about" className="hover:text-indigo-400 transition-colors">About Us</Link></li>
                <li><Link href="/blog" className="hover:text-indigo-400 transition-colors">Engineering Blog</Link></li>
                <li><Link href="/contact" className="hover:text-indigo-400 transition-colors">Contact Us</Link></li>
                <li><Link href="/pricing" className="hover:text-indigo-400 transition-colors">Enterprise Plans</Link></li>
              </ul>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Legal & Trust</h4>
              <ul className="space-y-2 text-xs text-slate-400">
                <li><Link href="/terms" className="hover:text-indigo-400 transition-colors">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-indigo-400 transition-colors">Privacy Policy</Link></li>
                <li><Link href="/refund" className="hover:text-indigo-400 transition-colors">Refund Policy</Link></li>
                <li><Link href="/cookie-policy" className="hover:text-indigo-400 transition-colors">Cookie Policy</Link></li>
                <li><Link href="/security" className="hover:text-indigo-400 transition-colors">Security Architecture</Link></li>
                <li><Link href="/acceptable-use" className="hover:text-indigo-400 transition-colors">Acceptable Use</Link></li>
                <li><Link href="/ai-policy" className="hover:text-indigo-400 transition-colors">AI & Ethics Policy</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-800/60 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
            <p>© {new Date().getFullYear()} PRAVAH Platform. All rights reserved.</p>
            <p>Designed for creators, businesses, and enterprise agencies.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
