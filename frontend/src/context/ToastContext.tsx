import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (message: string, title?: string) => void;
  error: (message: string, title?: string) => void;
  warning: (message: string, title?: string) => void;
  info: (message: string, title?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    const duration = toast.duration ?? 4500;
    const newToast: ToastMessage = { ...toast, id };

    setToasts(prev => [...prev, newToast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const success = useCallback((message: string, title = 'Success') => {
    addToast({ type: 'success', title, message });
  }, [addToast]);

  const error = useCallback((message: string, title = 'Error') => {
    addToast({ type: 'error', title, message });
  }, [addToast]);

  const warning = useCallback((message: string, title = 'Attention') => {
    addToast({ type: 'warning', title, message });
  }, [addToast]);

  const info = useCallback((message: string, title = 'Info') => {
    addToast({ type: 'info', title, message });
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      <div className="toast-container" style={{
        position: 'fixed',
        top: '1.25rem',
        right: '1.25rem',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        maxWidth: '420px',
        width: '100%',
        pointerEvents: 'none'
      }}>
        {toasts.map(toast => {
          let icon = <Info size={18} color="var(--accent-orange)" />;
          let borderColor = 'var(--accent-orange)';
          let bgColor = '#ffffff';

          if (toast.type === 'success') {
            icon = <CheckCircle2 size={18} color="#16a34a" />;
            borderColor = '#86efac';
          } else if (toast.type === 'error') {
            icon = <AlertCircle size={18} color="#dc2626" />;
            borderColor = '#fca5a5';
          } else if (toast.type === 'warning') {
            icon = <AlertTriangle size={18} color="#d97706" />;
            borderColor = '#fde68a';
          }

          return (
            <div
              key={toast.id}
              className="toast-card"
              style={{
                background: bgColor,
                border: `1px solid ${borderColor}`,
                borderRadius: '8px',
                padding: '0.85rem 1rem',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                color: '#09090b',
                pointerEvents: 'auto',
                animation: 'slideIn 0.25s ease-out'
              }}
            >
              <div style={{ flexShrink: 0, marginTop: '2px' }}>{icon}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                {toast.title && (
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: '2px', color: '#09090b' }}>
                    {toast.title}
                  </div>
                )}
                <div style={{ fontSize: '0.825rem', color: '#52525b', lineHeight: '1.35', wordBreak: 'break-word' }}>
                  {toast.message}
                </div>
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#71717a',
                  cursor: 'pointer',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                  borderRadius: '4px'
                }}
              >
                <X size={15} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
