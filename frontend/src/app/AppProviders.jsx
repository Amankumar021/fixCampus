import React from 'react';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../components/common/Toast';

export function AppProviders({ children }) {
  return <ToastProvider><AuthProvider>{children}</AuthProvider></ToastProvider>;
}
