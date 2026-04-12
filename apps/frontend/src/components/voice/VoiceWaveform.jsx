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
