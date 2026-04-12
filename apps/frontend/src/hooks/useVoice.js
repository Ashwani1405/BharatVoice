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
