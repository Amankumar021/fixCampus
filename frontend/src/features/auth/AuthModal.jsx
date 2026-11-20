import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck, UserPlus, ArrowRight, CircleHelp } from 'lucide-react';
import apiClient from '../../services/api';

export const AuthModal = () => {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState(new URLSearchParams(window.location.search).has('reset_token') ? 'reset' : 'login');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      if (mode === 'forgot') {
        await apiClient.post('/auth/forgot-password', { email });
        setMessage('If that account exists, password reset instructions will be sent to its email address.');
        return;
      }
      if (mode === 'reset') {
        const token = new URLSearchParams(window.location.search).get('reset_token');
        if (!token) throw new Error('This password reset link is missing its token. Request a new link.');
        if (newPassword !== confirmPassword) throw new Error('The passwords do not match.');
        await apiClient.post('/auth/reset-password', { token, new_password: newPassword });
        window.history.replaceState({}, '', window.location.pathname);
        setMode('login'); setPassword(''); setNewPassword(''); setConfirmPassword('');
        setMessage('Password changed. Sign in with your new password.');
        return;
      }
      if (isRegister) await register(email, password, fullName, phoneNumber);
      await login(email, password);
    } catch (err) {
      setError(err.message || err.response?.data?.detail || 'Authentication failed. Please check your details and try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (role) => {
    const accounts = {
      admin: ['admin@campusfix.edu', 'Admin@12345'],
      staff: ['electrical.staff@campusfix.edu', 'Staff@12345'],
      student: ['student1@campusfix.edu', 'Student@12345'],
    };
    setEmail(accounts[role][0]);
    setPassword(accounts[role][1]);
    setIsRegister(false);
  };

  return (
    <div className="auth-page">
      <section className="auth-visual" aria-label="CampusFix introduction">
        <div className="auth-brand"><div className="brand-mark"><ShieldCheck size={20} /></div> CampusFix</div>
        <div className="auth-copy">
          <div className="page-eyebrow" style={{ color: '#a8dec2' }}>Campus operations, connected</div>
          <h1>A better campus starts with listening.</h1>
          <p>One place to report campus issues, coordinate response teams, and keep every student informed.</p>
        </div>
        <div className="auth-footnote">A clearer path from report to resolution.</div>
      </section>
      <section className="auth-form-side">
        <div className="auth-form">
          <h2>{mode === 'reset' ? 'Choose a new password' : mode === 'forgot' ? 'Reset your password' : isRegister ? 'Create your account' : 'Welcome back'}</h2>
          <p className="auth-form-intro">{mode === 'reset' ? 'Use at least 8 characters for your new password.' : mode === 'forgot' ? 'Enter the campus email for your account.' : isRegister ? 'Join your campus community and follow the issues that matter.' : 'Sign in to your campus operations workspace.'}</p>
          {error && <div className="auth-error" role="alert">{error}</div>}
          {message && <div className="notice notice-success" role="status">{message}</div>}

          <form onSubmit={handleSubmit} className="auth-fields">
            {isRegister && mode === 'login' && <>
              <div>
                <label className="form-label" htmlFor="full-name">Full name</label>
                <input id="full-name" type="text" autoComplete="name" required className="input-field" placeholder="Your full name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
              </div>
              <div>
                <label className="form-label" htmlFor="phone-number">Phone number <span style={{ color: 'var(--muted)', fontWeight: 450 }}>(optional)</span></label>
                <input id="phone-number" type="tel" autoComplete="tel" className="input-field" placeholder="+91 98765 43210" value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} />
              </div>
            </>}
            {mode !== 'reset' && <div>
              <label className="form-label" htmlFor="email">Campus email</label>
              <input id="email" type="email" autoComplete="email" required className="input-field" placeholder="you@campus.edu" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>}
            {mode === 'login' && <div>
              <label className="form-label" htmlFor="password">Password</label>
              <input id="password" type="password" autoComplete={isRegister ? 'new-password' : 'current-password'} required minLength={isRegister ? 6 : undefined} className="input-field" placeholder="Enter your password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>}
            {mode === 'reset' && <>
              <div><label className="form-label" htmlFor="new-password">New password</label><input id="new-password" type="password" autoComplete="new-password" required minLength={8} className="input-field" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></div>
              <div><label className="form-label" htmlFor="confirm-password">Confirm new password</label><input id="confirm-password" type="password" autoComplete="new-password" required minLength={8} className="input-field" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} /></div>
            </>}
            <button type="submit" disabled={loading} className="btn-primary" style={{ marginTop: 4, minHeight: 44 }}>
              {loading ? 'Please wait...' : mode === 'reset' ? 'Update password' : mode === 'forgot' ? 'Send reset link' : isRegister ? 'Create student account' : 'Sign in'}
              {isRegister ? <UserPlus size={16} /> : <ArrowRight size={16} />}
            </button>
          </form>

          <div className="auth-switch">
            {mode === 'reset' || mode === 'forgot' ? 'Remember your password?' : isRegister ? 'Already have an account?' : 'New to CampusFix?'}
            <button type="button" onClick={() => { setMode('login'); setIsRegister(false); setError(''); setMessage(''); }}>{mode === 'reset' || mode === 'forgot' || isRegister ? 'Sign in' : 'Create an account'}</button>
          </div>

          {mode === 'login' && !isRegister && <button className="auth-switch" style={{ border: 0, background: 'transparent', width: '100%', justifyContent: 'center', cursor: 'pointer' }} type="button" onClick={() => { setMode('forgot'); setError(''); setMessage(''); }}>Forgot password?</button>}
          {mode === 'login' && !isRegister && <div className="auth-demo">
            <div className="auth-demo-title">Explore a demo workspace</div>
            <div className="auth-demo-actions">
              <button type="button" onClick={() => fillDemo('admin')} className="demo-chip">Admin</button>
              <button type="button" onClick={() => fillDemo('staff')} className="demo-chip">Maintenance staff</button>
              <button type="button" onClick={() => fillDemo('student')} className="demo-chip">Student</button>
            </div>
          </div>}
          <div style={{ marginTop: 28, color: 'var(--muted)', fontSize: 10, display: 'flex', justifyContent: 'center', gap: 5, alignItems: 'center' }}><CircleHelp size={12} /> Need access? Contact your campus administrator.</div>
        </div>
      </section>
    </div>
  );
};
