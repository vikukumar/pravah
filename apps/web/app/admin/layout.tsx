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
  CreditCard,
  Key,
  Bot,
  ScrollText,
  Package,
  Globe,
  Activity,
  Bell,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}
interface NavGroup {
  label: string;
  items: NavItem[];
}

const ADMIN_NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { name: "Platform Metrics", href: "/admin", icon: LayoutDashboard },
    ],
  },
  {
    label: "User & Org Management",
    items: [
      { name: "All Users", href: "/admin/users", icon: Users },
      { name: "All Workspaces", href: "/admin/organisations", icon: Building },
      { name: "Roles & Permissions", href: "/admin/roles", icon: Shield },
    ],
  },
  {
    label: "AI & Content",
    items: [
      { name: "AI Providers & Models", href: "/admin/ai-models", icon: Bot },
      { name: "CMS & Legal Pages", href: "/admin/cms", icon: FileText },
    ],
  },
  {
    label: "Integrations",
    items: [
      { name: "Social Media API Keys", href: "/admin/social-keys", icon: Globe },
      { name: "Payment Gateways", href: "/admin/payment-gateways", icon: CreditCard },
      { name: "Email & Notifications", href: "/admin/notifications", icon: Bell },
    ],
  },
  {
    label: "Billing & Plans",
    items: [
      { name: "Subscription Plans", href: "/admin/plans", icon: Package },
      { name: "Billing & Invoices", href: "/admin/billing", icon: CreditCard, badge: "Beta" },
    ],
  },
  {
    label: "System",
    items: [
      { name: "System Settings", href: "/admin/settings", icon: Sliders },
      { name: "API Keys & Secrets", href: "/admin/api-keys", icon: Key },
      { name: "Audit Trail", href: "/admin/audit-logs", icon: ScrollText },
      { name: "System Health", href: "/admin/health", icon: Activity },
    ],
  },
];

// Flat list for header lookup
const ALL_ADMIN_ITEMS = ADMIN_NAV_GROUPS.flatMap((g) => g.items);

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading } = useAuth();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

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

  const toggleGroup = (label: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      next.has(label) ? next.delete(label) : next.add(label);
      return next;
    });
  };

  const currentPageName = ALL_ADMIN_ITEMS.find((i) =>
    pathname === i.href || pathname.startsWith(i.href + "/")
  )?.name;

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
        <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-1 min-h-0">
          {!isSidebarCollapsed && (
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-red-950/30 border border-red-500/20 mb-3">
              <Shield className="w-4 h-4 text-red-400 shrink-0" />
              <div className="truncate">
                <p className="text-[10px] uppercase font-bold text-red-400">Super Administrator</p>
                <p className="text-xs font-semibold text-slate-200 truncate">{user.email}</p>
              </div>
            </div>
          )}

          {isSidebarCollapsed ? (
            // Collapsed: just icons
            <nav className="space-y-1">
              {ALL_ADMIN_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={item.name}
                    className={`flex items-center justify-center px-2 py-2.5 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                  </Link>
                );
              })}
            </nav>
          ) : (
            // Expanded: grouped nav
            <nav className="space-y-3">
              {ADMIN_NAV_GROUPS.map((group) => {
                const isGroupCollapsed = collapsedGroups.has(group.label);
                return (
                  <div key={group.label}>
                    {/* Group header */}
                    <button
                      onClick={() => toggleGroup(group.label)}
                      className="w-full flex items-center justify-between px-2 py-1 mb-1 group"
                    >
                      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 group-hover:text-slate-400 transition-colors">
                        {group.label}
                      </span>
                      {isGroupCollapsed ? (
                        <ChevronRight className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
                      )}
                    </button>

                    {/* Group items */}
                    {!isGroupCollapsed && (
                      <div className="space-y-0.5">
                        {group.items.map((item) => {
                          const Icon = item.icon;
                          const isActive =
                            pathname === item.href || pathname.startsWith(item.href + "/");
                          return (
                            <Link
                              key={item.href}
                              href={item.href}
                              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                                isActive
                                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                              }`}
                            >
                              <Icon className="w-3.5 h-3.5 shrink-0" />
                              <span className="truncate flex-1">{item.name}</span>
                              {item.badge && (
                                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                  {item.badge}
                                </span>
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </nav>
          )}
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
                {currentPageName || "Super Admin"}
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
