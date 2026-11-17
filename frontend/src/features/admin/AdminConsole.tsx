import React, { useState, useEffect } from 'react';
import { fetchApi } from '../../lib/api';
import { useAuthStore } from '../../lib/authStore';
import { RouteChip } from '../../components/design/RouteChip';
import { TransitMap } from '../../components/design/TransitMap';
import { ChangePasswordModal } from '../../components/auth/ChangePasswordModal';
import {
  Settings,
  Plus,
  MapPin,
  Bus,
  Users,
  Route as RouteIcon,
  Check,
  KeyRound,
  LogOut,
} from 'lucide-react';

export const AdminConsole: React.FC = () => {
  const { logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'stops' | 'routes' | 'vehicles' | 'drivers'>('stops');
  const [stops, setStops] = useState<any[]>([]);
  const [routes, setRoutes] = useState<any[]>([]);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [drivers, setDrivers] = useState<any[]>([]);
  const [changePwdOpen, setChangePwdOpen] = useState(false);

  // New Stop form (A-1)
  const [newStopCode, setNewStopCode] = useState('');
  const [newStopName, setNewStopName] = useState('');
  const [newStopLat, setNewStopLat] = useState('25.4450');
  const [newStopLng, setNewStopLng] = useState('81.8400');
  const [newStopAccessible, setNewStopAccessible] = useState(true);
  const [formSuccess, setFormSuccess] = useState('');

  const loadAll = async () => {
    try {
      const [sRes, rRes, vRes, dRes] = await Promise.all([
        fetchApi('/stops?page_size=50'),
        fetchApi('/routes?page_size=50'),
        fetchApi('/vehicles?page_size=50'),
        fetchApi('/drivers?page_size=50'),
      ]);
      setStops(sRes.items || []);
      setRoutes(rRes.items || []);
      setVehicles(vRes.items || []);
      setDrivers(dRes.items || []);
    } catch (e) {
      console.error('Failed to load admin data:', e);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleCreateStop = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchApi('/stops', {
        method: 'POST',
        body: JSON.stringify({
          code: newStopCode,
          name: newStopName,
          lat: parseFloat(newStopLat),
          lng: parseFloat(newStopLng),
          is_accessible: newStopAccessible,
          has_shelter: true,
        }),
      });
      setFormSuccess('Stop created successfully!');
      setNewStopCode('');
      setNewStopName('');
      loadAll();
      setTimeout(() => setFormSuccess(''), 2000);
    } catch (err: any) {
      alert(`Error creating stop: ${err.message}`);
    }
  };

  const handleDeleteStop = async (id: string) => {
    if (!confirm('Are you sure you want to delete this stop?')) return;
    try {
      await fetchApi(`/stops/${id}`, { method: 'DELETE' });
      loadAll();
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };
  void handleDeleteStop;

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]">
      {/* Admin Header */}
      <header className="border-b border-[var(--rule)] bg-[var(--surface)] px-5 py-3 sticky top-0 z-30 shadow-xs">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-[4px] bg-[var(--ink)] text-[var(--paper)] flex items-center justify-center font-bold">
              <Settings size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-extrabold uppercase tracking-tight" style={{ fontFamily: 'var(--font-mono)' }}>
                  Wayline Transit Administration
                </h1>
                <span className="text-[10px] px-1.5 py-0.2 rounded font-bold uppercase bg-[var(--signal)] text-[var(--signal-ink)]">
                  Admin
                </span>
              </div>
              <p className="text-[11px] text-[var(--ink-soft)]">
                Network topology, fleet management, and system master CRUD (Spec §5.4 A-1)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setChangePwdOpen(true)}
              className="p-1.5 rounded border border-[var(--rule)] text-[var(--ink-soft)] hover:text-[var(--ink)] cursor-pointer"
            >
              <KeyRound size={14} />
            </button>
            <button
              onClick={logout}
              className="p-1.5 rounded border border-[var(--late)]/30 text-[var(--late)] cursor-pointer"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-5 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-[var(--rule)] pb-2 text-xs font-semibold">
          {[
            { id: 'stops', label: `Stops (${stops.length})`, icon: MapPin },
            { id: 'routes', label: `Routes (${routes.length})`, icon: RouteIcon },
            { id: 'vehicles', label: `Fleet (${vehicles.length})`, icon: Bus },
            { id: 'drivers', label: `Drivers (${drivers.length})`, icon: Users },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-[4px] flex items-center gap-1.5 cursor-pointer ${
                  activeTab === tab.id
                    ? 'bg-[var(--signal)] text-[var(--signal-ink)] font-bold'
                    : 'text-[var(--ink-soft)] hover:text-[var(--ink)]'
                }`}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* 1. Stops Management + Route Editor Map (A-1, A-2) */}
        {activeTab === 'stops' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Left: Interactive map showing all stops */}
            <div className="lg:col-span-2 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
                  Network Stop Topology Map (A-2)
                </h3>
                <span className="text-[11px] text-[var(--ink-soft)]">Click stops to inspect coordinates</span>
              </div>
              <TransitMap
                vehicles={[]}
                stops={stops}
                className="h-[440px] w-full"
              />
            </div>

            {/* Right: Quick Add Stop Form */}
            <div className="p-4 rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] space-y-4 text-xs h-fit">
              <div className="flex items-center gap-1.5">
                <Plus size={16} className="text-[var(--signal)]" />
                <h3 className="font-bold text-[var(--ink)]">Add New Bus Stop</h3>
              </div>

              {formSuccess && (
                <div className="p-2.5 rounded bg-[var(--go)]/10 text-[var(--go)] font-semibold flex items-center gap-1.5">
                  <Check size={14} />
                  <span>{formSuccess}</span>
                </div>
              )}

              <form onSubmit={handleCreateStop} className="space-y-3">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                    Stop Code (Unique)
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. S029"
                    value={newStopCode}
                    onChange={(e) => setNewStopCode(e.target.value)}
                    className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] font-mono"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                    Stop Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Anand Bhawan Museum"
                    value={newStopName}
                    onChange={(e) => setNewStopName(e.target.value)}
                    className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] font-semibold"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                      Latitude
                    </label>
                    <input
                      type="text"
                      required
                      value={newStopLat}
                      onChange={(e) => setNewStopLat(e.target.value)}
                      className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] font-mono text-[11px]"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                      Longitude
                    </label>
                    <input
                      type="text"
                      required
                      value={newStopLng}
                      onChange={(e) => setNewStopLng(e.target.value)}
                      className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] font-mono text-[11px]"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="acc-check"
                    checked={newStopAccessible}
                    onChange={(e) => setNewStopAccessible(e.target.checked)}
                  />
                  <label htmlFor="acc-check" className="text-xs text-[var(--ink-soft)] cursor-pointer">
                    Wheelchair Accessible Stop
                  </label>
                </div>

                <button
                  type="submit"
                  className="w-full py-2 bg-[var(--signal)] text-[var(--signal-ink)] font-bold rounded cursor-pointer hover:opacity-90"
                >
                  Create Stop
                </button>
              </form>
            </div>
          </div>
        )}

        {/* 2. Routes Management (A-1) */}
        {activeTab === 'routes' && (
          <div className="rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] overflow-hidden">
            <div className="p-3 border-b border-[var(--rule)] bg-[var(--paper)] flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ink)]">
                Network Transit Routes ({routes.length})
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--paper)]/50 text-[var(--ink-soft)] font-bold uppercase text-[10px] border-b border-[var(--rule)]">
                  <tr>
                    <th className="py-2.5 px-3">Route Code</th>
                    <th className="py-2.5 px-3">Full Route Title</th>
                    <th className="py-2.5 px-3">Service Type</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--rule)]">
                  {routes.map((r) => (
                    <tr key={r.id} className="hover:bg-[var(--paper)]/40">
                      <td className="py-2.5 px-3">
                        <RouteChip code={r.short_name} color={r.color_hex} size="sm" />
                      </td>
                      <td className="py-2.5 px-3 font-semibold text-[var(--ink)]">{r.long_name}</td>
                      <td className="py-2.5 px-3 capitalize text-[var(--ink-soft)]">{r.route_type}</td>
                      <td className="py-2.5 px-3 text-[var(--go)] font-bold">Active</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 3. Fleet & Vehicles (A-1) */}
        {activeTab === 'vehicles' && (
          <div className="rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] overflow-hidden">
            <div className="p-3 border-b border-[var(--rule)] bg-[var(--paper)]">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ink)]">
                Municipal Fleet Asset Registry ({vehicles.length})
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--paper)]/50 text-[var(--ink-soft)] font-bold uppercase text-[10px] border-b border-[var(--rule)]">
                  <tr>
                    <th className="py-2.5 px-3">Fleet No</th>
                    <th className="py-2.5 px-3">Registration Plate</th>
                    <th className="py-2.5 px-3">Bus Type</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Depot Allocation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--rule)]">
                  {vehicles.map((v) => (
                    <tr key={v.id} className="hover:bg-[var(--paper)]/40">
                      <td className="py-2.5 px-3 font-mono font-bold">{v.fleet_no}</td>
                      <td className="py-2.5 px-3 font-mono text-[var(--ink-soft)]">{v.plate}</td>
                      <td className="py-2.5 px-3 capitalize">{v.type}</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          v.status === 'active' ? 'bg-[var(--go)]/10 text-[var(--go)]' : 'bg-[var(--late)]/10 text-[var(--late)]'
                        }`}>
                          {v.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-[var(--ink-soft)]">{v.depot}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 4. Drivers (A-1, A-4) */}
        {activeTab === 'drivers' && (
          <div className="rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] overflow-hidden">
            <div className="p-3 border-b border-[var(--rule)] bg-[var(--paper)]">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ink)]">
                Certified Transport Operators ({drivers.length})
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[var(--paper)]/50 text-[var(--ink-soft)] font-bold uppercase text-[10px] border-b border-[var(--rule)]">
                  <tr>
                    <th className="py-2.5 px-3">Driver Name</th>
                    <th className="py-2.5 px-3">License Number</th>
                    <th className="py-2.5 px-3">Phone</th>
                    <th className="py-2.5 px-3">Max Duty Hours</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--rule)]">
                  {drivers.map((d) => (
                    <tr key={d.id} className="hover:bg-[var(--paper)]/40">
                      <td className="py-2.5 px-3 font-bold text-[var(--ink)]">{d.name}</td>
                      <td className="py-2.5 px-3 font-mono text-[var(--ink-soft)]">{d.license_no}</td>
                      <td className="py-2.5 px-3 text-[var(--ink-soft)]">{d.phone}</td>
                      <td className="py-2.5 px-3 font-mono">{d.max_duty_minutes / 60} hrs</td>
                      <td className="py-2.5 px-3 text-[var(--go)] font-bold">Active</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      <ChangePasswordModal isOpen={changePwdOpen} onClose={() => setChangePwdOpen(false)} />
    </div>
  );
};
