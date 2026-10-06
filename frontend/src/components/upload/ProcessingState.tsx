import { useEffect, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';

const STEPS = [
  { label: 'Reading dataset',          duration: 700  },
  { label: 'Detecting columns',        duration: 800  },
  { label: 'Understanding data types', duration: 900  },
  { label: 'Profiling dataset',        duration: 1000 },
  { label: 'Preparing DATLY',          duration: 700  },
];

interface Props {
  onComplete: () => void;
}

export function ProcessingState({ onComplete }: Props) {
  const [stepIndex, setStepIndex] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let elapsed = 0;

    const advance = (idx: number) => {
      if (cancelled || idx >= STEPS.length) {
        if (!cancelled) {
          setDone(true);
          setTimeout(() => { if (!cancelled) onComplete(); }, 700);
        }
        return;
      }
      setTimeout(() => {
        if (!cancelled) {
          setStepIndex(idx + 1);
          advance(idx + 1);
        }
      }, STEPS[idx].duration);
      elapsed += STEPS[idx].duration;
    };

    advance(0);
    return () => { cancelled = true; };
  }, [onComplete]);

  const total = STEPS.reduce((s, x) => s + x.duration, 0);

  const progress = done ? 100 : STEPS.slice(0, stepIndex).reduce((s, x) => s + x.duration, 0) / total * 100;

  return (
    <div className="w-full flex flex-col items-center gap-8 py-8">
      {/* Animated icon */}
      <div className="relative w-20 h-20">
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#7c3aed] to-[#f97316] opacity-20 animate-ping" />
        <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-[#7c3aed]/30 to-[#f97316]/20 border border-white/10 flex items-center justify-center">
          {done
            ? <CheckCircle2 size={30} className="text-[#a78bfa]" strokeWidth={1.5} />
            : (
              <svg className="w-9 h-9 animate-spin" viewBox="0 0 36 36" fill="none">
                <circle cx="18" cy="18" r="14" stroke="rgba(139,92,246,0.2)" strokeWidth="2.5" />
                <path d="M18 4 A14 14 0 0 1 32 18" stroke="url(#spin-grad)" strokeWidth="2.5" strokeLinecap="round" />
                <defs>
                  <linearGradient id="spin-grad" x1="18" y1="4" x2="32" y2="18" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#7c3aed" />
                    <stop offset="1" stopColor="#f97316" />
                  </linearGradient>
                </defs>
              </svg>
            )
          }
        </div>
      </div>

      {/* Steps list */}
      <div className="w-full max-w-sm space-y-3">
        {STEPS.map((step, i) => {
          const isComplete = i < stepIndex;
          const isActive   = i === stepIndex && !done;
          return (
            <div key={step.label} className="flex items-center gap-3">
              {/* Status dot */}
              <span className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center border transition-all duration-500 ${
                isComplete ? 'bg-[#8b5cf6]/30 border-[#8b5cf6]/60' :
                isActive   ? 'bg-[#8b5cf6]/15 border-[#8b5cf6]/40' :
                             'bg-white/3 border-white/10'
              }`}>
                {isComplete && <CheckCircle2 size={12} className="text-[#a78bfa]" />}
                {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6] animate-pulse" />}
              </span>

              <span className={`text-sm transition-colors duration-500 ${
                isComplete ? 'text-white/50 line-through decoration-white/20' :
                isActive   ? 'text-white/90' :
                             'text-white/25'
              }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-sm">
        <div className="flex justify-between text-xs text-white/30 mb-2">
          <span>Processing</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#7c3aed] to-[#f97316] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <p className="text-white/25 text-xs">
        {done ? 'Dataset ready!' : 'Analyzing your data…'}
      </p>
    </div>
  );
}
