import React from 'react';
import clsx from 'clsx';

export default function Button({ children, onClick, variant = 'primary', className = '', type = 'button', disabled = false }) {
  const baseStyles = 'px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-fintech-primary hover:bg-blue-600 text-white',
    secondary: 'bg-slate-700 hover:bg-slate-600 text-white',
    danger: 'bg-fintech-danger hover:bg-red-600 text-white',
    ghost: 'bg-transparent hover:bg-slate-800 text-slate-300'
  };

  return (
    <button 
      type={type}
      onClick={onClick} 
      disabled={disabled}
      className={clsx(baseStyles, variants[variant], className)}
    >
      {children}
    </button>
  );
}
