import React from 'react';
import clsx from 'clsx';

export default function Badge({ children, status = 'default' }: { children: React.ReactNode, status?: 'default' | 'success' | 'warning' | 'danger' }) {
  const styles = {
    default: 'bg-slate-700 text-slate-300',
    success: 'bg-emerald-900/50 text-emerald-400 border border-emerald-800',
    warning: 'bg-amber-900/50 text-amber-400 border border-amber-800',
    danger: 'bg-red-900/50 text-red-400 border border-red-800',
  };

  return (
    <span className={clsx('px-2.5 py-0.5 rounded-full text-xs font-medium', styles[status])}>
      {children}
    </span>
  );
}
