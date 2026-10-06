import type { ClarificationOption } from '../../services/api';
import { HelpCircle } from 'lucide-react';

interface ClarificationCardProps {
  prompt: string;
  options: ClarificationOption[];
  onSelect: (option: ClarificationOption) => void;
}

export function ClarificationCard({ prompt, options, onSelect }: ClarificationCardProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3">
        <HelpCircle className="w-5 h-5 text-[#a78bfa] mt-0.5 flex-shrink-0" />
        <p className="text-white/90 text-sm">{prompt}</p>
      </div>
      <div className="flex flex-col gap-2 pl-8">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onSelect(option)}
            className="text-left bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 rounded-lg px-4 py-3 text-sm text-white/80 transition-colors w-full"
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
