"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Shield,
  LayoutDashboard,
  Users,
  Building,
  FileText,
  Sliders,
  ArrowLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Menu,
} from "lucide-react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuth();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated || !user?.isSuperAdmin) {
        router.push("/dashboard");
      }
    }
  }, [isLoading, isAuthenticated, user, router]);

  if (isLoading || !isAuthenticated || !user?.isSuperAdmin) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#080c14] text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const adminNav = [
    { name: "Platform Metrics", href: "/admin", icon: LayoutDashboard },
    { name: "AI Providers & Models", href: "/admin/ai-models", icon: Sliders },
    { name: "Social Media API Keys", href: "/admin/social-keys", icon: Shield },
    { name: "CMS & Legal Pages", href: "/admin/cms", icon: FileText },
    { name: "All Users", href: "/admin/users", icon: Users },
    { name: "All Workspaces", href: "/admin/organisations", icon: Building },
    { name: "Audit Trail", href: "/admin/audit-logs", icon: FileText },
    { name: "System Settings", href: "/admin/settings", icon: Sliders },
  ];

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#080c14] flex text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Super Admin Sidebar */}
      <aside
        className={`h-screen sticky top-0 flex flex-col justify-between shrink-0 border-r border-slate-800/80 bg-[#0a0f1d] z-40 transition-all duration-300 ease-in-out ${
          isSidebarCollapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Top Header / Branding */}
        <div className="p-3.5 border-b border-slate-800/60 flex items-center justify-between shrink-0">
          {!isSidebarCollapsed ? (
            <>
              <Link href="/admin" className="block relative w-32 h-8">
                <Image
                  src="/images/pravah_horizontal_logo.png"
                  alt="PRAVAH"
                  fill
                  className="object-contain"
                  priority
                />
              </Link>
              <button
                onClick={() => setIsSidebarCollapsed(true)}
                title="Collapse Sidebar"
                className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800/60 transition-colors"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </>
          ) : (
            <div className="w-full flex items-center justify-center">
              <button
                onClick={() => setIsSidebarCollapsed(false)}
                title="Expand Sidebar"
                className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800/60 transition-colors"
              >
                <PanelLeftOpen className="w-5 h-5 text-indigo-400" />
              </button>
            </div>
          )}
        </div>

        {/* Scrollable Nav Container */}
        <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-4 min-h-0">
          {!isSidebarCollapsed && (
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30">
              <Shield className="w-4 h-4 text-indigo-400 shrink-0" />
              <div className="truncate">
                <p className="text-[10px] uppercase font-bold text-indigo-300">Super Administrator</p>
                <p className="text-xs font-semibold text-slate-200 truncate">{user.email}</p>
              </div>
            </div>
          )}

          <nav className="space-y-1">
            {adminNav.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={isSidebarCollapsed ? item.name : undefined}
                  className={`flex items-center ${
                    isSidebarCollapsed ? "justify-center px-2 py-2.5" : "gap-2.5 px-3 py-2"
                  } rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  {!isSidebarCollapsed && <span className="truncate">{item.name}</span>}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Fixed Footer */}
        <div className="p-3 border-t border-slate-800/80 shrink-0">
          <Link href="/dashboard" title="Return to Brand App">
            <Button
              variant="outline"
              size="sm"
              className={`w-full text-xs ${isSidebarCollapsed ? "px-2 flex justify-center" : ""}`}
              leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
            >
              {!isSidebarCollapsed && "Back to Workspace"}
            </Button>
          </Link>
        </div>
      </aside>

      {/* Main Admin Viewport */}
      <div className="flex-1 h-screen flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 shrink-0 border-b border-slate-800/80 bg-[#080c14]/80 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors"
            >
              <Menu className="w-4 h-4 text-slate-300" />
            </button>

            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-slate-200">
                {adminNav.find((i) => i.href === pathname)?.name || "Super Admin"}
              </h2>
              <Badge variant="purple" className="text-[10px]">Master Console</Badge>
            </div>
          </div>

          <Link href="/dashboard">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}>
              Exit to Dashboard
            </Button>
          </Link>
        </header>

        {/* Admin Content Viewport */}
        <main className="flex-1 h-[calc(100vh-4rem)] overflow-y-auto p-4 sm:p-6 lg:p-8 no-scrollbar">
          {children}
        </main>
      </div>
    </div>
  );
}
