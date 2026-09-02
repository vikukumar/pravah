import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  glow?: boolean;
}

export function Card({ className, hoverEffect = false, glow = false, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "glass-panel rounded-2xl p-6 relative overflow-hidden",
        hoverEffect && "glass-panel-hover",
        glow && "border-indigo-500/30 shadow-lg shadow-indigo-500/10",
        className
      )}
      {...props}
    >
      {glow && (
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl rounded-full pointer-events-none" />
      )}
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex items-center justify-between pb-4 mb-4 border-b border-slate-800/60", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-lg font-semibold text-slate-100", className)} {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-xs text-slate-400 mt-1", className)} {...props}>
      {children}
    </p>
  );
}
