/**
 * Sprint 2 — Voice Hook
 * Manages the WebRTC connection state to VAPI for real-time voice interaction.
 */
// TODO: Sprint 2 — implement this hook

import { useState } from 'react';

export function useVoice() {
  const [isCalling, setIsCalling] = useState(false);
  
  const startCall = async () => {
    // Implementation placeholder Let's connect to VAPI WebRTC
    setIsCalling(true);
    console.log("Starting voice call...");
    throw new Error("Sprint 2: implement VAPI webRTC connection");
  };

  const endCall = () => {
    setIsCalling(false);
    console.log("Call ended");
  };

  return { isCalling, startCall, endCall };
}
