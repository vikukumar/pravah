"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useOrganisation } from "@/providers/org-provider";
import { useToast } from "@/components/ui/toast";
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Plus,
  Sparkles,
  Globe,
  Link2,
  Sun,
  Moon,
  Star,
  Zap,
} from "lucide-react";

interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  event_type: string;
  category?: string;
  event_date: string;
  is_all_day?: boolean;
  emoji?: string;
  color?: string;
  importance?: number;
  source?: string;
}

interface ContentSuggestion {
  event_id?: string;
  event_title: string;
  event_emoji?: string;
  event_category?: string;
  event_color?: string;
  topic: string;
  image_prompt?: string;
  hashtags?: string[];
}

interface CalendarData {
  year: number;
  month: number;
  by_date: Record<string, CalendarEvent[]>;
  total_events: number;
  has_google_calendar: boolean;
}

const CATEGORY_ICONS: Record<string, string> = {
  hindu: "🕉️",
  muslim: "☪️",
  christian: "✝️",
  sikh: "☬",
  buddhist: "☸️",
  jain: "🙏",
  national: "🇮🇳",
  secular: "🌍",
  custom: "📌",
  google: "📅",
};

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];
const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function CalendarPage() {
  const { activeOrg } = useOrganisation();
  const toast = useToast();
  const router = useRouter();

  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [calendarData, setCalendarData] = useState<CalendarData | null>(null);
  const [scheduledItems, setScheduledItems] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<ContentSuggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [googleConnected, setGoogleConnected] = useState(false);

  const fetchCalendarData = useCallback(async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const [calData, contentData] = await Promise.all([
        fetchApi<CalendarData>(
          `/calendar/events?year=${currentYear}&month=${currentMonth + 1}`
        ),
        fetchApi<any[]>("/content/calendar").catch(() => []),
      ]);
      setCalendarData(calData);
      setScheduledItems(contentData || []);
      setGoogleConnected(calData.has_google_calendar);
    } catch {
      // calendar API might not have events seeded yet
    } finally {
      setIsLoading(false);
    }
  }, [activeOrg, currentMonth, currentYear]);

  useEffect(() => {
    fetchCalendarData();
  }, [fetchCalendarData]);

  const handleDayClick = useCallback(
    async (dateStr: string) => {
      setSelectedDate(dateStr);
      setLoadingSuggestions(true);
      setSuggestions([]);
      try {
        const data = await fetchApi<ContentSuggestion[]>(
          `/calendar/suggestions?event_date=${dateStr}`
        );
        setSuggestions(data || []);
      } catch {
        setSuggestions([]);
      } finally {
        setLoadingSuggestions(false);
      }
    },
    []
  );

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear((y) => y - 1);
    } else {
      setCurrentMonth((m) => m - 1);
    }
    setSelectedDate(null);
    setSuggestions([]);
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear((y) => y + 1);
    } else {
      setCurrentMonth((m) => m + 1);
    }
    setSelectedDate(null);
    setSuggestions([]);
  };

  const handleGoToToday = () => {
    const now = new Date();
    setCurrentMonth(now.getMonth());
    setCurrentYear(now.getFullYear());
  };

  const handleUseSuggestion = (suggestion: ContentSuggestion) => {
    const params = new URLSearchParams({
      topic: suggestion.topic,
      event: suggestion.event_title,
      hashtags: (suggestion.hashtags || []).join(","),
    });
    router.push(`/dashboard/ai-studio?${params.toString()}`);
  };

  const handleConnectGoogle = async () => {
    try {
      const redirectUri = `${window.location.origin}/dashboard/calendar/google-callback`;
      const result = await fetchApi<any>("/calendar/link-google", {
        method: "POST",
        body: JSON.stringify({ redirect_uri: redirectUri }),
      });
      if (result.authorization_url) {
        window.location.href = result.authorization_url;
      } else {
        toast.error(result.message || "Google Calendar not configured");
      }
    } catch {
      toast.error("Failed to initiate Google Calendar connection");
    }
  };

  // Build days array for the month
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfWeek = new Date(currentYear, currentMonth, 1).getDay();
  const days: (number | null)[] = [];
  for (let i = 0; i < firstDayOfWeek; i++) days.push(null);
  for (let d = 1; d <= daysInMonth; d++) days.push(d);

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  const getDateStr = (day: number) =>
    `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

  const getEventsForDay = (day: number): CalendarEvent[] => {
    const ds = getDateStr(day);
    return calendarData?.by_date[ds] || [];
  };

  const getScheduledForDay = (day: number) => {
    return scheduledItems.filter((item) => {
      if (!item.scheduled_for) return false;
      const d = new Date(item.scheduled_for);
      return d.getDate() === day && d.getMonth() === currentMonth && d.getFullYear() === currentYear;
    });
  };

  const selectedEvents = selectedDate
    ? calendarData?.by_date[selectedDate] || []
    : [];
  const selectedScheduled = selectedDate
    ? scheduledItems.filter((item) => {
        if (!item.scheduled_for) return false;
        const d = new Date(item.scheduled_for);
        const ds = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
        return ds === selectedDate;
      })
    : [];

  return (
    <div className="max-w-[1600px] mx-auto space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
            <CalendarIcon className="w-6 h-6 text-indigo-400" />
            Content Calendar
          </h1>
          <p className="text-xs text-slate-400">
            Festivals, holidays, scheduled posts, and AI content suggestions — all in one view.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {!googleConnected && (
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Globe className="w-3.5 h-3.5" />}
              onClick={handleConnectGoogle}
              className="text-xs"
            >
              Connect Google Calendar
            </Button>
          )}
          {googleConnected && (
            <Badge variant="info" className="text-xs text-emerald-400 border-emerald-500/30 gap-1.5">
              <Globe className="w-3 h-3" /> Google Calendar Connected
            </Badge>
          )}
          <Link href="/dashboard/ai-studio">
            <Button variant="glow" size="sm" leftIcon={<Sparkles className="w-3.5 h-3.5" />}>
              Auto Generate
            </Button>
          </Link>
          <Link href="/dashboard/content">
            <Button variant="outline" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />}>
              Schedule Post
            </Button>
          </Link>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 flex-wrap text-[11px] text-slate-400">
        <span className="font-semibold text-slate-300">Legend:</span>
        {Object.entries(CATEGORY_ICONS).slice(0, 7).map(([cat, icon]) => (
          <span key={cat} className="flex items-center gap-1">
            <span>{icon}</span>
            <span className="capitalize">{cat}</span>
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-indigo-500 inline-block" />
          <span>Scheduled post</span>
        </span>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-5">
        {/* Calendar Grid — takes 3/4 width */}
        <div className="xl:col-span-3 space-y-4">
          {/* Month nav */}
          <Card className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <button
                  onClick={handlePrevMonth}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-base font-bold text-slate-100 min-w-[150px] text-center">
                  {MONTH_NAMES[currentMonth]} {currentYear}
                </span>
                <button
                  onClick={handleNextMonth}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={handleGoToToday}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300 transition-colors px-2 py-1 rounded-lg hover:bg-indigo-500/10 border border-indigo-500/20"
                >
                  Today
                </button>
              </div>
              <div className="text-[11px] text-slate-500">
                {calendarData?.total_events || 0} events this month
              </div>
            </div>

            {/* Day headers */}
            <div className="grid grid-cols-7 gap-1.5 mb-1.5">
              {DAY_NAMES.map((d) => (
                <div
                  key={d}
                  className="text-center text-[11px] font-semibold text-slate-500 py-1"
                >
                  {d}
                </div>
              ))}
            </div>

            {/* Day cells */}
            {isLoading ? (
              <div className="grid grid-cols-7 gap-1.5">
                {Array.from({ length: 35 }).map((_, i) => (
                  <div key={i} className="h-24 rounded-xl bg-slate-900/40 animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-7 gap-1.5">
                {days.map((day, idx) => {
                  if (day === null) {
                    return (
                      <div
                        key={`empty-${idx}`}
                        className="h-24 rounded-xl bg-slate-950/20"
                      />
                    );
                  }

                  const ds = getDateStr(day);
                  const isToday = ds === todayStr;
                  const isSelected = ds === selectedDate;
                  const events = getEventsForDay(day);
                  const scheduled = getScheduledForDay(day);
                  const topEvent = events.find((e) => e.importance === 1) || events[0];
                  const hasScheduled = scheduled.length > 0;
                  const majorFestival = events.find((e) => e.importance === 1);

                  return (
                    <button
                      key={`day-${day}`}
                      onClick={() => handleDayClick(ds)}
                      className={`h-24 p-2 rounded-xl border text-left flex flex-col justify-between transition-all duration-200 relative group ${
                        isSelected
                          ? "bg-indigo-950/30 border-indigo-500/70 shadow-lg shadow-indigo-500/10 scale-[1.02]"
                          : isToday
                          ? "bg-indigo-950/20 border-indigo-500/40"
                          : "bg-slate-900/40 border-slate-800/80 hover:border-slate-600 hover:bg-slate-900/60"
                      }`}
                    >
                      {/* Day number */}
                      <div className="flex items-center justify-between">
                        <span
                          className={`text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full ${
                            isToday
                              ? "bg-indigo-500 text-white"
                              : isSelected
                              ? "text-indigo-300"
                              : "text-slate-400"
                          }`}
                        >
                          {day}
                        </span>
                        {hasScheduled && (
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                        )}
                      </div>

                      {/* Festival indicator */}
                      {majorFestival && (
                        <div
                          className="px-1 py-0.5 rounded text-[9px] font-semibold truncate flex items-center gap-0.5"
                          style={{
                            backgroundColor: `${majorFestival.color}20`,
                            color: majorFestival.color || "#E5E7EB",
                            borderLeft: `2px solid ${majorFestival.color || "#6366F1"}`,
                          }}
                        >
                          <span>{majorFestival.emoji}</span>
                          <span className="truncate">{majorFestival.title}</span>
                        </div>
                      )}

                      {/* Additional events count */}
                      <div className="flex items-center justify-between gap-1">
                        {events.length > 1 && (
                          <span className="text-[9px] text-slate-500">
                            +{events.length - 1} more
                          </span>
                        )}
                        {hasScheduled && (
                          <span className="text-[9px] text-indigo-400 ml-auto">
                            {scheduled.length}📝
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Side Panel — 1/4 width */}
        <div className="xl:col-span-1 space-y-4">
          {/* Selected Day Details */}
          {selectedDate ? (
            <Card className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-100">
                  {new Date(selectedDate + "T00:00:00").toLocaleDateString("en-IN", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                  })}
                </h3>
                <button
                  onClick={() => { setSelectedDate(null); setSuggestions([]); }}
                  className="text-slate-500 hover:text-slate-300 text-xs"
                >
                  ✕
                </button>
              </div>

              {/* Events on this day */}
              {selectedEvents.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Occasions
                  </p>
                  {selectedEvents.map((ev) => (
                    <div
                      key={ev.id}
                      className="flex items-start gap-2 p-2 rounded-lg"
                      style={{ backgroundColor: `${ev.color}10`, borderLeft: `3px solid ${ev.color || "#6366F1"}` }}
                    >
                      <span className="text-sm">{ev.emoji}</span>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-200 leading-tight">
                          {ev.title}
                        </p>
                        {ev.description && (
                          <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed line-clamp-2">
                            {ev.description}
                          </p>
                        )}
                        <span
                          className="text-[9px] capitalize"
                          style={{ color: ev.color || "#94A3B8" }}
                        >
                          {CATEGORY_ICONS[ev.category || ""] || ""} {ev.category}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Scheduled posts on this day */}
              {selectedScheduled.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    Scheduled Posts ({selectedScheduled.length})
                  </p>
                  {selectedScheduled.slice(0, 3).map((item, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20"
                    >
                      <p className="text-[11px] font-semibold text-indigo-200 truncate">
                        {item.title || "Scheduled Post"}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-0.5 truncate">
                        {item.platforms?.join(", ")}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* AI Content Suggestions */}
              <div className="space-y-2">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                    AI Suggestions
                  </p>
                </div>

                {loadingSuggestions ? (
                  <div className="space-y-2">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-12 rounded-lg bg-slate-800/50 animate-pulse" />
                    ))}
                  </div>
                ) : suggestions.length > 0 ? (
                  <div className="space-y-2">
                    {suggestions.slice(0, 4).map((s, i) => (
                      <button
                        key={i}
                        onClick={() => handleUseSuggestion(s)}
                        className="w-full text-left p-2 rounded-lg bg-amber-500/5 border border-amber-500/20 hover:bg-amber-500/10 hover:border-amber-500/40 transition-all group"
                      >
                        <div className="flex items-start gap-1.5">
                          <span className="text-sm shrink-0">{s.event_emoji || "✨"}</span>
                          <div className="min-w-0">
                            <p className="text-[10px] text-amber-200/80 leading-tight line-clamp-2 group-hover:text-amber-200">
                              {s.topic}
                            </p>
                            {s.hashtags && s.hashtags.length > 0 && (
                              <p className="text-[9px] text-slate-500 mt-0.5 truncate">
                                #{s.hashtags.slice(0, 2).join(" #")}
                              </p>
                            )}
                          </div>
                          <Zap className="w-3 h-3 text-amber-500/60 group-hover:text-amber-400 shrink-0 mt-0.5 transition-colors" />
                        </div>
                      </button>
                    ))}
                  </div>
                ) : selectedEvents.length === 0 ? (
                  <p className="text-[10px] text-slate-500 italic">
                    No events on this day. Click a day with festivals for suggestions.
                  </p>
                ) : (
                  <p className="text-[10px] text-slate-500 italic">
                    No suggestions available for this date.
                  </p>
                )}
              </div>
            </Card>
          ) : (
            <Card className="p-4 space-y-3">
              <div className="flex items-center gap-2 text-slate-300">
                <CalendarIcon className="w-4 h-4 text-indigo-400" />
                <span className="text-sm font-semibold">Select a Day</span>
              </div>
              <p className="text-xs text-slate-500">
                Click on any calendar day to see festivals, scheduled posts, and AI content suggestions.
              </p>
              <div className="p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/20 space-y-1">
                <p className="text-[11px] text-indigo-300 font-semibold">💡 Pro Tip</p>
                <p className="text-[10px] text-slate-400">
                  Days with 🪔 festival indicators have pre-generated AI content suggestions.
                  Click them to auto-fill the AI Studio!
                </p>
              </div>
            </Card>
          )}

          {/* Upcoming Festivals This Month */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Star className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-xs font-bold text-slate-200">This Month's Events</span>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {calendarData
                ? Object.entries(calendarData.by_date)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .flatMap(([ds, events]) =>
                      events
                        .filter((e) => e.importance === 1)
                        .map((ev) => ({ ...ev, dateStr: ds }))
                    )
                    .slice(0, 10)
                    .map((ev) => (
                      <button
                        key={ev.id}
                        onClick={() => handleDayClick(ev.dateStr)}
                        className="w-full text-left flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800/50 transition-colors group"
                      >
                        <span className="text-base">{ev.emoji}</span>
                        <div className="min-w-0">
                          <p className="text-[11px] font-semibold text-slate-200 truncate">
                            {ev.title}
                          </p>
                          <p className="text-[10px] text-slate-500">
                            {new Date(ev.dateStr + "T00:00:00").toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                            })}
                          </p>
                        </div>
                      </button>
                    ))
                : Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="h-8 rounded-lg bg-slate-800/50 animate-pulse" />
                  ))}
              {calendarData &&
                Object.values(calendarData.by_date).flat().filter((e) => e.importance === 1)
                  .length === 0 && (
                  <p className="text-[11px] text-slate-500 italic py-2">
                    No major festivals this month.
                  </p>
                )}
            </div>
          </Card>

          {/* Google Calendar Card */}
          {!googleConnected && (
            <Card className="p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs font-bold text-slate-200">Google Calendar</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Connect your Google Calendar to see personal and org events alongside festivals.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="w-full text-xs"
                leftIcon={<Link2 className="w-3 h-3" />}
                onClick={handleConnectGoogle}
              >
                Connect Google Calendar
              </Button>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
