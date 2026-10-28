import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  width?: string;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  width = 'max-w-md',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-[1px] transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Container */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        className={`relative z-10 w-full ${width} bg-[var(--surface)] text-[var(--ink)] shadow-2xl flex flex-col border-l border-[var(--rule)] h-full overflow-hidden`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--rule)] flex-shrink-0">
          <div>
            <h2 id="drawer-title" className="text-base font-bold text-[var(--ink)]">
              {title}
            </h2>
            {subtitle && (
              <p className="text-xs text-[var(--ink-soft)] mt-0.5">{subtitle}</p>
            )}
          </div>
          <button
            onClick={onClose}
            type="button"
            className="p-1 rounded-[4px] hover:bg-[var(--paper)] text-[var(--ink-soft)] hover:text-[var(--ink)] transition-colors cursor-pointer"
            aria-label="Close drawer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">{children}</div>
      </div>
    </div>
  );
};

