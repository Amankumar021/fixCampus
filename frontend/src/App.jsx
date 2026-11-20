import React from 'react';
import { useAuth } from './context/AuthContext';
import { AppProviders } from './app/AppProviders';
import { AuthModal } from './features/auth/AuthModal';
import { AppLayout } from './components/layout/AppLayout';
import { StudentDashboard } from './features/student/StudentDashboard';
import { StaffDashboard } from './features/staff/StaffDashboard';
import { AdminDashboard } from './features/admin/AdminDashboard';
import './index.css';
import './App.css';

const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen" role="status" aria-live="polite">
        <span className="loading-mark"><span /></span>
        <div><strong>CampusFix</strong><span>Preparing your workspace…</span></div>
      </div>
    );
  }

  if (!user) {
    return <AuthModal />;
  }

  return (
    <AppLayout>
      {user.role === 'admin' && <AdminDashboard />}
      {user.role === 'staff' && <StaffDashboard />}
      {user.role === 'student' && <StudentDashboard />}
    </AppLayout>
  );
};

export function App() {
  return (
    <AppProviders>
      <AppContent />
    </AppProviders>
  );
}

export default App;
