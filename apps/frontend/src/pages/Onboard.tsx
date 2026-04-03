import React from 'react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

export default function Onboard() {
  return (
    <div className="max-w-2xl mx-auto p-6 mt-10">
      <Card>
        <h2 className="text-2xl font-bold mb-4">Voice Onboarding</h2>
        <p className="text-slate-400 mb-6">
          Sprint 2 Placeholder: Call VAPI WebRTC agent here.
        </p>
        <div className="flex justify-center p-10 bg-slate-800 rounded-xl border border-slate-700">
          <Button>Start Call</Button>
        </div>
      </Card>
    </div>
  );
}
