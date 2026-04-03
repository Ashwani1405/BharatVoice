import React from 'react';
import Card from '../components/ui/Card';
import DocumentUpload from '../components/kyc/DocumentUpload';

export default function KYC() {
  return (
    <div className="max-w-2xl mx-auto p-6 mt-10">
      <Card>
        <h2 className="text-2xl font-bold mb-4">Document Verification</h2>
        <p className="text-slate-400 mb-6">
          Sprint 3 Placeholder: Upload your Aadhaar or PAN card.
        </p>
        <DocumentUpload />
      </Card>
    </div>
  );
}
