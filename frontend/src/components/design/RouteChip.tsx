import React from 'react';

interface RouteChipProps {
  code: string;
  color?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

function getContrastColor(hexColor?: string): string {
  if (!hexColor) return '#FFFFFF';
  const cleanHex = hexColor.replace('#', '');
  if (cleanHex.length !== 6) return '#FFFFFF';
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);
  // YIQ luminance formula
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 140 ? '#1C1B19' : '#FFFFFF';
}

export const RouteChip: React.FC<RouteChipProps> = ({
  code,
  color = '#2563EB',
  className = '',
  size = 'md',
}) => {
  const textColor = getContrastColor(color);
  
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5 font-bold',
    md: 'text-sm px-2 py-0.5 font-bold',
    lg: 'text-base px-2.5 py-1 font-bold',
  }[size];

  return (
    <span
      className={`inline-flex items-center justify-center rounded-[4px] tracking-wide select-none ${sizeClasses} ${className}`}
      style={{
        backgroundColor: color,
        color: textColor,
        fontFamily: 'var(--font-mono)',
      }}
      aria-label={`Route ${code}`}
    >
      {code}
    </span>
  );
};

