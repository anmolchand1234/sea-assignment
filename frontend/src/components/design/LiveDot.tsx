import React from 'react';

interface LiveDotProps {
  isLive: boolean;
  className?: string;
}

export const LiveDot: React.FC<LiveDotProps> = ({ isLive, className = '' }) => {
  if (isLive) {
    return (
      <span className={`inline-flex items-center gap-1.5 ${className}`} title="Live GPS position">
        <span
          className="w-2 h-2 rounded-full animate-live-pulse"
          style={{ backgroundColor: 'var(--go)' }}
          aria-hidden="true"
        />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--go)]">
          Live
        </span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`} title="Scheduled timetable">
      <span
        className="w-2 h-2 rounded-full border border-[var(--ink-soft)]"
        aria-hidden="true"
      />
      <span className="text-[11px] font-medium uppercase tracking-wider text-[var(--ink-soft)]">
        Sched
      </span>
    </span>
  );
};

