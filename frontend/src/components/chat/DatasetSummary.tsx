import type { Dataset } from '../../lib/datasetParser';
import { CheckCircle2, FileSpreadsheet } from 'lucide-react';

export function DatasetSummary({ dataset }: { dataset: Dataset }) {
  return (
    <div className="flex flex-col gap-3 py-1">
      <div className="flex items-center gap-2">
         <CheckCircle2 size={16} className="text-[#a78bfa]" />
         <span className="text-white/90 font-medium tracking-wide">Dataset understood</span>
      </div>
      
      <div className="flex items-center gap-4 bg-white/4 border border-white/5 rounded-xl px-4 py-3">
        <div className="shrink-0 w-10 h-10 rounded-lg bg-[#8b5cf6]/15 border border-[#8b5cf6]/20 flex items-center justify-center">
          <FileSpreadsheet size={18} className="text-[#a78bfa]" />
        </div>
        <div className="min-w-0 flex-1">
           <p className="text-white/90 text-sm font-medium truncate">{dataset.name}</p>
           <p className="text-white/40 text-xs mt-0.5">
             {dataset.rows.toLocaleString()} rows · {dataset.columns} columns · {dataset.fileType}
           </p>
        </div>
      </div>
    </div>
  );
}
