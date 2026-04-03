/**
 * Sprint 3 — Document Upload Component
 * Handles dragging and dropping ID cards for KYC upload.
 */
// TODO: Sprint 3 — implement this component
import React from 'react';

export default function DocumentUpload({ onUpload }) {
  return (
    <div className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center bg-slate-800/50">
      <p className="text-slate-400 mb-4">Drag and drop your ID (Aadhaar or PAN) here</p>
      <button className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-sm text-white" disabled>
        Upload File (Sprint 3)
      </button>
    </div>
  );
}
