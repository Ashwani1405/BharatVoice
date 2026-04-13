import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VoiceWaveform from '../components/voice/VoiceWaveform';
import TranscriptPanel from '../components/voice/TranscriptPanel';
import { useVoice, useMockVoice } from '../hooks/useVoice';
import { KYC_FIELDS, KYC_FIELD_LABELS } from '../utils/constants';

// NOTE: Switch to `useMockVoice` for local dev without backend
// const currentHook = useMockVoice; 
const currentHook = useVoice; 

export default function Onboard() {
  const navigate = useNavigate();
  // Using hardcoded language and user for sprint 2 scaffolding
  const { 
    callStatus, isSpeaking, isMuted, sessionData, 
    transcript, startCall, endCall, toggleMute, error 
  } = currentHook("hi");

  useEffect(() => {
    const userId = localStorage.getItem("user_id") || "demo-user-123";
    startCall(userId);
  }, []); // eslint-disable-line

  useEffect(() => {
    if (callStatus === "complete") {
      setTimeout(() => navigate('/kyc'), 1500);
    }
  }, [callStatus, navigate]);

  if (error) {
    return (
      <div className="min-h-screen bg-fintech-dark text-white flex flex-col items-center justify-center p-4">
        <div className="bg-red-900/20 border border-red-500 p-6 rounded-xl text-center max-w-md">
          <h2 className="text-xl font-bold text-red-500 mb-2">Connection Failed</h2>
          <p className="text-gray-300 mb-4">{error}</p>
          <button onClick={() => window.location.reload()} className="bg-red-600 px-4 py-2 rounded font-medium hover:bg-red-700">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const collectedCount = sessionData 
    ? Object.values(sessionData.fields_collected).filter(v => v !== null).length 
    : 0;

  const renderField = (fieldKey) => {
    const value = sessionData?.fields_collected?.[fieldKey];
    const isNext = sessionData?.missing_fields?.[0] === fieldKey;
    let displayValue = "";

    if (value) {
      if (fieldKey === "phone") displayValue = value.substring(0, 5) + "•••••";
      else if (fieldKey === "aadhaar_number") displayValue = "•••• •••• " + value.slice(-4);
      else if (fieldKey === "pan_number") displayValue = value.substring(0, 2) + "•••••" + value.slice(-2);
      else displayValue = value;
    }

    return (
      <div key={fieldKey} className="flex items-center justify-between p-2 rounded hover:bg-gray-800/50 transition">
        <div className="flex items-center space-x-3">
          {value ? (
            <span className="text-green-500 font-bold">✅</span>
          ) : isNext ? (
            <span className="relative flex h-3 w-3 ml-1 mr-1">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
            </span>
          ) : (
            <span className="text-gray-600 ml-1 mr-1">○</span>
          )}
          <span className={`text-sm ${value ? 'text-gray-200' : isNext ? 'text-yellow-400 font-medium' : 'text-gray-500'}`}>
            {KYC_FIELD_LABELS[fieldKey]}
          </span>
        </div>
        {value && <span className="text-sm font-mono text-gray-400">{displayValue}</span>}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-fintech-dark text-fintech-text py-12 px-4 flex justify-center font-sans tracking-wide">
      <div className="w-full max-w-lg flex flex-col space-y-6">
        
        <header className="flex justify-between items-center py-4 border-b border-gray-800">
          <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
            BharatVoice
          </h1>
          <div className="flex items-center space-x-4 text-sm font-medium">
            <span className="px-2 py-1 rounded bg-indigo-900 text-indigo-200">Hi</span>
            <button onClick={() => navigate('/')} className="text-gray-400 hover:text-white transition">
              ← Back
            </button>
          </div>
        </header>

        <section className="bg-[#111] rounded-2xl border border-gray-800 shadow-2xl p-6">
          <VoiceWaveform 
            isActive={callStatus === 'active'} 
            isSpeaking={isSpeaking} 
            callStatus={callStatus} 
          />
          
          <div className="mt-8 border border-gray-800 rounded-xl p-4 bg-gray-900/30">
            <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
              <h3 className="font-semibold text-gray-200">KYC Progress</h3>
              <span className="text-xs bg-gray-800 px-2 py-1 rounded-full">{collectedCount}/5 fields</span>
            </div>
            <div className="space-y-1">
              {KYC_FIELDS.map(renderField)}
            </div>
          </div>
        </section>

        <section>
          <TranscriptPanel turns={transcript} />
        </section>

        <footer className="flex justify-between pt-4 pb-12 w-full gap-4">
          <button 
            onClick={toggleMute}
            className={`flex-1 py-3 px-4 rounded-xl font-medium transition ${isMuted ? 'bg-amber-600/20 text-amber-500 border border-amber-500/50' : 'bg-gray-800 hover:bg-gray-700 text-white'}`}
          >
            {isMuted ? 'Unmute' : '🔇 Mute'}
          </button>
          
          <button 
            onClick={endCall}
            disabled={callStatus === 'idle' || callStatus === 'ended'}
            className="flex-1 py-3 px-4 rounded-xl font-medium bg-red-500/10 text-red-500 border border-red-500/30 hover:bg-red-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            End Call
          </button>
        </footer>

      </div>
    </div>
  );
}
