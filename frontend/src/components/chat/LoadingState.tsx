import { useState, useEffect } from 'react';

const MESSAGES = [
  "Understanding your question...",
  "Building analysis...",
  "Verifying result...",
  "Preparing visualization..."
];

export function LoadingState() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (index >= MESSAGES.length - 1) return;
    
    const timer = setTimeout(() => {
      setIndex(prev => prev + 1);
    }, 800); // Change message every 800ms
    
    return () => clearTimeout(timer);
  }, [index]);

  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-1">
        <div className="w-1.5 h-1.5 rounded-full bg-[#a78bfa] animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-[#a78bfa] animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-[#a78bfa] animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-white/60 text-sm animate-pulse">{MESSAGES[index]}</span>
    </div>
  );
}
