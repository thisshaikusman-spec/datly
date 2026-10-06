import type { VerificationDetails as TVerificationDetails } from '../../services/api';
import { ShieldCheck, ChevronDown, ChevronUp, Database, GitMerge, Filter, Rows } from 'lucide-react';
import { useState } from 'react';

export function VerificationDetails({ details }: { details: TVerificationDetails }) {
  const [open, setOpen] = useState(false);

  const datasets = details.datasets_used && details.datasets_used.length > 0
    ? details.datasets_used
    : (details.dataset ? [details.dataset] : []);

  const joins = details.joins || [];
  const filters = details.filters_applied || [];

  return (
    <div className="flex flex-col gap-2 mt-2 pt-4 border-t border-white/10">
      <button 
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full group"
      >
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-[#a78bfa]" />
          <span className="text-xs text-[#a78bfa]/80 uppercase tracking-wider font-semibold">Verified Analysis</span>
          {datasets.length > 0 && (
            <span className="text-[10px] bg-[#a78bfa]/10 text-[#a78bfa] border border-[#a78bfa]/20 px-1.5 py-0.5 rounded font-mono">
              {datasets.join(', ')}
            </span>
          )}
        </div>
        <div className="text-white/40 group-hover:text-white/70 transition-colors">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {open && (
        <div className="mt-2 flex flex-col gap-2 text-xs">
          {/* Datasets Used */}
          {datasets.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex items-center gap-2">
              <Database size={13} className="text-[#a78bfa] shrink-0" />
              <span className="text-white/40 shrink-0">Datasets:</span>
              <div className="flex flex-wrap gap-1">
                {datasets.map(d => (
                  <span key={d} className="bg-white/10 text-white/90 px-1.5 py-0.5 rounded font-mono text-[11px]">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Joins */}
          {joins.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-white/40 mb-0.5">
                <GitMerge size={13} className="text-[#a78bfa] shrink-0" />
                <span>Joins:</span>
              </div>
              {joins.map((j, idx) => (
                <div key={idx} className="text-white/80 font-mono text-[11px] bg-black/30 px-2 py-1 rounded">
                  <span className="text-[#a78bfa]">{j.left}</span>.{j.left_on} = <span className="text-[#a78bfa]">{j.right}</span>.{j.right_on}
                  {j.how && <span className="text-white/40 ml-1.5 font-sans">({j.how})</span>}
                </div>
              ))}
            </div>
          )}

          {/* Filters */}
          {filters.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-white/40 mb-0.5">
                <Filter size={13} className="text-[#a78bfa] shrink-0" />
                <span>Filters Applied:</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {filters.map((f: any, idx: number) => (
                  <span key={idx} className="bg-black/30 text-white/80 font-mono text-[11px] px-2 py-0.5 rounded">
                    {typeof f === 'object' ? `${f.column || ''} ${f.operator || ''} ${f.value ?? ''}` : String(f)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Row Counts */}
          {(details.row_count_before !== undefined || details.row_count_after !== undefined) && (
            <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex items-center justify-between">
              <div className="flex items-center gap-2 text-white/40">
                <Rows size={13} className="text-[#a78bfa] shrink-0" />
                <span>Row Count:</span>
              </div>
              <div className="text-white/80 font-mono text-[11px]">
                {details.row_count_before !== undefined && (
                  <span>Before: {details.row_count_before.toLocaleString()}</span>
                )}
                {details.row_count_before !== undefined && details.row_count_after !== undefined && (
                  <span className="text-white/40 mx-1.5">→</span>
                )}
                {details.row_count_after !== undefined && (
                  <span className="text-[#34d399]">After: {details.row_count_after.toLocaleString()}</span>
                )}
              </div>
            </div>
          )}

          {/* Grid for standard ops */}
          <div className="grid grid-cols-2 gap-2">
            {details.operation && (
              <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <span className="text-white/40 block mb-0.5">Operation</span>
                <span className="text-white/80 font-mono capitalize">{details.operation.replace(/_/g, ' ')}</span>
              </div>
            )}
            {details.group_column && (
              <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <span className="text-white/40 block mb-0.5">Grouped By</span>
                <span className="text-white/80 font-mono capitalize">{details.group_column}</span>
              </div>
            )}
            {details.metric_column && (
              <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <span className="text-white/40 block mb-0.5">Metric</span>
                <span className="text-white/80 font-mono capitalize">{details.metric_column}</span>
              </div>
            )}
            {details.aggregation && (
              <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <span className="text-white/40 block mb-0.5">Aggregation</span>
                <span className="text-white/80 font-mono capitalize">{details.aggregation}</span>
              </div>
            )}
            {details.sort && (
              <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <span className="text-white/40 block mb-0.5">Sort</span>
                <span className="text-white/80 font-mono capitalize">{details.sort === 'desc' ? 'Highest first' : 'Lowest first'}</span>
              </div>
            )}
            {details.limit && (
              <div className="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <span className="text-white/40 block mb-0.5">Limit</span>
                <span className="text-white/80 font-mono">{details.limit}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
