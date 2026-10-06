import type { DatasetProfile } from '../../lib/datasetParser';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

export function DataQuality({ profile }: { profile: DatasetProfile }) {
  const hasIssues = profile.missingPercentage > 0 || profile.duplicatePercentage > 0;

  return (
    <div className="flex flex-col gap-2 mt-4">
      <h3 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-1">Data Quality</h3>
      
      {!hasIssues ? (
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-[#22c55e]/20 bg-[#22c55e]/5">
          <CheckCircle2 size={14} className="text-[#4ade80]" />
          <span className="text-xs text-[#4ade80]/90">No critical issues</span>
        </div>
      ) : (
        <div className="flex gap-3">
          {profile.missingPercentage > 0 && (
             <div className="flex-1 flex flex-col gap-1 px-3 py-2.5 rounded-xl border border-orange-500/20 bg-orange-500/5">
                <div className="flex items-center gap-1.5">
                   <AlertTriangle size={12} className="text-orange-400" />
                   <span className="text-[11px] text-orange-400/80 uppercase font-semibold">Missing values</span>
                </div>
                <span className="text-sm font-medium text-orange-300">{(profile.missingPercentage * 100).toFixed(1)}%</span>
             </div>
          )}
          {profile.duplicatePercentage > 0 && (
             <div className="flex-1 flex flex-col gap-1 px-3 py-2.5 rounded-xl border border-blue-500/20 bg-blue-500/5">
                <div className="flex items-center gap-1.5">
                   <AlertTriangle size={12} className="text-blue-400" />
                   <span className="text-[11px] text-blue-400/80 uppercase font-semibold">Duplicate rows</span>
                </div>
                <span className="text-sm font-medium text-blue-300">{(profile.duplicatePercentage * 100).toFixed(1)}%</span>
             </div>
          )}
        </div>
      )}
    </div>
  );
}
