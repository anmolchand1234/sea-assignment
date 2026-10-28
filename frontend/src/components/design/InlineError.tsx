import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface InlineErrorProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const InlineError: React.FC<InlineErrorProps> = ({ message, onRetry, className = '' }) => {
  return (
    <div
      role="alert"
      className={`flex items-center justify-between p-3.5 rounded-[4px] border border-[var(--late)]/30 bg-[var(--late)]/10 text-[var(--late)] text-sm ${className}`}
    >
      <div className="flex items-center gap-2.5">
        <AlertCircle size={18} className="flex-shrink-0" />
        <span className="font-medium">{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          type="button"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-[4px] bg-[var(--late)] text-white hover:opacity-90 transition-opacity cursor-pointer"
        >
          <RefreshCw size={13} />
          Retry
        </button>
      )}
    </div>
  );
};

