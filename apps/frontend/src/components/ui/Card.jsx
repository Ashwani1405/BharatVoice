import React from 'react';
import clsx from 'clsx';

export default function Card({ children, className = '' }) {
  return (
    <div className={clsx('bg-fintech-card border border-slate-700 rounded-xl shadow-lg p-6', className)}>
      {children}
    </div>
  );
}
