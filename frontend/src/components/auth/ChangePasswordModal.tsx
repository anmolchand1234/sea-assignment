import React, { useState } from 'react';
import { fetchApi } from '../../lib/api';
import { KeyRound, Check, AlertCircle } from 'lucide-react';

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({ isOpen, onClose }) => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }

    try {
      setLoading(true);
      await fetchApi('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      });
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to change password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-[var(--surface)] border border-[var(--rule)] rounded-[8px] max-w-sm w-full p-5 shadow-xl space-y-4">
        <div className="flex items-center gap-2">
          <KeyRound size={18} className="text-[var(--signal)]" />
          <h3 className="text-sm font-bold text-[var(--ink)]">Change Password</h3>
        </div>

        {error && (
          <div className="p-2.5 rounded bg-[var(--late)]/10 text-[var(--late)] text-xs flex items-center gap-1.5 font-medium">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-2.5 rounded bg-[var(--go)]/10 text-[var(--go)] text-xs flex items-center gap-1.5 font-medium">
            <Check size={14} />
            <span>Password updated successfully!</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
              Current Password
            </label>
            <input
              type="password"
              required
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="w-full px-3 py-1.5 text-xs rounded-[4px] border border-[var(--rule)] bg-[var(--paper)] text-[var(--ink)]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
              New Password
            </label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-1.5 text-xs rounded-[4px] border border-[var(--rule)] bg-[var(--paper)] text-[var(--ink)]"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold text-[var(--ink-soft)] uppercase mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-1.5 text-xs rounded-[4px] border border-[var(--rule)] bg-[var(--paper)] text-[var(--ink)]"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-semibold rounded-[4px] border border-[var(--rule)] hover:bg-[var(--paper)] text-[var(--ink-soft)] cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-3 py-1.5 text-xs font-bold rounded-[4px] bg-[var(--signal)] text-[var(--signal-ink)] hover:opacity-90 cursor-pointer"
            >
              {loading ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

