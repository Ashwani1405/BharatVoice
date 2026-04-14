import React, { useState } from 'react';
import axios from 'axios';
import Card from '../components/ui/Card';
import DocumentUpload from '../components/kyc/DocumentUpload';

interface ExtractedData {
  id_number?: string;
  dob?: string;
  name?: string;
  [key: string]: unknown;
}

export default function KYC() {
  const [step, setStep] = useState<'document' | 'aadhaar' | 'verified'>('document');
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null);
  const [aadhaarNumber, setAadhaarNumber] = useState('');
  const [referenceId, setReferenceId] = useState<string | null>(null);
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleDocumentUpload = (data: ExtractedData) => {
    setExtractedData(data);
    if (data.id_number) {
      setSuccess('Document verified! You can now proceed to Aadhaar verification.');
      // Check if uploaded doc was Aadhaar and extract number
      if (data.id_number.length === 12) {
        setAadhaarNumber(data.id_number);
        setStep('aadhaar');
      }
    }
  };

  const triggerAadhaarOTP = async () => {
    if (!aadhaarNumber || aadhaarNumber.length !== 12) {
      setError('Please enter a valid 12-digit Aadhaar number');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.post(
        `${apiUrl}/api/kyc/verify-aadhaar/trigger`,
        { aadhaar_number: aadhaarNumber },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          },
        }
      );

      setReferenceId(response.data.reference_id);
      setSuccess('OTP sent to your registered phone number');
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to trigger OTP. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const verifyAadhaarOTP = async () => {
    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    if (!referenceId) {
      setError('Reference ID missing. Please trigger OTP first.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.post(
        `${apiUrl}/api/kyc/verify-aadhaar/confirm`,
        { reference_id: referenceId, otp },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
          },
        }
      );

      setSuccess('Aadhaar verified successfully!');
      setStep('verified');
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to verify OTP. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 mt-10">
      <Card>
        <h2 className="text-2xl font-bold mb-4">Know Your Customer (KYC)</h2>
        <p className="text-slate-400 mb-6">
          Complete your identity verification in two steps: Document OCR and Aadhaar verification.
        </p>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 text-sm mb-6">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-900/30 border border-green-700 rounded-lg p-4 text-green-300 text-sm mb-6">
            {success}
          </div>
        )}

        {/* Step 1: Document Upload */}
        <div className={`mb-6 p-4 rounded-lg ${step === 'document' ? 'bg-slate-700/50 border border-slate-600' : 'bg-slate-800/50'}`}>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
              step === 'document' || extractedData 
                ? 'bg-blue-600 text-white' 
                : 'bg-slate-600 text-slate-400'
            }`}>
              1
            </span>
            Document Upload & OCR
          </h3>
          {step === 'document' && <DocumentUpload onUpload={handleDocumentUpload} />}
          {extractedData && step !== 'document' && (
            <div className="text-slate-300 text-sm">
              ✓ Document verified: {extractedData.id_number}
            </div>
          )}
        </div>

        {/* Step 2: Aadhaar Verification */}
        {extractedData && (
          <div className={`mb-6 p-4 rounded-lg ${step === 'aadhaar' ? 'bg-slate-700/50 border border-slate-600' : 'bg-slate-800/50'}`}>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                step === 'aadhaar' || step === 'verified'
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-600 text-slate-400'
              }`}>
                2
              </span>
              Aadhaar OTP Verification
            </h3>

            {step === 'aadhaar' && (
              <div className="space-y-4">
                {!referenceId ? (
                  <>
                    <div>
                      <label className="block text-slate-300 text-sm mb-2">Aadhaar Number</label>
                      <input
                        type="text"
                        value={aadhaarNumber}
                        onChange={(e) => setAadhaarNumber(e.target.value.replace(/\D/g, '').slice(0, 12))}
                        placeholder="Enter 12-digit Aadhaar number"
                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                        disabled={loading}
                      />
                      <p className="text-slate-500 text-xs mt-1">Format: XXXX XXXX XXXX</p>
                    </div>
                    <button
                      onClick={triggerAadhaarOTP}
                      disabled={loading || aadhaarNumber.length !== 12}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-white transition"
                    >
                      {loading ? 'Sending OTP...' : 'Send OTP'}
                    </button>
                  </>
                ) : (
                  <>
                    <p className="text-slate-300 text-sm">OTP sent to your registered mobile number</p>
                    <div>
                      <label className="block text-slate-300 text-sm mb-2">Enter 6-digit OTP</label>
                      <input
                        type="text"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        placeholder="000000"
                        className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-center text-2xl tracking-widest"
                        disabled={loading}
                      />
                    </div>
                    <button
                      onClick={verifyAadhaarOTP}
                      disabled={loading || otp.length !== 6}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed px-4 py-2 rounded-lg text-white transition"
                    >
                      {loading ? 'Verifying...' : 'Verify OTP'}
                    </button>
                    <button
                      onClick={() => {
                        setReferenceId(null);
                        setOtp('');
                      }}
                      className="w-full text-slate-400 hover:text-slate-300 text-sm py-2"
                    >
                      Send OTP again
                    </button>
                  </>
                )}
              </div>
            )}

            {step === 'verified' && (
              <div className="text-green-300 text-sm flex items-center gap-2">
                ✓ Aadhaar verified successfully
              </div>
            )}
          </div>
        )}

        {/* Completion Message */}
        {step === 'verified' && (
          <div className="bg-green-900/30 border border-green-700 rounded-lg p-4 text-center">
            <p className="text-green-300 font-semibold">KYC Verification Complete! ✓</p>
            <p className="text-green-200 text-sm mt-1">Your account has been fully verified.</p>
          </div>
        )}
      </Card>
    </div>
  );
}
