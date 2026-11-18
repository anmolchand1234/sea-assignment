import { useEffect, useState } from 'react';
import { PassengerHome } from './features/passenger/PassengerHome';
import { UserDashboard } from './features/dispatcher/UserDashboard';
import { DriverPortal } from './features/driver/DriverPortal';
import { AdminConsole } from './features/admin/AdminConsole';
import { DesignShowcase } from './features/design-system/DesignShowcase';
import { useAuthStore } from './lib/authStore';
import { LayoutGrid, Bus, Shield, UserCheck, Settings } from 'lucide-react';

export default function App() {
  const { user, initFromStorage } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'passenger' | 'ops' | 'driver' | 'admin' | 'design'>('passenger');

  useEffect(() => {
    initFromStorage();
  }, [initFromStorage]);

  // Role-based auto navigation upon sign in; redirect to passenger on sign out
  useEffect(() => {
    if (user) {
      if (user.role === 'dispatcher') setActiveTab('ops');
      else if (user.role === 'admin') setActiveTab('admin');
      else if (user.role === 'driver') setActiveTab('driver');
      else if (user.role === 'passenger') setActiveTab('passenger');
    } else {
      // Signed out — always fall back to the public passenger portal
      setActiveTab('passenger');
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
            <span>Passenger Portal</span>
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
            <span>Dispatcher Console</span>
          </button>

          <button
            onClick={() => setActiveTab('driver')}
            className={`px-3 py-1.5 rounded-[4px] cursor-pointer flex items-center gap-1.5 transition-colors ${
              activeTab === 'driver'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <UserCheck size={14} />
            <span>Driver Portal</span>
          </button>

          <button
            onClick={() => setActiveTab('admin')}
            className={`px-3 py-1.5 rounded-[4px] cursor-pointer flex items-center gap-1.5 transition-colors ${
              activeTab === 'admin'
                ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            <Settings size={14} />
            <span>Admin Console</span>
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
            <span>Design System</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {user ? (
            <span className="text-[11px] text-[var(--ink-soft)] font-mono">
              Signed in: <strong className="text-[var(--ink)]">{user.name}</strong> ({user.role})
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
      {activeTab === 'driver' && <DriverPortal />}
      {activeTab === 'admin' && <AdminConsole />}
      {activeTab === 'design' && <DesignShowcase />}
    </div>
  );
}
