"use client";

import React from "react";
import { Modal } from "./modal";
import { Button } from "./button";
import { AlertTriangle } from "lucide-react";

export interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary";
  isLoading?: boolean;
}

export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
}: ConfirmationDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} maxWidth="sm">
      <div className="text-center py-2 space-y-4">
        <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h3 className="text-base font-semibold text-slate-100">{title}</h3>
          <p className="text-xs text-slate-400">{message}</p>
        </div>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === "danger" ? "danger" : "primary"}
            size="sm"
            onClick={onConfirm}
            isLoading={isLoading}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
