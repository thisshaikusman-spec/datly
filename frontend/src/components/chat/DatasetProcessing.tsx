import { useEffect, useState } from 'react';
import { CheckCircle2, Circle } from 'lucide-react';

const STEPS = [
  { label: 'Reading dataset',          duration: 500 },
  { label: 'Detecting columns',        duration: 700 },
  { label: 'Identifying data types',   duration: 600 },
  { label: 'Understanding column roles', duration: 800 },
  { label: 'Profiling dataset',        duration: 600 },
  { label: 'Dataset ready',            duration: 400 },
];

interface Props {
  filename: string;
}

export function DatasetProcessing({ filename }: Props) {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    let cancelled = false;
    
    const advance = (idx: number) => {
      if (cancelled || idx >= STEPS.length - 1) return;
      setTimeout(() => {
        if (!cancelled) {
          setStepIndex(idx + 1);
          advance(idx + 1);
        }
      }, STEPS[idx].duration);
    };

    advance(0);
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="flex flex-col gap-4 font-sans py-1">
      <div className="flex items-center gap-2 mb-1">
         <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6] animate-pulse" />
         <span className="text-white/80 font-medium tracking-wide">Understanding {filename}</span>
      </div>

      <div className="flex flex-col gap-2.5">
        {STEPS.map((step, i) => {
          const isComplete = i < stepIndex;
          const isPending  = i > stepIndex;

          if (isPending) {
             return (
               <div key={step.label} className="flex items-center gap-2.5 opacity-30">
                 <Circle size={14} className="text-white/40" />
                 <span className="text-sm text-white/50">{step.label}</span>
               </div>
             );
          }

          if (isComplete) {
             return (
               <div key={step.label} className="flex items-center gap-2.5">
                 <CheckCircle2 size={14} className="text-[#a78bfa]" />
                 <span className="text-sm text-white/60">{step.label}</span>
               </div>
             );
          }

          // Active
          return (
             <div key={step.label} className="flex items-center gap-2.5">
               <div className="w-3.5 h-3.5 flex items-center justify-center shrink-0">
                  <div className="w-2 h-2 rounded-full bg-[#8b5cf6] animate-pulse" />
               </div>
               <span className="text-sm text-white/90">{step.label}</span>
             </div>
          );
        })}
      </div>
    </div>
  );
}
