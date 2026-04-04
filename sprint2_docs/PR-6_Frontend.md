# Pull Request 6: Frontend Voice UI

**Assigned to:** Vikram Aditya Verma  
**Branch Name:** `feat/sprint2-frontend-voice`

---

## PR Title
`feat(frontend): sprint 2 - voice onboarding ui and vapi web hook`

## PR Description

### ## Summary
This PR replaces the frontend stubs with a fully active, real-time Voice interaction UI. It introduces a `useVoice` hook wrapping the `@vapi-ai/web` SDK to seamlessly conduct a call. The UI tracks transcriptions in a chat layout and visualizes the agent's current state with animated tailwind waveforms.

### ## Changes
- Created `Onboard.jsx` layout tracking KYC completion.
- Created `VoiceWaveform.jsx` with keyframe-based CSS animations representing listening/speaking endpoints.
- Created `TranscriptPanel.jsx` rendering chat bubbles sequentially.
- Created `useVoice.js` encapsulating Vapi start/stop lifecycle and HTTP long-polling the backend state.
- Added `@vapi-ai/web` to `package.json`.
- Added mock sessions to ease frontend development prior to full API completion.

### ## How to test
1. If developing locally while backend PRs are unmerged, use `useMockVoice` out of `useVoice.js`.
2. Ensure `VAPI_WEB_TOKEN` is loaded into the frontend environment.

### ## Dependencies
**Depends on:** `feat/sprint2-foundation` (PR-1). Must be merged into main first!

### ## Definition of Done
- No hardcoded secrets.
- Unmounting the hook must clearly kill the VAPI connection to prevent memory leaks and zombie calls.
- Animated state smoothly transitions without jittering.

---

## Reviewers Checklist
- [ ] No npm or yarn commands anywhere
- [ ] No hardcoded API keys or secrets
- [ ] All Python functions have type hints
- [ ] All async functions use await (no blocking calls)
- [ ] Error states handled — no unhandled promise rejections
- [ ] Imports use absolute paths (`app.*`) not relative
- [ ] docker compose up still works after this PR

---

## Files to Create/Modify

### 1. `apps/frontend/src/utils/constants.js` (NEW/MODIFY)
```javascript
export const KYC_FIELDS = ["name", "dob", "phone", "aadhaar_number", "pan_number", "address"];

export const KYC_FIELD_LABELS = {
  name: "Full Name",
  dob: "Date of Birth",
  phone: "Mobile Number",
  aadhaar_number: "Aadhaar Number",
  pan_number: "PAN Number (Optional)",
  address: "Full Address"
};

export const KYC_REQUIRED_FIELDS = ["name", "dob", "phone", "aadhaar_number", "address"];
```

### 2. `apps/frontend/package.json` (MODIFY)
*Ensure your dependencies map includes `@vapi-ai/web`*

```json
{
  "name": "@bharatvoice/frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "lucide-react": "^0.441.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.2",
    "axios": "^1.7.7",
    "@vapi-ai/web": "^2.1.2"
  },
  "devDependencies": {
    "@eslint/js": "^9.9.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.9.0",
    "eslint-plugin-react-hooks": "^5.1.0-rc.0",
    "eslint-plugin-react-refresh": "^0.4.9",
    "globals": "^15.9.0",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.11",
    "typescript": "^5.5.3",
    "typescript-eslint": "^8.0.1",
    "vite": "^5.4.1"
  }
}
```

