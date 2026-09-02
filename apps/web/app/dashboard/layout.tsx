"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { useOrganisation } from "@/providers/org-provider";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  LayoutDashboard,
  Bot,
  FileText,
  Calendar,
  Share2,
  Workflow,
  BarChart3,
  Layers,
  Image as ImageIcon,
  Users,
  CreditCard,
  Settings,
  Bell,
  LogOut,
  ChevronDown,
  Sparkles,
  Shield,
  Check,
  PanelLeftClose,
  PanelLeftOpen,
  Menu,
} from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const { organisations, activeOrg, switchOrganisation } = useOrganisation();

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [orgDropdownOpen, setOrgDropdownOpen] = useState(false);
  const [notifsOpen, setNotifsOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchApi<any[]>("/notifications")
        .then((data) => setNotifications(data))
        .catch(() => {});
    }
  }, [isAuthenticated]);

  if (authLoading || !isAuthenticated) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#080c14] text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const navItems = [
    { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { name: "AI Studio", href: "/dashboard/ai-studio", icon: Bot, highlight: true },
    { name: "Content & Posts", href: "/dashboard/content", icon: FileText },
    { name: "Calendar", href: "/dashboard/calendar", icon: Calendar },
    { name: "Social Accounts", href: "/dashboard/social", icon: Share2 },
    { name: "No-Code Workflows", href: "/dashboard/workflows", icon: Workflow },
    { name: "Analytics & ROI", href: "/dashboard/analytics", icon: BarChart3 },
    { name: "Campaigns", href: "/dashboard/campaigns", icon: Layers },
    { name: "Media Assets", href: "/dashboard/media", icon: ImageIcon },
    { name: "Team & Roles", href: "/dashboard/team", icon: Users },
    { name: "Billing & Quotas", href: "/dashboard/billing", icon: CreditCard },
    { name: "Workspace Settings", href: "/dashboard/settings", icon: Settings },
  ];

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#080c14] flex text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Sidebar - Constrained strictly to single screen with internal smooth scrolling */}
      <aside
        className={`h-screen sticky top-0 flex flex-col justify-between shrink-0 border-r border-slate-800/80 bg-[#0a0f1d] z-40 transition-all duration-300 ease-in-out ${
          isSidebarCollapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Top Header / Branding & Toggle */}
        <div className="p-3.5 border-b border-slate-800/60 flex items-center justify-between shrink-0">
          {!isSidebarCollapsed ? (
            <>
              <Link href="/dashboard" className="block relative w-32 h-8">
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

        {/* Scrollable Center Nav Section (no outer page scroll spillover) */}
        <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-4 min-h-0">
          {/* Active Workspace / Org Switcher */}
          {!isSidebarCollapsed && (
            <div className="relative">
              <button
                onClick={() => setOrgDropdownOpen(!orgDropdownOpen)}
                className="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-colors text-left"
              >
                <div className="truncate">
                  <p className="text-[10px] uppercase font-semibold tracking-wider text-slate-500">Workspace</p>
                  <p className="text-xs font-semibold text-slate-200 truncate">
                    {activeOrg?.name || "Select Brand"}
                  </p>
                </div>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${orgDropdownOpen ? "rotate-180" : ""}`} />
              </button>

              {/* Dropdown Menu */}
              {orgDropdownOpen && (
                <div className="absolute top-full left-0 mt-1 w-full bg-[#0d1322] border border-slate-700/80 rounded-xl shadow-2xl p-2 z-50 space-y-1 animate-in fade-in zoom-in-95">
                  <p className="text-[10px] text-slate-400 px-2 py-1 uppercase font-semibold">Your Brands</p>
                  {organisations.map((org) => (
                    <button
                      key={org.id}
                      onClick={() => {
                        switchOrganisation(org.id);
                        setOrgDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors text-left ${
                        org.id === activeOrg?.id
                          ? "bg-indigo-600/20 text-indigo-300 font-semibold"
                          : "text-slate-300 hover:bg-slate-800"
                      }`}
                    >
                      <span className="truncate">{org.name}</span>
                      {org.id === activeOrg?.id && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={isSidebarCollapsed ? item.name : undefined}
                  className={`flex items-center ${
                    isSidebarCollapsed ? "justify-center px-2 py-2.5" : "justify-between px-3 py-2"
                  } rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-white" : item.highlight ? "text-indigo-400" : "text-slate-400"}`} />
                    {!isSidebarCollapsed && <span className="truncate">{item.name}</span>}
                  </div>
                  {!isSidebarCollapsed && item.highlight && !isActive && (
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Profile & Footer Actions (Fixed Bottom) */}
        <div className="p-3 border-t border-slate-800/80 space-y-2 bg-[#080c14]/40 shrink-0">
          {user?.isSuperAdmin && !isSidebarCollapsed && (
            <Link href="/admin">
              <Button variant="outline" size="sm" className="w-full text-xs text-indigo-300 border-indigo-500/30" leftIcon={<Shield className="w-3.5 h-3.5 text-indigo-400" />}>
                Super Admin
              </Button>
            </Link>
          )}

          {user?.isSuperAdmin && isSidebarCollapsed && (
            <Link href="/admin" title="Super Admin Panel" className="flex items-center justify-center p-2 rounded-xl text-indigo-400 hover:bg-slate-800/60 transition-colors">
              <Shield className="w-4 h-4" />
            </Link>
          )}

          <div className={`flex items-center ${isSidebarCollapsed ? "justify-center" : "justify-between"} pt-1`}>
            {!isSidebarCollapsed && (
              <div className="truncate max-w-[150px]">
                <p className="text-xs font-semibold text-slate-200 truncate">
                  {user?.firstName} {user?.lastName}
                </p>
                <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
              </div>
            )}
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area - Full screen viewport with independent smooth scrolling */}
      <div className="flex-1 h-screen flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 shrink-0 border-b border-slate-800/80 bg-[#080c14]/80 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
            {/* Collapse / Expand Hamburger Toggle */}
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
              className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors"
            >
              <Menu className="w-4 h-4 text-slate-300" />
            </button>

            <h2 className="text-sm font-semibold text-slate-200">
              {navItems.find((i) => i.href === pathname)?.name || "Dashboard"}
            </h2>
            {activeOrg && (
              <Badge variant="purple" className="text-[10px] hidden sm:inline-flex">
                {activeOrg.name}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Link href="/dashboard/ai-studio">
              <Button variant="glow" size="sm" leftIcon={<Sparkles className="w-3.5 h-3.5" />}>
                Generate AI Post
              </Button>
            </Link>

            {/* Notifications Popover */}
            <div className="relative">
              <button
                onClick={() => setNotifsOpen(!notifsOpen)}
                className="relative p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-colors"
              >
                <Bell className="w-4 h-4" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-indigo-500 text-[10px] font-bold text-white rounded-full flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>

              {notifsOpen && (
                <div className="absolute right-0 top-full mt-2 w-80 bg-[#0d1322] border border-slate-700/80 rounded-2xl shadow-2xl p-4 z-50 space-y-3 animate-in fade-in zoom-in-95">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <h4 className="text-xs font-semibold text-slate-200">Notifications</h4>
                    <span className="text-[10px] text-slate-400">{notifications.length} total</span>
                  </div>

                  <div className="space-y-2 max-h-60 overflow-y-auto no-scrollbar">
                    {notifications.length === 0 ? (
                      <p className="text-xs text-slate-400 text-center py-4">No notifications yet.</p>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 text-xs"
                        >
                          <p className="font-semibold text-slate-200">{n.title}</p>
                          <p className="text-slate-400 text-[11px]">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Dashboard Viewport - Independent smooth scroll, fits single screen */}
        <main className="flex-1 h-[calc(100vh-4rem)] overflow-y-auto p-4 sm:p-6 lg:p-8 no-scrollbar">
          {children}
        </main>
      </div>
    </div>
  );
}
