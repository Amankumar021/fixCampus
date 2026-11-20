import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { CheckCircle2, CircleAlert, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const dismiss = useCallback((id) => setItems((current) => current.filter((item) => item.id !== id)), []);
  const notify = useCallback((message, type = 'success') => {
    const id = `${Date.now()}-${Math.random()}`;
    setItems((current) => [...current, { id, message, type }]);
    window.setTimeout(() => dismiss(id), 4500);
  }, [dismiss]);
  const value = useMemo(() => ({ notify }), [notify]);
  return <ToastContext.Provider value={value}>{children}<div className="toast-stack" aria-live="polite">{items.map((item) => <div className={`toast toast-${item.type}`} key={item.id}>{item.type === 'error' ? <CircleAlert size={16} /> : <CheckCircle2 size={16} />}<span>{item.message}</span><button onClick={() => dismiss(item.id)} aria-label="Dismiss notification"><X size={14} /></button></div>)}</div></ToastContext.Provider>;
}

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) throw new Error('useToast must be used inside ToastProvider');
  return value;
}
