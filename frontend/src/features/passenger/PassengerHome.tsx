import React, { useState, useEffect } from 'react';
import { DepartureRow, type Departure } from '../../components/design/DepartureRow';
import { RouteChip } from '../../components/design/RouteChip';
import { ConnectionStatus } from '../../components/design/ConnectionStatus';
import { AuthModal } from '../../components/auth/AuthModal';
import { ChangePasswordModal } from '../../components/auth/ChangePasswordModal';
import { useAuthStore } from '../../lib/authStore';
import {
  Search,
  MapPin,
  Bookmark,
  Bell,
  Bus,
  RefreshCw,
  LogIn,
  LogOut,
  KeyRound,
  Compass,
  ArrowRight,
} from 'lucide-react';
import { fetchApi } from '../../lib/api';

export const PassengerHome: React.FC = () => {
  const { user, logout } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<{ stops: any[]; routes: any[] }>({ stops: [], routes: [] });
  const [selectedStopId, setSelectedStopId] = useState<string>('S001');
  const [stopData, setStopData] = useState<any>(null);
  const [arrivals, setArrivals] = useState<Departure[]>([]);
  const [loading, setLoading] = useState(false);
  const [pinnedStops, setPinnedStops] = useState<string[]>(['S001', 'S003', 'S011']);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [changePwdOpen, setChangePwdOpen] = useState(false);

  // Trip planner states (P-4)
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [fromStop, setFromStop] = useState('S001');
  const [toStop, setToStop] = useState('S009');
  const [journeyResult, setJourneyResult] = useState<any>(null);
  const [planning, setPlanning] = useState(false);

  // Load stop arrivals
  const loadArrivals = async (stopId: string) => {
    try {
      setLoading(true);
      const data = await fetchApi(`/public/stops/${stopId}/arrivals?limit=8`);
      setStopData(data.stop);
      const formatted: Departure[] = (data.arrivals || []).map((a: any) => ({
        id: a.id,
        routeCode: a.route_code,
        routeColor: a.route_color,
        destination: a.destination,
        minutesAway: a.minutes_away,
        isLive: a.is_live,
        delayMinutes: a.delay_minutes,
        platform: '1',
      }));
      setArrivals(formatted);
    } catch (err) {
      console.error('Failed to load arrivals', err);
    } finally {
      setLoading(false);
    }
  };

  // Search handler
  useEffect(() => {
    if (searchQuery.trim().length > 1) {
      fetchApi(`/public/search?q=${encodeURIComponent(searchQuery)}`)
        .then(setSearchResults)
        .catch(console.error);
    } else {
      setSearchResults({ stops: [], routes: [] });
    }
  }, [searchQuery]);

  // Load initial data
  useEffect(() => {
    loadArrivals(selectedStopId);
    fetchApi('/public/alerts').then(setAlerts).catch(console.error);

    const interval = setInterval(() => {
      loadArrivals(selectedStopId);
    }, 12000);
    return () => clearInterval(interval);
  }, [selectedStopId]);

  const togglePin = (code: string) => {
    setPinnedStops((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const handlePlanJourney = async () => {
    setPlanning(true);
    try {
      const res = await fetchApi(`/public/plan?from=${fromStop}&to=${toStop}`);
      setJourneyResult(res);
    } catch (err: any) {
      alert(`Trip plan error: ${err.message}`);
    } finally {
      setPlanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]">
      {/* Top Municipal Banner */}
      <header className="border-b border-[var(--rule)] bg-[var(--surface)] px-4 py-3 sticky top-0 z-30 shadow-xs">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] flex items-center justify-center font-extrabold text-lg">
              W
            </div>
            <div>
              <h1 className="text-base font-extrabold tracking-tight uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                Wayline Passenger
              </h1>
              <p className="text-[10px] text-[var(--ink-soft)] uppercase tracking-wider font-semibold">
                Prayagraj Municipal City Bus • Live Board
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ConnectionStatus status="connected" />
            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-[var(--rule)]">
                <span className="text-xs font-bold text-[var(--ink)] hidden sm:inline">
                  {user.name}
                </span>
                <button
                  onClick={() => setChangePwdOpen(true)}
                  title="Change Password"
                  className="p-1.5 rounded border border-[var(--rule)] text-[var(--ink-soft)] hover:text-[var(--ink)] cursor-pointer"
                >
                  <KeyRound size={13} />
                </button>
                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-1.5 rounded border border-[var(--late)]/30 text-[var(--late)] hover:bg-[var(--late)]/10 cursor-pointer"
                >
                  <LogOut size={13} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setAuthModalOpen(true)}
                className="px-3 py-1.5 rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] text-xs font-bold flex items-center gap-1.5 cursor-pointer hover:opacity-90"
              >
                <LogIn size={13} />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-5 space-y-6">
        {/* Service Alerts Banner */}
        {alerts.length > 0 && (
          <div className="p-3 bg-[var(--signal)]/15 border-l-4 border-[var(--signal)] rounded-r-[4px] text-xs">
            <div className="flex items-center gap-2 font-bold text-[var(--signal-ink)] mb-0.5">
              <Bell size={14} />
              <span>{alerts[0].title}</span>
            </div>
            <p className="text-[var(--ink)]">{alerts[0].body}</p>
          </div>
        )}

        {/* Action Bar: Planner Toggle & Quick Info */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
            Find Next Bus or Plan Route
          </span>
          <button
            onClick={() => setPlannerOpen(!plannerOpen)}
            className="text-xs font-bold text-[var(--signal-ink)] bg-[var(--signal)]/20 px-2.5 py-1 rounded-[4px] flex items-center gap-1 cursor-pointer hover:bg-[var(--signal)]/30"
          >
            <Compass size={13} />
            <span>{plannerOpen ? 'Close Trip Planner' : 'Trip Planner (A → B)'}</span>
          </button>
        </div>

        {/* Trip Planner Drawer/Box (Spec §5.1 P-4) */}
        {plannerOpen && (
          <div className="p-4 rounded-[6px] border-2 border-[var(--signal)] bg-[var(--surface)] space-y-3 text-xs">
            <h3 className="font-bold uppercase tracking-wider text-[var(--ink)] flex items-center gap-1.5">
              <Compass size={15} className="text-[var(--signal)]" />
              <span>Journey Planner (A to B)</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                  From Stop
                </label>
                <select
                  value={fromStop}
                  onChange={(e) => setFromStop(e.target.value)}
                  className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] text-xs font-semibold"
                >
                  <option value="S001">S001 - Civil Lines Terminal</option>
                  <option value="S003">S003 - Prayagraj Junction</option>
                  <option value="S011">S011 - IIIT Allahabad (Jhalwa)</option>
                  <option value="S013">S013 - Naini Railway Station</option>
                  <option value="S018">S018 - Bamrauli Airport Gate</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                  To Stop
                </label>
                <select
                  value={toStop}
                  onChange={(e) => setToStop(e.target.value)}
                  className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] text-xs font-semibold"
                >
                  <option value="S009">S009 - Sangam Ghat Terminal</option>
                  <option value="S006">S006 - Katra Market</option>
                  <option value="S021">S021 - MNNIT Allahabad Gate</option>
                  <option value="S007">S007 - University of Allahabad</option>
                  <option value="S015">S015 - Jhunsi Bus Stand</option>
                </select>
              </div>
            </div>

            <button
              onClick={handlePlanJourney}
              disabled={planning}
              className="w-full py-2 bg-[var(--signal)] text-[var(--signal-ink)] font-bold rounded cursor-pointer hover:opacity-90"
            >
              {planning ? 'Calculating Best Routes...' : 'Find Fastest Bus Route'}
            </button>

            {/* Planner Results */}
            {journeyResult && (
              <div className="pt-2 space-y-2 border-t border-[var(--rule)]">
                <span className="font-bold uppercase tracking-wider text-[10px] text-[var(--ink-soft)]">
                  Available Route Options:
                </span>
                {journeyResult.plans.length === 0 ? (
                  <p className="text-[var(--ink-soft)]">No direct or 1-transfer transit path found.</p>
                ) : (
                  journeyResult.plans.map((p: any, idx: number) => (
                    <div key={idx} className="p-3 bg-[var(--paper)] rounded border border-[var(--rule)] flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-[var(--ink)]">{p.total_minutes} mins</span>
                          <span className="text-[10px] uppercase font-bold text-[var(--go)]">
                            {p.transfers === 0 ? 'Direct Route' : '1 Transfer'}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-[var(--ink-soft)]">
                          {p.legs.map((leg: any, lIdx: number) => (
                            <React.Fragment key={lIdx}>
                              {leg.type === 'ride' ? (
                                <RouteChip code={leg.route_short_name || 'BUS'} size="sm" />
                              ) : (
                                <span className="text-[10px] italic">transfer</span>
                              )}
                              {lIdx < p.legs.length - 1 && <ArrowRight size={10} />}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}

        {/* 1. Large Search Bar (Spec §8.2) */}
        <div className="relative">
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-[4px] border-2 border-[var(--rule)] bg-[var(--surface)] focus-within:border-[var(--signal)] transition-colors">
            <Search size={18} className="text-[var(--ink-soft)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search stop name, code (e.g. S001), or route..."
              className="w-full bg-transparent text-sm font-medium outline-hidden placeholder:text-[var(--ink-soft)]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="text-xs text-[var(--ink-soft)] font-bold px-1.5 py-0.5 rounded hover:bg-[var(--rule)]"
              >
                Clear
              </button>
            )}
          </div>

          {/* Autocomplete dropdown */}
          {(searchResults.stops.length > 0 || searchResults.routes.length > 0) && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--surface)] border border-[var(--rule)] rounded-[4px] shadow-lg z-40 max-h-72 overflow-y-auto divide-y divide-[var(--rule)]">
              {searchResults.stops.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setSelectedStopId(s.code);
                    setSearchQuery('');
                  }}
                  className="w-full text-left p-3 hover:bg-[var(--paper)] flex items-center justify-between text-xs cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <MapPin size={14} className="text-[var(--signal)]" />
                    <span className="font-bold text-[var(--ink)]">{s.name}</span>
                  </div>
                  <span className="font-mono text-[var(--ink-soft)]">{s.code}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 2. Pinned Stops Quick Bar */}
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
              Saved Places
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {pinnedStops.map((code) => (
              <button
                key={code}
                onClick={() => setSelectedStopId(code)}
                className={`px-3 py-1.5 rounded-[4px] border text-xs font-semibold cursor-pointer transition-colors flex items-center gap-1.5 ${
                  selectedStopId === code
                    ? 'border-[var(--signal)] bg-[var(--signal)]/10 text-[var(--signal-ink)] font-bold'
                    : 'border-[var(--rule)] bg-[var(--surface)] text-[var(--ink-soft)] hover:text-[var(--ink)]'
                }`}
              >
                <Bookmark size={12} className={selectedStopId === code ? 'fill-current' : ''} />
                <span>Stop {code}</span>
              </button>
            ))}
          </div>
        </section>

        {/* 3. Stop Departure Board (Signature Screen - Spec §8.2) */}
        <section className="space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--rule)] pb-2">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-extrabold text-[var(--ink)] tracking-tight">
                  {stopData?.name || 'Loading Stop...'}
                </h2>
                <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-[var(--paper)] border border-[var(--rule)] text-[var(--ink-soft)]">
                  {stopData?.code || selectedStopId}
                </span>
              </div>
              <p className="text-xs text-[var(--ink-soft)] mt-0.5">
                {stopData?.is_accessible ? 'Wheelchair accessible • ' : ''}
                {stopData?.has_shelter ? 'Sheltered' : 'Street stop'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => loadArrivals(selectedStopId)}
                title="Refresh departures"
                className="p-1.5 rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] hover:bg-[var(--paper)] text-[var(--ink-soft)] cursor-pointer"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              </button>
              <button
                onClick={() => togglePin(selectedStopId)}
                className={`px-2.5 py-1.5 rounded-[4px] border text-xs font-bold cursor-pointer flex items-center gap-1 ${
                  pinnedStops.includes(selectedStopId)
                    ? 'border-[var(--signal)] bg-[var(--signal)] text-[var(--signal-ink)]'
                    : 'border-[var(--rule)] bg-[var(--surface)] text-[var(--ink-soft)]'
                }`}
              >
                <Bookmark size={12} className={pinnedStops.includes(selectedStopId) ? 'fill-current' : ''} />
                <span>{pinnedStops.includes(selectedStopId) ? 'Pinned' : 'Pin'}</span>
              </button>
            </div>
          </div>

          {/* Departure List */}
          <div
            role="region"
            aria-live="polite"
            className="rounded-[8px] border border-[var(--rule)] bg-[var(--surface)] overflow-hidden shadow-xs divide-y divide-[var(--rule)]"
          >
            {arrivals.length === 0 ? (
              <div className="p-8 text-center text-xs text-[var(--ink-soft)]">
                {loading ? 'Fetching upcoming buses...' : 'No upcoming departures scheduled for this stop.'}
              </div>
            ) : (
              arrivals.map((dep) => (
                <DepartureRow
                  key={dep.id}
                  departure={dep}
                  onClick={() => alert(`Showing tracking for route ${dep.routeCode}`)}
                />
              ))
            )}
          </div>
        </section>

        {/* 4. Active Transit Routes in City */}
        <section className="space-y-3 pt-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
            Network Trunk & Express Routes
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {[
              { code: '7A', name: 'Sangam Express', color: '#2563EB' },
              { code: '14', name: 'IIIT - Civil Lines', color: '#DC2626' },
              { code: '21E', name: 'Naini - Teliyarganj', color: '#059669' },
              { code: '5B', name: 'Jhunsi Feeder', color: '#7C3AED' },
              { code: 'AIR-1', name: 'Airport Express', color: '#D97706' },
              { code: 'N1', name: 'Night Owl Circular', color: '#1F2937' },
            ].map((r) => (
              <div
                key={r.code}
                className="p-3 rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <RouteChip code={r.code} color={r.color} size="sm" />
                  <span className="text-xs font-bold truncate max-w-[90px]">{r.name}</span>
                </div>
                <Bus size={14} className="text-[var(--ink-soft)]" />
              </div>
            ))}
          </div>
        </section>
      </main>

      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
      <ChangePasswordModal isOpen={changePwdOpen} onClose={() => setChangePwdOpen(false)} />
    </div>
  );
};
