import { useEffect, useState } from 'react';
import { PassengerHome } from './features/passenger/PassengerHome';
import { UserDashboard } from './features/dispatcher/UserDashboard';
import { DesignShowcase } from './features/design-system/DesignShowcase';
import { useAuthStore } from './lib/authStore';
import { LayoutGrid, Bus, Shield } from 'lucide-react';

export default function App() {
  const { user, initFromStorage } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'passenger' | 'ops' | 'design'>('passenger');

  useEffect(() => {
    initFromStorage();
  }, [initFromStorage]);

  // If user signs in as dispatcher or admin, automatically default view to Ops Console
  useEffect(() => {
    if (user && (user.role === 'dispatcher' || user.role === 'admin')) {
      setActiveTab('ops');
    }
  }, [user]);

  return (
    <div>
      {/* Top Universal App Mode Switcher */}
      <nav className="bg-[var(--surface)] border-b border-[var(--rule)] px-4 py-2 flex items-center justify-between text-xs font-semibold">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setActiveTab('passenger')}
            className={`px-3 py-1.5 rounded-[4px] cursor-pointer flex items-center gap-1.5 transition-colors ${
              activeTab === 'passenger'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <Bus size={14} />
            <span>Passenger Portal (Live Board)</span>
          </button>

          <button
            onClick={() => setActiveTab('ops')}
            className={`px-3 py-1.5 rounded-[4px] cursor-pointer flex items-center gap-1.5 transition-colors ${
              activeTab === 'ops'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <Shield size={14} />
            <span>User / Dispatcher Console</span>
            {user && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-black/10">
                {user.role}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('design')}
            className={`px-3 py-1.5 rounded-[4px] cursor-pointer flex items-center gap-1.5 transition-colors ${
              activeTab === 'design'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <LayoutGrid size={14} />
            <span>Design System Primitives</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {user ? (
            <span className="text-[11px] text-[var(--ink-soft)] font-mono">
              Signed in: <strong className="text-[var(--ink)]">{user.name}</strong>
            </span>
          ) : (
            <span className="text-[11px] text-[var(--ink-soft)] font-mono">
              Guest Mode
            </span>
          )}
        </div>
      </nav>

      {/* Screen Render */}
      {activeTab === 'passenger' && <PassengerHome />}
      {activeTab === 'ops' && <UserDashboard />}
      {activeTab === 'design' && <DesignShowcase />}
    </div>
  );
}
