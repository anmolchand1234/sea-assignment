import React, { useState } from 'react';
import { RouteChip } from '../../components/design/RouteChip';
import { LiveDot } from '../../components/design/LiveDot';
import { DelayBadge } from '../../components/design/DelayBadge';
import { OccupancyLabel } from '../../components/design/OccupancyLabel';
import { DepartureRow, type Departure } from '../../components/design/DepartureRow';
import { ConnectionStatus } from '../../components/design/ConnectionStatus';
import { EmptyState } from '../../components/design/EmptyState';
import { InlineError } from '../../components/design/InlineError';
import { Drawer } from '../../components/design/Drawer';
import { DataTable, type Column } from '../../components/design/DataTable';
import { Moon, Sun } from 'lucide-react';

export const DesignShowcase: React.FC = () => {
  const [isDark, setIsDark] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const sampleDepartures: Departure[] = [
    {
      id: '1',
      routeCode: '7A',
      routeColor: '#2563EB',
      destination: 'Civil Lines via Subedarganj',
      minutesAway: 2,
      isLive: true,
      delayMinutes: 0,
      platform: '1',
    },
    {
      id: '2',
      routeCode: '14',
      routeColor: '#DC2626',
      destination: 'IIIT Jhalwa Campus',
      minutesAway: 0, // due
      isLive: true,
      delayMinutes: 4,
      platform: '3',
    },
    {
      id: '3',
      routeCode: '21E',
      routeColor: '#059669',
      destination: 'Naini Railway Station Express',
      minutesAway: 12,
      isLive: false,
      platform: '2',
    },
    {
      id: '4',
      routeCode: '5B',
      routeColor: '#7C3AED',
      destination: 'Sangam Ghat Circular',
      minutesAway: 28,
      isLive: false,
      delayMinutes: 8,
      platform: '4',
    },
  ];

  interface VehicleRow {
    fleetNo: string;
    route: string;
    routeColor: string;
    driver: string;
    delay: number;
    status: string;
  }

  const sampleFleet: VehicleRow[] = [
    { fleetNo: 'BUS-101', route: '7A', routeColor: '#2563EB', driver: 'Rajesh Kumar', delay: 1, status: 'On Route' },
    { fleetNo: 'BUS-104', route: '14', routeColor: '#DC2626', driver: 'Amit Sharma', delay: 5, status: 'In Transit' },
    { fleetNo: 'BUS-109', route: '21E', routeColor: '#059669', driver: 'Pooja Verma', delay: 0, status: 'At Terminal' },
    { fleetNo: 'BUS-112', route: '5B', routeColor: '#7C3AED', driver: 'Sunil Yadav', delay: 12, status: 'Delayed' },
  ];

  const fleetColumns: Column<VehicleRow>[] = [
    { key: 'fleetNo', header: 'Vehicle', width: '120px' },
    {
      key: 'route',
      header: 'Route',
      width: '100px',
      render: (v) => <RouteChip code={v.route} color={v.routeColor} size="sm" />,
    },
    { key: 'driver', header: 'Driver' },
    {
      key: 'delay',
      header: 'Adherence',
      width: '130px',
      render: (v) => <DelayBadge delayMinutes={v.delay} />,
    },
    { key: 'status', header: 'Status', width: '120px' },
  ];

  return (
    <div className={isDark ? 'dark' : ''}>
      <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)] p-6 transition-colors duration-200">
        <div className="max-w-5xl mx-auto space-y-10">
          {/* Top Bar */}
          <header className="flex items-center justify-between border-b border-[var(--rule)] pb-5">
            <div>
              <div className="flex items-center gap-3">
                <span className="font-extrabold text-2xl tracking-tight uppercase" style={{ fontFamily: 'var(--font-mono)' }}>
                  Wayline
                </span>
                <span className="text-xs px-2 py-0.5 rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] font-bold">
                  Design Showcase
                </span>
              </div>
              <p className="text-xs text-[var(--ink-soft)] mt-1">
                Municipal Transit Signage System Primitives (Spec §9)
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsDark(!isDark)}
                type="button"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[4px] border border-[var(--rule)] bg-[var(--surface)] text-xs font-semibold cursor-pointer hover:bg-[var(--paper)]"
              >
                {isDark ? <Sun size={14} className="text-[var(--signal)]" /> : <Moon size={14} />}
                <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
              </button>
            </div>
          </header>

          {/* Section 1: Connection & Live Status */}
          <section className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
              1. Telemetry & Live Indicators
            </h2>
            <div className="flex flex-wrap items-center gap-3 p-4 rounded-[4px] border border-[var(--rule)] bg-[var(--surface)]">
              <ConnectionStatus status="connected" />
              <ConnectionStatus status="reconnecting" />
              <ConnectionStatus status="polling" />
              <ConnectionStatus status="disconnected" />
              <div className="h-5 w-px bg-[var(--rule)] mx-2" />
              <LiveDot isLive={true} />
              <LiveDot isLive={false} />
            </div>
          </section>

          {/* Section 2: Route Chips & Badges */}
          <section className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
              2. Route Chips & Adherence Badges
            </h2>
            <div className="flex flex-wrap items-center gap-4 p-4 rounded-[4px] border border-[var(--rule)] bg-[var(--surface)]">
              <RouteChip code="7A" color="#2563EB" size="sm" />
              <RouteChip code="14" color="#DC2626" size="md" />
              <RouteChip code="21E" color="#059669" size="lg" />
              <RouteChip code="E-LOOP" color="#EAB308" size="md" />
              <RouteChip code="NIGHT" color="#1F2937" size="md" />
              <div className="h-5 w-px bg-[var(--rule)] mx-2" />
              <DelayBadge delayMinutes={0} />
              <DelayBadge delayMinutes={3} />
              <DelayBadge delayMinutes={11} />
              <div className="h-5 w-px bg-[var(--rule)] mx-2" />
              <OccupancyLabel level="empty" />
              <OccupancyLabel level="seats" />
              <OccupancyLabel level="standing" />
              <OccupancyLabel level="full" />
            </div>
          </section>

          {/* Section 3: Municipal Departure Board */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
                  3. Stop Departure Board (Civil Lines Terminal)
                </h2>
                <p className="text-xs text-[var(--ink-soft)]">
                  Minutes numeral is the loudest element; live GPS marked with green pulse
                </p>
              </div>
              <span className="text-xs font-mono font-bold text-[var(--ink-soft)]">
                STOP: S014
              </span>
            </div>
            <div className="rounded-[8px] border border-[var(--rule)] bg-[var(--surface)] overflow-hidden shadow-xs divide-y divide-[var(--rule)]">
              {sampleDepartures.map((dep) => (
                <DepartureRow
                  key={dep.id}
                  departure={dep}
                  onClick={() => alert(`Selected departure ${dep.routeCode} to ${dep.destination}`)}
                />
              ))}
            </div>
          </section>

          {/* Section 4: Data Table */}
          <section className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
              4. Dispatcher Fleet Board (DataTable)
            </h2>
            <DataTable
              data={sampleFleet}
              columns={fleetColumns}
              keyExtractor={(item) => item.fleetNo}
              onRowClick={(item) => alert(`Vehicle inspected: ${item.fleetNo}`)}
            />
          </section>

          {/* Section 5: State Feedback & Error States */}
          <section className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
              5. Inline Feedback & Empty States
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InlineError
                message="WebSocket connection timed out. Falling back to 10s HTTP polling."
                onRetry={() => alert('Retrying connection...')}
              />
              <EmptyState
                title="No active disruptions reported"
                description="All 6 routes are operating within normal scheduled headway tolerances."
                actionLabel="Create Notice"
                onAction={() => alert('Composer opened')}
              />
            </div>
          </section>

          {/* Section 6: Drawer Primitive */}
          <section className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
              6. Slide-out Panel (Drawer)
            </h2>
            <button
              onClick={() => setDrawerOpen(true)}
              type="button"
              className="px-4 py-2 rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] font-semibold text-xs cursor-pointer hover:opacity-90"
            >
              Open Incident Drawer Demo
            </button>
            <Drawer
              isOpen={drawerOpen}
              onClose={() => setDrawerOpen(false)}
              title="Incident INC-042: Vehicle Breakdown"
              subtitle="Vehicle BUS-104 on Route 14 near Katra Crossing"
            >
              <div className="space-y-4 text-xs">
                <div className="p-3 bg-[var(--late)]/10 border border-[var(--late)]/20 rounded-[4px] text-[var(--late)] font-semibold">
                  Driver reported engine coolant failure. 3 remaining trips affected.
                </div>
                <h4 className="font-bold uppercase tracking-wider text-[var(--ink-soft)]">
                  Suggested Replacements (Ranked)
                </h4>
                <div className="p-3 rounded-[4px] border border-[var(--rule)] bg-[var(--paper)]">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold">BUS-108 (Standard Diesel)</span>
                    <span className="text-[var(--go)] font-semibold">1.2 km away</span>
                  </div>
                  <p className="text-[var(--ink-soft)] mb-2">Depot Subedarganj • Driver S. Patel available</p>
                  <button
                    onClick={() => {
                      alert('Replacement assigned!');
                      setDrawerOpen(false);
                    }}
                    type="button"
                    className="w-full py-1.5 rounded-[4px] bg-[var(--go)] text-white font-bold cursor-pointer hover:opacity-90"
                  >
                    Assign BUS-108 as Replacement
                  </button>
                </div>
              </div>
            </Drawer>
          </section>
        </div>
      </div>
    </div>
  );
};
