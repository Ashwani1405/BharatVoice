/**
 * Sprint 2 — Voice Waveform visualization
 * Displays standard active state animation during a voice call.
 */
// TODO: Sprint 2 — implement this component
import React from 'react';

export default function VoiceWaveform({ isSpeaking }: { isSpeaking: boolean }) {
  return (
    <div className="flex items-center justify-center space-x-1 h-12">
      {/* Placeholder animation for now */}
      <span className="text-slate-400 text-sm italic">
        {isSpeaking ? "Speaking..." : "Listening..."}
      </span>
    </div>
  );
}
