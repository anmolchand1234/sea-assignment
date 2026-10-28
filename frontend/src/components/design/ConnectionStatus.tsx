import React from 'react';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

export type ConnectionState = 'connected' | 'reconnecting' | 'polling' | 'disconnected';

interface ConnectionStatusProps {
  status: ConnectionState;
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ status, className = '' }) => {
  const configs: Record<
    ConnectionState,
    { label: string; icon: React.ReactNode; colorClass: string }
  > = {
    connected: {
      label: 'Live',
      icon: <span className="w-2 h-2 rounded-full bg-[var(--go)] animate-pulse" />,
      colorClass: 'text-[var(--go)] border-[var(--go)]/20 bg-[var(--go)]/10',
    },
    reconnecting: {
      label: 'Reconnecting',
      icon: <RefreshCw size={12} className="animate-spin text-[var(--caution)]" />,
      colorClass: 'text-[var(--caution)] border-[var(--caution)]/20 bg-[var(--caution)]/10',
    },
    polling: {
      label: 'Polling (10s)',
      icon: <Wifi size={12} className="text-[var(--info)]" />,
      colorClass: 'text-[var(--info)] border-[var(--info)]/20 bg-[var(--info)]/10',
    },
    disconnected: {
      label: 'Offline',
      icon: <WifiOff size={12} className="text-[var(--late)]" />,
      colorClass: 'text-[var(--late)] border-[var(--late)]/20 bg-[var(--late)]/10',
    },
  };

  const { label, icon, colorClass } = configs[status] || configs.connected;

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] border text-xs font-semibold select-none ${colorClass} ${className}`}
      title={`Telemetry status: ${label}`}
    >
      {icon}
      <span>{label}</span>
    </div>
  );
};

