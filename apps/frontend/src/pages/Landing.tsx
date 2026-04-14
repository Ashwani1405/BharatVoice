import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/ui/Button';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-fintech-dark bg-gradient-to-br from-fintech-dark to-slate-900 flex flex-col items-center justify-center p-6 bg-noise">
      <div className="absolute top-4 right-4 group">
        <select className="bg-slate-800 text-slate-300 border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-fintech-primary cursor-pointer transition-all">
          <option value="en">English</option>
          <option value="hi">हिंदी (Hindi)</option>
        </select>
      </div>

      <div className="max-w-3xl text-center space-y-8 animate-fade-in-up">
        {/* Logo Placeholder */}
        <div className="w-20 h-20 bg-fintech-primary/20 rounded-2xl mx-auto flex items-center justify-center border border-fintech-primary/30 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
          <svg className="w-10 h-10 text-fintech-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
        </div>

        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight">
            Apna Bank Account Kholein — Sirf Ek Call Mein
          </h1>
          <p className="text-xl md:text-2xl text-slate-400 font-light max-w-2xl mx-auto">
            Open your secure bank account using just your voice. No branches, no typing, no hassle.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
          <Button 
            onClick={() => navigate('/onboard')} 
            className="w-full sm:w-auto px-8 py-4 text-lg bg-gradient-to-r from-fintech-primary to-blue-600 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 transition-all rounded-xl font-bold"
          >
            Start Voice KYC
          </Button>
          <Button 
            variant="secondary"
            onClick={() => navigate('/dashboard')}
            className="w-full sm:w-auto px-8 py-4 text-lg border border-slate-700 hover:border-slate-500 transition-all rounded-xl"
          >
            Go to Dashboard
          </Button>
        </div>

        {/* Trust Badges */}
        <div className="pt-16 grid grid-cols-1 md:grid-cols-3 gap-6 opacity-60">
          <div className="flex flex-col items-center space-y-2">
            <svg className="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
            <span className="text-sm font-medium uppercase tracking-wider text-slate-300">RBI Compliant</span>
          </div>
          <div className="flex flex-col items-center space-y-2">
            <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" /></svg>
            <span className="text-sm font-medium uppercase tracking-wider text-slate-300">Aadhaar Powered</span>
          </div>
          <div className="flex flex-col items-center space-y-2">
            <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            <span className="text-sm font-medium uppercase tracking-wider text-slate-300">End-to-End Encrypted</span>
          </div>
        </div>
      </div>
    </div>
  );
}
