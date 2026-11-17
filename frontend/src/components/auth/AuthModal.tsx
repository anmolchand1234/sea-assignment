import React, { useState } from 'react';
import { useAuthStore } from '../../lib/authStore';
import { fetchApi } from '../../lib/api';
import { LogIn, UserPlus, AlertCircle, Shield, Bus } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'login' | 'signup';
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, defaultTab = 'login' }) => {
  const [tab, setTab] = useState<'login' | 'signup'>(defaultTab);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'passenger' | 'dispatcher'>('passenger');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const setAuth = useAuthStore((s) => s.setAuth);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (tab === 'login') {
        const res = await fetchApi('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        setAuth(
          { id: res.access_token, name: res.name, email: res.email || email, role: res.role },
          res.access_token
        );
      } else {
        const res = await fetchApi('/auth/signup', {
          method: 'POST',
          body: JSON.stringify({ name, email, password, role }),
        });
        setAuth(
          { id: res.access_token, name: res.name, email: res.email || email, role: res.role },
          res.access_token
        );
      }
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-[8px] max-w-sm w-full p-6 shadow-2xl space-y-5">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[var(--rule)] pb-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] flex items-center justify-center font-extrabold text-sm">
              W
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--ink)] tracking-tight">
                {tab === 'login' ? 'Sign In to Wayline' : 'Create an Account'}
              </h2>
              <p className="text-[10px] text-[var(--ink-soft)] uppercase font-semibold">
                Unified Municipal Transit Portal
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="text-xs text-[var(--ink-soft)] hover:text-[var(--ink)] font-bold px-1.5 py-0.5 rounded"
          >
            ✕
          </button>
        </div>

        {/* Tab switch */}
        <div className="flex border-b border-[var(--rule)] text-xs font-semibold">
          <button
            type="button"
            onClick={() => { setTab('login'); setError(''); }}
            className={`flex-1 py-2 text-center border-b-2 cursor-pointer ${
              tab === 'login'
                ? 'border-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'border-transparent text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('signup'); setError(''); }}
            className={`flex-1 py-2 text-center border-b-2 cursor-pointer ${
              tab === 'signup'
                ? 'border-[var(--signal)] text-[var(--signal-ink)] font-bold'
                : 'border-transparent text-[var(--ink-soft)] hover:text-[var(--ink)]'
            }`}
          >
            Sign Up
          </button>
        </div>

        {error && (
          <div className="p-2.5 rounded bg-[var(--late)]/10 text-[var(--late)] text-xs flex items-center gap-1.5 font-medium">
            <AlertCircle size={14} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          {tab === 'signup' && (
            <>
              <div>
                <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rajesh Kumar"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-[4px] border border-[var(--rule)] bg-[var(--paper)] text-[var(--ink)]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
                  I am a
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRole('passenger')}
                    className={`py-2 px-3 rounded-[4px] border flex items-center justify-center gap-1.5 font-semibold cursor-pointer ${
                      role === 'passenger'
                        ? 'border-[var(--signal)] bg-[var(--signal)]/10 text-[var(--signal-ink)] font-bold'
                        : 'border-[var(--rule)] bg-[var(--paper)] text-[var(--ink-soft)]'
                    }`}
                  >
                    <Bus size={14} />
                    <span>Passenger</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('dispatcher')}
                    className={`py-2 px-3 rounded-[4px] border flex items-center justify-center gap-1.5 font-semibold cursor-pointer ${
                      role === 'dispatcher'
                        ? 'border-[var(--signal)] bg-[var(--signal)]/10 text-[var(--signal-ink)] font-bold'
                        : 'border-[var(--rule)] bg-[var(--paper)] text-[var(--ink-soft)]'
                    }`}
                  >
                    <Shield size={14} />
                    <span>Operations / User</span>
                  </button>
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              placeholder="e.g. passenger@wayline.local"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-[4px] border border-[var(--rule)] bg-[var(--paper)] text-[var(--ink)]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
              Password
            </label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-[4px] border border-[var(--rule)] bg-[var(--paper)] text-[var(--ink)]"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] font-bold cursor-pointer hover:opacity-90 flex items-center justify-center gap-1.5 transition-opacity"
            >
              {tab === 'login' ? <LogIn size={14} /> : <UserPlus size={14} />}
              <span>{loading ? 'Authenticating...' : tab === 'login' ? 'Sign In' : 'Create Account'}</span>
            </button>
          </div>
        </form>

        {/* Demo Credentials hint */}
        <div className="p-3 bg-[var(--paper)] rounded-[4px] border border-[var(--rule)] text-[11px] text-[var(--ink-soft)] space-y-1">
          <span className="font-bold uppercase tracking-wider block text-[10px] text-[var(--ink)]">
            Demo Credentials (Pre-seeded):
          </span>
          <div className="flex justify-between">
            <span>Dispatcher (User):</span>
            <span className="font-mono text-[var(--ink)] font-semibold">dispatcher@wayline.local / dispatch123</span>
          </div>
          <div className="flex justify-between">
            <span>Admin:</span>
            <span className="font-mono text-[var(--ink)] font-semibold">admin@wayline.local / admin123</span>
          </div>
        </div>
      </div>
    </div>
  );
};
