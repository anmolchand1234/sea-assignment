import React, { useState } from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  keyExtractor: (item: T) => string | number;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
  className?: string;
}

export function DataTable<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  emptyMessage = 'No records found.',
  className = '',
}: DataTableProps<T>) {
  const [density, setDensity] = useState<'comfortable' | 'compact'>('compact');

  const paddingClasses = density === 'compact' ? 'py-2 px-3 text-xs' : 'py-3.5 px-4 text-sm';

  return (
    <div className={`w-full flex flex-col border border-[var(--rule)] rounded-[4px] overflow-hidden bg-[var(--surface)] ${className}`}>
      {/* Header toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-[var(--rule)] bg-[var(--paper)]">
        <span className="text-xs font-semibold text-[var(--ink-soft)] uppercase tracking-wider">
          {data.length} records
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setDensity('compact')}
            type="button"
            className={`px-2 py-0.5 text-[11px] font-medium rounded-[4px] cursor-pointer ${
              density === 'compact'
                ? 'bg-[var(--surface)] text-[var(--ink)] border border-[var(--rule)] shadow-xs'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            Compact
          </button>
          <button
            onClick={() => setDensity('comfortable')}
            type="button"
            className={`px-2 py-0.5 text-[11px] font-medium rounded-[4px] cursor-pointer ${
              density === 'comfortable'
                ? 'bg-[var(--surface)] text-[var(--ink)] border border-[var(--rule)] shadow-xs'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            Comfortable
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto w-full">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[var(--rule)] bg-[var(--paper)]">
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{ width: col.width }}
                  className={`py-2 px-3 text-[11px] font-bold text-[var(--ink-soft)] uppercase tracking-wider ${
                    col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                  }`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--rule)]">
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="py-8 text-center text-xs text-[var(--ink-soft)]">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((item) => (
                <tr
                  key={keyExtractor(item)}
                  onClick={() => onRowClick && onRowClick(item)}
                  className={`hover:bg-[var(--paper)]/50 transition-colors ${
                    onRowClick ? 'cursor-pointer' : ''
                  }`}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`${paddingClasses} text-[var(--ink)] ${
                        col.align === 'right'
                          ? 'text-right'
                          : col.align === 'center'
                          ? 'text-center'
                          : 'text-left'
                      }`}
                    >
                      {col.render ? col.render(item) : (item as any)[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

