import { useState } from 'react';
import { PassengerHome } from './features/passenger/PassengerHome';
import { DesignShowcase } from './features/design-system/DesignShowcase';
import { LayoutGrid, Bus } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'passenger' | 'design'>('passenger');

  return (
    <div>
      {/* Switcher Navigation */}
      <nav className="bg-[var(--surface)] border-b border-[var(--rule)] px-4 py-2 flex items-center justify-between text-xs font-semibold">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab('passenger')}
            className={`px-3 py-1 rounded-[4px] cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'passenger'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <Bus size={14} />
            <span>Passenger App (Live Board)</span>
          </button>
          <button
            onClick={() => setActiveTab('design')}
            className={`px-3 py-1 rounded-[4px] cursor-pointer flex items-center gap-1.5 ${
              activeTab === 'design'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <LayoutGrid size={14} />
            <span>Design System Primitives</span>
          </button>
        </div>
        <span className="text-[11px] font-mono text-[var(--ink-soft)]">
          Wayline v1.0
        </span>
      </nav>

      {/* Screen Render */}
      {activeTab === 'passenger' ? <PassengerHome /> : <DesignShowcase />}
    </div>
  );
}
