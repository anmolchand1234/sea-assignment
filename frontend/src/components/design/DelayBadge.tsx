import React from 'react';

interface DelayBadgeProps {
  delayMinutes: number;
  className?: string;
}

export const DelayBadge: React.FC<DelayBadgeProps> = ({ delayMinutes, className = '' }) => {
  if (delayMinutes <= 1) {
    return (
      <span
        className={`inline-flex items-center px-1.5 py-0.5 rounded-[4px] text-xs font-semibold text-[var(--go)] bg-[var(--go)]/10 border border-[var(--go)]/20 ${className}`}
      >
        On time
      </span>
    );
  }

  if (delayMinutes <= 5) {
    return (
      <span
        className={`inline-flex items-center px-1.5 py-0.5 rounded-[4px] text-xs font-semibold text-[var(--caution)] bg-[var(--caution)]/10 border border-[var(--caution)]/20 ${className}`}
      >
        +{delayMinutes}m delay
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-[4px] text-xs font-semibold text-[var(--late)] bg-[var(--late)]/10 border border-[var(--late)]/20 ${className}`}
    >
      +{delayMinutes}m late
    </span>
  );
};

