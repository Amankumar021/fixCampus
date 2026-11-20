import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck, LogOut, LayoutDashboard, Menu, ChevronRight, ClipboardList, KeyRound, UserRound } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PasswordSettingsModal } from '../../features/auth/PasswordSettingsModal';

export const AppLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [activeSection, setActiveSection] = useState(window.location.hash || '#dashboard');
  const roleLabel = user?.role === 'admin' ? 'Administration' : user?.role === 'staff' ? 'Maintenance' : 'Student services';
  useEffect(() => {
    const updateActive = () => setActiveSection(window.location.hash || '#dashboard');
    window.addEventListener('hashchange', updateActive);
    return () => window.removeEventListener('hashchange', updateActive);
  }, []);

  return (
    <div className="layout-container">
      {/* Sidebar */}
      {menuOpen && <button type="button" className="sidebar-backdrop" onClick={() => setMenuOpen(false)} aria-label="Close navigation" />}
      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="brand-mark"><ShieldCheck size={20} /></div>
          <span>CampusFix</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Workspace</div>
          <a href="#dashboard" onClick={() => setMenuOpen(false)} className={`nav-link ${activeSection === '#dashboard' ? 'active' : ''}`}>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </a>
          <a href="#issues" onClick={() => setMenuOpen(false)} className={`nav-link ${activeSection === '#issues' ? 'active' : ''}`}>
            <ClipboardList size={17} /><span>{user?.role === 'staff' ? 'Work orders' : 'Issues'}</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <button type="button" onClick={() => { setAccountOpen(true); setMenuOpen(false); }} className="user-chip account-profile-button" aria-label="Open account security settings">
            <div className="user-avatar">{user?.full_name?.charAt(0) || 'U'}</div>
            <div className="user-meta">
              <div className="user-name">{user?.full_name}</div>
              <div className="user-role">{user?.role} {user?.department ? `· ${user.department}` : ''}</div>
            </div>
             <KeyRound className="profile-key" size={15} />
          </button>
          <button onClick={logout} className="sidebar-logout">
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      {/* Main Workspace */}
      <div className="main-content">
        <header className="navbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
            <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setMenuOpen(!menuOpen)}><Menu size={18} /></button>
            <div className="breadcrumb"><span>CampusFix</span><ChevronRight size={13} /><strong>{roleLabel}</strong></div>
          </div>
          <div className="navbar-actions">
            <span className="workspace-status">Campus operations · Live</span>
            <button type="button" className="account-top-button" aria-label="Open account security settings" onClick={() => setAccountOpen(true)}><span className="account-top-avatar"><UserRound size={16} /></span><span>Account</span><KeyRound size={14} /></button>
          </div>
        </header>

        <main className="page-body" id="dashboard">
          {children}
        </main>
      </div>
      {accountOpen && <PasswordSettingsModal onClose={() => setAccountOpen(false)} />}
    </div>
  );
};
