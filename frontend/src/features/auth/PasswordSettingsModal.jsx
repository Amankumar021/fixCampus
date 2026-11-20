import React, { useEffect, useState } from 'react';
import { Eye, EyeOff, KeyRound, LockKeyhole, X } from 'lucide-react';
import apiClient from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/common/Toast';

export function PasswordSettingsModal({ onClose }) {
  const { logout } = useAuth();
  const { notify } = useToast();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const closeOnEscape = (event) => { if (event.key === 'Escape' && !busy) onClose(); };
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', closeOnEscape);
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', closeOnEscape);
    };
  }, [busy, onClose]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (newPassword !== confirmPassword) {
      setError('Your new passwords do not match.');
      return;
    }
    if (newPassword === currentPassword) {
      setError('Choose a password different from your current one.');
      return;
    }
    setBusy(true);
    try {
      await apiClient.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      notify('Password updated. Sign in again with your new password.');
      onClose();
      await logout();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not update your password. Please try again.');
      setBusy(false);
    }
  };

  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onClose(); }}>
    <section className="modal-panel password-panel" role="dialog" aria-modal="true" aria-labelledby="password-title">
      <div className="modal-header"><div><div className="page-eyebrow">Account security</div><h2 id="password-title">Change your password</h2><p>Use a new password of at least 8 characters.</p></div><button type="button" className="icon-button" onClick={onClose} disabled={busy} aria-label="Close password settings"><X size={18} /></button></div>
      {error && <div className="notice notice-error" role="alert">{error}</div>}
      <form onSubmit={handleSubmit} className="form-stack">
        <PasswordField id="current-password" label="Current password" value={currentPassword} onChange={setCurrentPassword} shown={showPasswords} />
        <PasswordField id="new-password" label="New password" value={newPassword} onChange={setNewPassword} shown={showPasswords} minLength={8} />
        <PasswordField id="confirm-password" label="Confirm new password" value={confirmPassword} onChange={setConfirmPassword} shown={showPasswords} minLength={8} />
        <button type="button" className="password-visibility" onClick={() => setShowPasswords((value) => !value)}>
          {showPasswords ? <EyeOff size={16} /> : <Eye size={16} />}{showPasswords ? 'Hide passwords' : 'Show passwords'}
        </button>
        <div className="password-guidance"><LockKeyhole size={16} /><span>Changing your password signs out your active sessions so your account stays protected.</span></div>
        <div className="form-actions"><button type="button" className="btn-secondary" onClick={onClose} disabled={busy}>Cancel</button><button type="submit" className="btn-primary" disabled={busy || !currentPassword || newPassword.length < 8 || !confirmPassword}><KeyRound size={15} />{busy ? 'Updating…' : 'Update password'}</button></div>
      </form>
    </section>
  </div>;
}

function PasswordField({ id, label, value, onChange, shown, minLength }) {
  const autoComplete = id === 'current-password' ? 'current-password' : 'new-password';
  return <div><label className="form-label" htmlFor={id}>{label}</label><input id={id} type={shown ? 'text' : 'password'} autoComplete={autoComplete} required minLength={minLength} maxLength={128} className="input-field" value={value} onChange={(event) => onChange(event.target.value)} /></div>;
}
