import React from 'react';
import { RouteChip } from './RouteChip';
import { LiveDot } from './LiveDot';
import { DelayBadge } from './DelayBadge';

export interface Departure {
  id: string;
  routeCode: string;
  routeColor: string;
  destination: string;
  minutesAway: number;
  isLive: boolean;
  delayMinutes?: number;
  platform?: string;
  isAccessible?: boolean;
}

interface DepartureRowProps {
  departure: Departure;
  onClick?: () => void;
  className?: string;
}

export const DepartureRow: React.FC<DepartureRowProps> = ({
  departure,
  onClick,
  className = '',
}) => {
  const isDue = departure.minutesAway <= 1;

  return (
    <div
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      className={`group flex items-center justify-between py-3.5 px-4 border-b border-[var(--rule)] hover:bg-[var(--surface)] transition-colors cursor-pointer select-none ${className}`}
    >
      {/* Left: Route and destination */}
      <div className="flex items-center gap-3.5 min-w-0">
        <RouteChip code={departure.routeCode} color={departure.routeColor} size="md" />
        <div className="flex flex-col min-w-0">
          <span className="font-semibold text-base text-[var(--ink)] truncate leading-snug">
            {departure.destination}
          </span>
          <div className="flex items-center gap-2 mt-0.5 text-xs text-[var(--ink-soft)]">
            <LiveDot isLive={departure.isLive} />
            {departure.delayMinutes !== undefined && departure.delayMinutes > 1 && (
              <>
                <span className="text-[var(--rule)]">•</span>
                <DelayBadge delayMinutes={departure.delayMinutes} />
              </>
            )}
            {departure.platform && (
              <>
                <span className="text-[var(--rule)]">•</span>
                <span>Bay {departure.platform}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Right: Big Minutes Numerals (Loudest element per Spec §6 & §9.3) */}
      <div className="flex items-baseline gap-1 text-right pl-3 flex-shrink-0">
        {isDue ? (
          <span
            className="text-2xl font-bold uppercase tracking-tight text-[var(--late)] animate-pulse"
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            Due
          </span>
        ) : (
          <>
            <span
              className="text-3xl font-extrabold text-[var(--ink)] tracking-tight tabular-nums"
              style={{ fontFamily: 'var(--font-mono)' }}
            >
              {departure.minutesAway}
            </span>
            <span className="text-xs font-semibold text-[var(--ink-soft)] uppercase tracking-wide">
              min
            </span>
          </>
        )}
      </div>
    </div>
  );
};

