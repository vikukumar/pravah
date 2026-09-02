"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useOrganisation } from "@/providers/org-provider";
import { formatDate } from "@/lib/utils";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Plus,
  Sparkles,
} from "lucide-react";

export default function CalendarPage() {
  const { activeOrg } = useOrganisation();
  const [scheduledItems, setScheduledItems] = useState<any[]>([]);
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [recommendation, setRecommendation] = useState<any>(null);

  useEffect(() => {
    if (!activeOrg) return;

    fetchApi<any[]>("/content/calendar")
      .then((data) => setScheduledItems(data))
      .catch(() => {});

    fetchApi<any>("/ai/recommend-best-time?platform=x")
      .then((rec) => setRecommendation(rec))
      .catch(() => {});
  }, [activeOrg]);

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();

  const days = [];
  for (let i = 0; i < firstDayOfWeek; i++) {
    days.push(null);
  }
  for (let d = 1; d <= daysInMonth; d++) {
    days.push(d);
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <CalendarIcon className="w-6 h-6 text-indigo-400" /> Content Scheduling Calendar
          </h1>
          <p className="text-xs text-slate-400">
            View scheduled posts, peak engagement windows, and distribution timing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={handlePrevMonth}
              className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-semibold px-3 text-slate-200">
              {monthNames[currentMonth]} {currentYear}
            </span>
            <button
              onClick={handleNextMonth}
              className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <Link href="/dashboard/content">
            <Button variant="glow" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
              Schedule Post
            </Button>
          </Link>
        </div>
      </div>

      {/* AI Recommendation Alert */}
      {recommendation && (
        <div className="glass-panel p-4 rounded-xl border-indigo-500/30 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-200">Optimal AI Recommendation Window</p>
              <p className="text-[11px] text-slate-400">
                {recommendation.reason} ({recommendation.confidence_score * 100}% Confidence)
              </p>
            </div>
          </div>
          <Link href="/dashboard/ai-studio">
            <Button variant="outline" size="sm" className="shrink-0 text-xs">
              Fill Optimal Slot
            </Button>
          </Link>
        </div>
      )}

      {/* Calendar Grid */}
      <Card className="p-4 space-y-4">
        {/* Days of week header */}
        <div className="grid grid-cols-7 gap-2 text-center text-xs font-semibold text-slate-400 pb-2 border-b border-slate-800">
          <div>SUN</div>
          <div>MON</div>
          <div>TUE</div>
          <div>WED</div>
          <div>THU</div>
          <div>FRI</div>
          <div>SAT</div>
        </div>

        {/* Days cells */}
        <div className="grid grid-cols-7 gap-2">
          {days.map((day, idx) => {
            if (day === null) {
              return <div key={`empty-${idx}`} className="h-28 bg-slate-950/20 rounded-xl" />;
            }

            const isToday =
              day === new Date().getDate() &&
              currentMonth === new Date().getMonth() &&
              currentYear === new Date().getFullYear();

            // Find scheduled items on this day
            const itemsOnDay = scheduledItems.filter((item) => {
              if (!item.scheduled_for) return false;
              const itemDate = new Date(item.scheduled_for);
              return (
                itemDate.getDate() === day &&
                itemDate.getMonth() === currentMonth &&
                itemDate.getFullYear() === currentYear
              );
            });

            return (
              <div
                key={`day-${day}`}
                className={`h-28 p-2 rounded-xl border flex flex-col justify-between transition-colors ${
                  isToday
                    ? "bg-indigo-950/20 border-indigo-500/50 shadow-md shadow-indigo-500/10"
                    : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-semibold ${
                      isToday ? "text-indigo-400" : "text-slate-400"
                    }`}
                  >
                    {day}
                  </span>
                  {itemsOnDay.length > 0 && (
                    <span className="w-2 h-2 rounded-full bg-indigo-500" />
                  )}
                </div>

                <div className="space-y-1 overflow-y-auto max-h-16">
                  {itemsOnDay.map((item, iIdx) => (
                    <div
                      key={iIdx}
                      className="p-1 rounded bg-indigo-600/20 border border-indigo-500/30 text-[10px] text-indigo-200 truncate font-mono"
                    >
                      {item.title || "Scheduled Post"}
                    </div>
                  ))}
                </div>

                <div className="text-[10px] text-slate-600 text-right">
                  {itemsOnDay.length > 0 ? `${itemsOnDay.length} post(s)` : ""}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