### 3. `apps/frontend/src/hooks/useVoice.js` (REPLACE)
```javascript
import { useState, useRef, useEffect } from "react";
import Vapi from "@vapi-ai/web";
import axios from "axios";

const VAPI_WEB_TOKEN = import.meta.env.VITE_VAPI_WEB_TOKEN || "";
const apiClient = axios.create({ baseURL: import.meta.env.VITE_API_URL });

export function useVoice(language = "hi") {
  const [callStatus, setCallStatus] = useState("idle"); // idle, connecting, active, ended, complete
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [sessionData, setSessionData] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [callId, setCallId] = useState(null);
  const [error, setError] = useState(null);

  const vapiRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const startPolling = (cid) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await apiClient.get(`/api/voice/call/${cid}/status`);
        setSessionData(res.data);
        if (res.data.is_complete) {
          setCallStatus("complete");
          stopPolling();
        }
      } catch (err) {
        // silently ignore poll errors to keep UI smooth
      }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  };

  const startCall = async (userId) => {
    try {
      setCallStatus("connecting");
      setError(null);

      const res = await apiClient.post("/api/voice/call/start", { user_id: userId, language });
      const { call_id, web_call_url } = res.data;
      setCallId(call_id);

      vapiRef.current = new Vapi(VAPI_WEB_TOKEN);

      vapiRef.current.on("call-start", () => {
        setCallStatus("active");
        startPolling(call_id);
      });

      vapiRef.current.on("call-end", () => {
        setCallStatus("ended");
        stopPolling();
      });

      vapiRef.current.on("speech-start", () => setIsSpeaking(true));
      vapiRef.current.on("speech-end", () => setIsSpeaking(false));

      vapiRef.current.on("message", (msg) => {
        if (msg.type === "transcript" && msg.role !== "system") {
          setTranscript((prev) => [
            ...prev,
            { role: msg.role, content: msg.transcript, timestamp: new Date().toISOString() }
          ]);
        }
      });

      vapiRef.current.on("error", (e) => {
        setError(e.message || "Call error occurred");
        setCallStatus("ended");
        stopPolling();
      });

      await vapiRef.current.start(web_call_url);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start call");
      setCallStatus("idle");
    }
  };

  const endCall = async () => {
    stopPolling();
    if (vapiRef.current) {
      await vapiRef.current.stop();
    }
    if (callId) {
      await apiClient.delete(`/api/voice/call/${callId}`).catch(() => {});
    }
    setCallStatus("ended");
  };

  const toggleMute = () => {
    if (vapiRef.current) {
      vapiRef.current.setMuted(!isMuted);
    }
    setIsMuted((prev) => !prev);
  };

  useEffect(() => {
    return () => {
      stopPolling();
      if (vapiRef.current) {
        vapiRef.current.stop();
      }
    };
  }, []);

  return { callStatus, isSpeaking, isMuted, sessionData, transcript, startCall, endCall, toggleMute, error };
}

// -------------------------------------------------------------
// LOCAL MOCK FOR DEVELOPMENT BEFORE BACKEND ROUTES ARE MERGED:
// -------------------------------------------------------------
export const MOCK_SESSION_DATA = {
  call_id: "test-call-123",
  status: "active",
  fields_collected: {
    name: "Ramesh Kumar",
    dob: "1990-08-15",
    phone: "9876543210",
    aadhaar_number: null,
    pan_number: null,
    address: null
  },
  missing_fields: ["aadhaar_number", "pan_number", "address"],
  is_complete: false,
  turns_count: 6,
  language: "hi"
};

export function useMockVoice() {
  const [callStatus, setCallStatus] = useState("idle");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  
  const startCall = () => {
    setCallStatus("connecting");
    setTimeout(() => {
      setCallStatus("active");
      setInterval(() => setIsSpeaking(prev => !prev), 4000);
    }, 1500);
  };

  const endCall = () => setCallStatus("ended");
  const toggleMute = () => setIsMuted(prev => !prev);

  return { 
    callStatus, isSpeaking, isMuted, sessionData: MOCK_SESSION_DATA, 
    transcript: [{role: "agent", content: "Namaste!", timestamp: "2024-01-01T00:00:00Z"}], 
    startCall, endCall, toggleMute, error: null 
  };
}
```

