import React, { useState, useEffect } from 'react';
import { fetchApi } from '../../lib/api';
import { useAuthStore } from '../../lib/authStore';
import { RouteChip } from '../../components/design/RouteChip';
import { DelayBadge } from '../../components/design/DelayBadge';
import { ChangePasswordModal } from '../../components/auth/ChangePasswordModal';
import {
  Play,
  Square,
  AlertTriangle,
  Clock,
  MapPin,
  CheckCircle,
  LogOut,
  KeyRound,
  ShieldAlert,
  Send,
} from 'lucide-react';

export const DriverPortal: React.FC = () => {
  const { user, logout } = useAuthStore();
  const [duty, setDuty] = useState<any>(null);
  const [currentTripStatus, setCurrentTripStatus] = useState<'scheduled' | 'in_progress' | 'completed'>('in_progress');
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [changePwdOpen, setChangePwdOpen] = useState(false);

  // Issue report form (R-3)
  const [issueType, setIssueType] = useState('traffic');
  const [issueNote, setIssueNote] = useState('');
  const [reportSuccess, setReportSuccess] = useState(false);

  const loadDuty = async () => {
    try {
      const res = await fetchApi('/driver/duty/today');
      setDuty(res);
    } catch (e) {
      console.error('Failed to load driver duty:', e);
    }
  };

  useEffect(() => {
    loadDuty();
  }, []);

  const handleStartTrip = async (tripId: string) => {
    try {
      await fetchApi(`/driver/trips/${tripId}/start`, { method: 'POST' });
      setCurrentTripStatus('in_progress');
      alert(`Trip ${tripId} started.`);
    } catch (e: any) {
      alert(`Failed to start trip: ${e.message}`);
    }
  };

  const handleEndTrip = async (tripId: string) => {
    try {
      await fetchApi(`/driver/trips/${tripId}/end`, { method: 'POST' });
      setCurrentTripStatus('completed');
      alert(`Trip ${tripId} marked completed.`);
    } catch (e: any) {
      alert(`Failed to complete trip: ${e.message}`);
    }
  };

  const handleReportIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchApi('/incidents', {
        method: 'POST',
        body: JSON.stringify({
          type: issueType,
          severity: issueType === 'breakdown' ? 'high' : 'med',
          description: `Driver ${user?.name || 'Driver'}: ${issueNote || issueType}`,
          vehicle_id: 'V-101',
        }),
      });
      setReportSuccess(true);
      setTimeout(() => {
        setReportSuccess(false);
        setReportModalOpen(false);
        setIssueNote('');
      }, 1500);
    } catch (err: any) {
      alert(`Failed to submit issue: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--paper)] text-[var(--ink)]">
      {/* High-contrast mobile-friendly driver header (SPEC §8.4) */}
      <header className="border-b border-[var(--rule)] bg-[var(--surface)] px-4 py-3 sticky top-0 z-30 shadow-xs">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--signal-ink)] bg-[var(--signal)] px-1.5 py-0.5 rounded">
              Driver Shift Portal
            </span>
            <h1 className="text-base font-extrabold tracking-tight mt-0.5 text-[var(--ink)]">
              {user?.name || 'Driver Rajesh Kumar'}
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setChangePwdOpen(true)}
              className="p-1.5 rounded border border-[var(--rule)] text-[var(--ink-soft)] hover:text-[var(--ink)] cursor-pointer"
            >
              <KeyRound size={15} />
            </button>
            <button
              onClick={logout}
              className="p-1.5 rounded border border-[var(--late)]/30 text-[var(--late)] cursor-pointer"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-md mx-auto p-4 space-y-4">
        {/* Today's Duty Summary (R-1) */}
        <div className="p-4 rounded-[6px] border border-[var(--rule)] bg-[var(--surface)] space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-mono font-bold text-sm text-[var(--ink)]">
              Shift {duty?.duty_id || 'DUTY-101'}
            </span>
            <span className="font-semibold text-[var(--go)]">On Duty</span>
          </div>
          <div className="text-[var(--ink-soft)] space-y-1">
            <p>Vehicle: <strong>{duty?.assigned_vehicle || 'BUS-101 (UP-70-AT-1001)'}</strong></p>
            <p>Hours: <strong>{duty?.start_time || '07:30'} — {duty?.end_time || '15:30'}</strong></p>
            <p className="text-[var(--signal-ink)] font-medium">Break: {duty?.break_window}</p>
          </div>
        </div>

        {/* Current Active Trip Card with Large Buttons (R-2, Spec §8.4) */}
        <div className="p-5 rounded-[8px] border-2 border-[var(--signal)] bg-[var(--surface)] shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <RouteChip code={duty?.current_trip?.route_code || '7A'} color="#2563EB" size="lg" />
            <span className="font-bold text-sm uppercase text-[var(--go)]">
              {currentTripStatus === 'in_progress' ? 'Trip In Progress' : 'Trip Scheduled'}
            </span>
          </div>

          <div>
            <h2 className="text-xl font-extrabold text-[var(--ink)]">
              {duty?.current_trip?.destination || 'Sangam Ghat Terminal'}
            </h2>
            <div className="flex items-center gap-2 mt-1 text-xs text-[var(--ink-soft)] font-medium">
              <Clock size={13} />
              <span>Scheduled: {duty?.current_trip?.start_time} - {duty?.current_trip?.end_time}</span>
              <span>•</span>
              <DelayBadge delayMinutes={duty?.current_trip?.delay_minutes || 2} />
            </div>
          </div>

          <div className="p-3 bg-[var(--paper)] rounded border border-[var(--rule)] flex items-center justify-between text-xs">
            <span className="text-[var(--ink-soft)]">Next Stop:</span>
            <span className="font-bold text-[var(--ink)] flex items-center gap-1">
              <MapPin size={13} className="text-[var(--signal)]" />
              {duty?.current_trip?.next_stop || 'Medical College (SRN Hospital)'}
            </span>
          </div>

          {/* Large Touch Target Action Buttons (Spec §8.4) */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <button
              onClick={() => handleStartTrip(duty?.current_trip?.id || 'TRIP-1')}
              disabled={currentTripStatus === 'in_progress'}
              className={`h-14 rounded-[6px] font-extrabold text-sm flex items-center justify-center gap-2 cursor-pointer transition-colors ${
                currentTripStatus === 'in_progress'
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-[var(--go)] text-white hover:opacity-90'
              }`}
            >
              <Play size={18} />
              <span>Start Trip</span>
            </button>

            <button
              onClick={() => handleEndTrip(duty?.current_trip?.id || 'TRIP-1')}
              disabled={currentTripStatus === 'completed'}
              className="h-14 rounded-[6px] font-extrabold text-sm bg-[var(--late)] text-white flex items-center justify-center gap-2 cursor-pointer hover:opacity-90 transition-colors"
            >
              <Square size={18} />
              <span>End Trip</span>
            </button>
          </div>

          {/* Report Issue Secondary Button (R-3) */}
          <button
            onClick={() => setReportModalOpen(true)}
            className="w-full h-11 rounded-[6px] border border-[var(--rule)] bg-[var(--paper)] hover:bg-[var(--surface)] text-[var(--late)] font-bold text-xs flex items-center justify-center gap-2 cursor-pointer"
          >
            <AlertTriangle size={15} />
            <span>Report Issue (Breakdown / Traffic / Delay)</span>
          </button>
        </div>

        {/* Remaining Trips in Duty Manifest (R-1) */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ink-soft)]">
            Remaining Shift Trips ({duty?.upcoming_trips?.length || 2})
          </h3>
          {duty?.upcoming_trips?.map((t: any) => (
            <div key={t.id} className="p-3 rounded border border-[var(--rule)] bg-[var(--surface)] flex items-center justify-between text-xs">
              <div className="flex items-center gap-2.5">
                <RouteChip code={t.route_code} size="sm" />
                <div>
                  <span className="font-bold text-[var(--ink)] block">{t.destination}</span>
                  <span className="text-[10px] text-[var(--ink-soft)] font-mono">{t.start_time} - {t.end_time}</span>
                </div>
              </div>
              <span className="text-[10px] uppercase font-bold text-[var(--ink-soft)]">Scheduled</span>
            </div>
          ))}
        </div>
      </main>

      {/* Driver Incident Report Modal (R-3) */}
      {reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-[8px] max-w-sm w-full p-5 shadow-xl space-y-4">
            <div className="flex items-center gap-2">
              <ShieldAlert size={18} className="text-[var(--late)]" />
              <h3 className="text-sm font-bold text-[var(--ink)]">Report Operational Issue</h3>
            </div>

            {reportSuccess ? (
              <div className="p-3 bg-[var(--go)]/10 text-[var(--go)] rounded font-semibold text-xs flex items-center gap-2">
                <CheckCircle size={15} />
                <span>Incident submitted to Operations Dispatcher!</span>
              </div>
            ) : (
              <form onSubmit={handleReportIssue} className="space-y-3 text-xs">
                <div>
                  <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                    Issue Category
                  </label>
                  <select
                    value={issueType}
                    onChange={(e) => setIssueType(e.target.value)}
                    className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] text-xs font-semibold"
                  >
                    <option value="traffic">Traffic Delay</option>
                    <option value="breakdown">Vehicle Breakdown (Engine/Tire)</option>
                    <option value="accident">Accident / Road Obstruction</option>
                    <option value="other">Passenger / Medical Emergency</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase text-[var(--ink-soft)] mb-1">
                    Details / Location Note
                  </label>
                  <textarea
                    rows={3}
                    placeholder="e.g. Broken water pipe near SRN hospital, delay 15m..."
                    value={issueNote}
                    onChange={(e) => setIssueNote(e.target.value)}
                    className="w-full p-2 border border-[var(--rule)] rounded bg-[var(--paper)] text-xs"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setReportModalOpen(false)}
                    className="px-3 py-1.5 border border-[var(--rule)] rounded text-xs text-[var(--ink-soft)] cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 bg-[var(--late)] text-white font-bold rounded text-xs flex items-center gap-1 cursor-pointer"
                  >
                    <Send size={13} />
                    <span>Submit Report</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      <ChangePasswordModal isOpen={changePwdOpen} onClose={() => setChangePwdOpen(false)} />
    </div>
  );
};
