"use client";

import React, { createContext, useContext, useState } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  title: string;
  message?: string;
  type: ToastType;
}

interface ToastContextType {
  toast: (options: { title: string; message?: string; type?: ToastType }) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (options: { title: string; message?: string; type?: ToastType }) => {
    const id = Math.random().toString(36).substring(2, 9);
    const newToast: Toast = {
      id,
      title: options.title,
      message: options.message,
      type: options.type || "info",
    };
    setToasts((prev) => [...prev, newToast]);

    setTimeout(() => {
      removeToast(id);
    }, 4000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const toastMethods = {
    toast: addToast,
    success: (title: string, message?: string) => addToast({ title, message, type: "success" }),
    error: (title: string, message?: string) => addToast({ title, message, type: "error" }),
    info: (title: string, message?: string) => addToast({ title, message, type: "info" }),
  };

  return (
    <ToastContext.Provider value={toastMethods}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto p-4 rounded-xl shadow-2xl border flex items-start gap-3 backdrop-blur-xl animate-in slide-in-from-bottom-5 duration-200",
              t.type === "success" && "bg-slate-900/90 border-emerald-500/30 text-emerald-300",
              t.type === "error" && "bg-slate-900/90 border-rose-500/30 text-rose-300",
              t.type === "info" && "bg-slate-900/90 border-indigo-500/30 text-indigo-300"
            )}
          >
            {t.type === "success" && <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />}
            {t.type === "error" && <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />}
            {t.type === "info" && <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />}

            <div className="flex-1 text-xs">
              <h4 className="font-semibold text-slate-100">{t.title}</h4>
              {t.message && <p className="text-slate-400 mt-0.5">{t.message}</p>}
            </div>

            <button
              onClick={() => removeToast(t.id)}
              className="text-slate-400 hover:text-slate-200 p-1 rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