### 4. `apps/frontend/src/components/voice/VoiceWaveform.jsx` (REPLACE)
```javascript
import React from 'react';

export default function VoiceWaveform({ isActive, isSpeaking, callStatus }) {
  const bars = Array.from({ length: 20 });

  let statusText = "Tap to begin your KYC call";
  if (callStatus === "connecting") statusText = "Connecting to BharatVoice...";
  if (callStatus === "active" && isSpeaking) statusText = "Agent is speaking";
  if (callStatus === "active" && !isSpeaking) statusText = "Listening...";
  if (callStatus === "ended") statusText = "Call ended";
  if (callStatus === "complete") statusText = "KYC Complete!";

  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-6">
      {/* Keyframe defined inline or added to global index.css */}
      <style>{`
        @keyframes waveform-speaking {
          0%, 100% { height: 4px; }
          50% { height: var(--wave-height); }
        }
        @keyframes waveform-listening {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
      `}</style>
      
      <div className="flex items-center space-x-1 h-12">
        {bars.map((_, i) => {
          // Inner bars are taller than outer bars forming a dome shape
          const distFromCenter = Math.abs(i - 9.5);
          const maxHeight = Math.max(4, 48 - (distFromCenter * 4));
          
          let animationStyle = {};
          let colorClass = "bg-gray-600";
          let baseHeight = "4px";

          if (isActive && isSpeaking) {
            colorClass = "bg-indigo-400";
            animationStyle = {
              animation: "waveform-speaking 0.8s ease-in-out infinite",
              animationDelay: `${i * 0.05}s`,
              "--wave-height": `${maxHeight}px`
            };
          } else if (isActive && !isSpeaking) {
            colorClass = "bg-indigo-300";
            baseHeight = "8px";
            animationStyle = {
              animation: "waveform-listening 2s ease-in-out infinite"
            };
          }

          return (
            <div
              key={i}
              className={`w-1.5 rounded-full transition-all duration-300 ${colorClass}`}
              style={{ height: baseHeight, ...animationStyle }}
            />
          );
        })}
      </div>
      
      <div className="text-sm font-medium text-gray-400 transition-colors animate-pulse">
        {statusText}
      </div>
    </div>
  );
}
```

### 5. `apps/frontend/src/components/voice/TranscriptPanel.jsx` (NEW)
```javascript
import React, { useEffect, useRef } from 'react';

export default function TranscriptPanel({ turns = [] }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  if (turns.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-500 italic border border-gray-800 rounded-xl bg-gray-900/50">
        Your conversation will appear here...
      </div>
    );
  }

  const formatTime = (isoString) => {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col space-y-4 h-48 overflow-y-auto p-4 border border-gray-800 rounded-xl bg-gray-900/50 scrollbar-thin scrollbar-thumb-gray-800">
      {turns.map((turn, i) => {
        const isAgent = turn.role === "agent";
        return (
          <div key={i} className={`flex w-full ${isAgent ? "justify-start" : "justify-end"} transition-opacity duration-300 ease-in opacity-0 animate-[fadeIn_0.3s_forwards]`}>
            {isAgent && (
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold shrink-0 mr-2">
                A
              </div>
            )}
            
            <div className={`max-w-[80%] rounded-xl p-3 text-sm ${isAgent ? "bg-gray-800 text-gray-200" : "bg-indigo-900 text-indigo-50"}`}>
              <div className="text-xs opacity-50 mb-1 flex justify-between">
                <span>{isAgent ? "BharatVoice Agent" : "You"}</span>
                <span className="ml-4">{formatTime(turn.timestamp)}</span>
              </div>
              <p>{turn.content}</p>
            </div>

            {!isAgent && (
              <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-xs font-bold shrink-0 ml-2">
                U
              </div>
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
```

### 6. `apps/frontend/src/pages/Onboard.jsx` (REPLACE)
```javascript
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VoiceWaveform from '../components/voice/VoiceWaveform';
import TranscriptPanel from '../components/voice/TranscriptPanel';
import { useVoice, useMockVoice } from '../hooks/useVoice';
import { KYC_FIELDS, KYC_FIELD_LABELS } from '../utils/constants';

// NOTE: Switch this to `useVoice` once the backend PRs are fully merged
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
```
