import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "glow";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer active:scale-[0.98]";

    const variantStyles = {
      primary:
        "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25 border border-indigo-500/30",
      glow:
        "bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 text-white font-semibold shadow-lg shadow-indigo-500/30 hover:opacity-95 hover:shadow-indigo-500/50",
      secondary:
        "bg-slate-800/80 hover:bg-slate-700/80 text-slate-100 border border-slate-700/60 backdrop-blur-md",
      outline:
        "bg-transparent border border-slate-700/80 hover:border-slate-600 hover:bg-slate-800/40 text-slate-200",
      ghost:
        "bg-transparent hover:bg-slate-800/60 text-slate-300 hover:text-slate-100",
      danger:
        "bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-600/20 border border-rose-500/30",
    };

    const sizeStyles = {
      sm: "text-xs px-3 py-1.5 gap-1.5 h-8",
      md: "text-sm px-4 py-2 gap-2 h-10",
      lg: "text-base px-6 py-3 gap-2.5 h-12",
      icon: "h-10 w-10 p-0 justify-center",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
        {!isLoading && leftIcon}
        {children}
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = "Button";
