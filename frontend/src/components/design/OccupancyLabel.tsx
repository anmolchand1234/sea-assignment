import React from 'react';

export type OccupancyLevel = 'empty' | 'seats' | 'standing' | 'full';

interface OccupancyLabelProps {
  level: OccupancyLevel;
  className?: string;
}

export const OccupancyLabel: React.FC<OccupancyLabelProps> = ({ level, className = '' }) => {
  const configs: Record<OccupancyLevel, { label: string; textClass: string }> = {
    empty: { label: 'Many seats', textClass: 'text-[var(--go)]' },
    seats: { label: 'Seats available', textClass: 'text-[var(--ink-soft)]' },
    standing: { label: 'Standing room only', textClass: 'text-[var(--caution)]' },
    full: { label: 'Bus full', textClass: 'text-[var(--late)]' },
  };

  const { label, textClass } = configs[level] || configs.seats;

  return (
    <span className={`text-xs font-medium tracking-tight ${textClass} ${className}`}>
      {label}
    </span>
  );
};

