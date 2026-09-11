import React from "react";
import { SeverityBand } from "../types";

interface ScoreBadgeProps {
  score: number;
  severity: SeverityBand;
  size?: "sm" | "md" | "lg";
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({
  score,
  severity,
  size = "md",
}) => {
  const configs: Record<
    SeverityBand,
    { bg: string; text: string; border: string; label: string; icon: string }
  > = {
    LOW: {
      bg: "bg-emerald-50",
      text: "text-emerald-800",
      border: "border-emerald-300",
      label: "LOW RISK",
      icon: "✓",
    },
    MODERATE: {
      bg: "bg-amber-50",
      text: "text-amber-800",
      border: "border-amber-300",
      label: "MODERATE RISK",
      icon: "▲",
    },
    HIGH: {
      bg: "bg-rose-50",
      text: "text-rose-800",
      border: "border-rose-400",
      label: "HIGH RISK",
      icon: "⚠",
    },
  };

  const current = configs[severity] || configs.LOW;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-sm",
    lg: "px-4 py-2 text-base font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-medium ${current.bg} ${current.text} ${current.border} ${sizeClasses[size]}`}
      data-testid="score-badge"
    >
      <span aria-hidden="true" className="font-bold">
        {current.icon}
      </span>
      <span>{current.label}</span>
      <span className="font-bold tabular-nums">({score}/100)</span>
    </span>
  );
};
