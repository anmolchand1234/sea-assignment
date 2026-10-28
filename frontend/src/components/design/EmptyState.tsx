import React from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-start justify-center p-8 rounded-[8px] border border-dashed border-[var(--rule)] bg-[var(--surface)] text-left ${className}`}
    >
      <h3 className="text-base font-bold text-[var(--ink)] tracking-tight mb-1">
        {title}
      </h3>
      <p className="text-sm text-[var(--ink-soft)] max-w-md leading-relaxed mb-4">
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          type="button"
          className="inline-flex items-center justify-center px-3.5 py-1.5 text-xs font-semibold rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] hover:opacity-95 transition-opacity cursor-pointer"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

