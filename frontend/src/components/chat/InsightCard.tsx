import { Lightbulb } from 'lucide-react';

export function InsightCard({ insight }: { insight: string }) {
  return (
    <div className="bg-gradient-to-r from-[#a78bfa]/10 to-transparent border border-[#a78bfa]/20 rounded-xl p-4 mt-6 flex items-start gap-3">
      <Lightbulb className="text-[#a78bfa] w-5 h-5 flex-shrink-0 mt-0.5" />
      <div>
        <h4 className="text-[#a78bfa] text-xs font-semibold uppercase tracking-wider mb-1">Key Insight</h4>
        <p className="text-white/80 text-sm leading-relaxed">{insight}</p>
      </div>
    </div>
  );
}
