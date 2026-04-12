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
