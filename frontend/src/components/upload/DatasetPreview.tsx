import { useEffect, useState } from 'react';
import { CheckCircle2, ArrowRight, Table2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface DatasetMeta {
  id?: string;
  name: string;
  ext: string;
  rows: number;
  cols: number;
  columns: string[];
  preview: Record<string, string | number>[];
}

interface Props {
  meta: DatasetMeta;
}


export function DatasetPreview({ meta }: Props) {
  const navigate = useNavigate();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className={`w-full space-y-6 transition-all duration-700 ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
      {/* Success header */}
      <div className="flex flex-col items-center gap-3 py-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#7c3aed]/30 to-[#f97316]/20 border border-[#8b5cf6]/30 flex items-center justify-center shadow-[0_0_24px_rgba(139,92,246,0.2)]">
          <CheckCircle2 size={28} className="text-[#a78bfa]" strokeWidth={1.5} />
        </div>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-white/95 mb-1">Dataset ready</h2>
          <p className="text-white/40 text-sm font-mono">{meta.name}</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Rows',    value: meta.rows.toLocaleString() },
          { label: 'Columns', value: meta.cols.toString() },
          { label: 'Format',  value: meta.ext },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-xl border border-white/8 bg-white/[0.03] px-4 py-3 text-center">
            <p className="text-2xl font-semibold text-white/90">{value}</p>
            <p className="text-xs text-white/35 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Column chips */}
      <div>
        <p className="text-xs text-white/35 uppercase tracking-widest font-mono mb-2 flex items-center gap-2">
          <Table2 size={11} /> Columns detected
        </p>
        <div className="flex flex-wrap gap-1.5">
          {meta.columns.map((col) => (
            <span key={col} className="px-2.5 py-1 rounded-lg bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 text-[#a78bfa] text-xs font-mono truncate max-w-[160px]">
              {col}
            </span>
          ))}
        </div>
      </div>

      {/* Preview table */}
      {meta.preview.length > 0 && (
        <div>
          <p className="text-xs text-white/35 uppercase tracking-widest font-mono mb-2">Preview (first {meta.preview.length} rows)</p>
          <div className="w-full overflow-x-auto rounded-xl border border-white/8">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-white/8 bg-white/[0.03]">
                  {meta.columns.map((col) => (
                    <th key={col} className="px-3 py-2.5 text-white/50 font-mono font-medium whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {meta.preview.map((row, ri) => (
                  <tr key={ri} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
                    {meta.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-white/60 whitespace-nowrap font-mono truncate max-w-[180px]">
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CTA */}
      <button
        id="dataset-go-to-workspace"
        onClick={() => navigate('/chat', { state: { dataset: meta } })}
        className="w-full flex items-center justify-center gap-2
          bg-gradient-to-r from-[#7c3aed] to-[#a855f7]
          hover:from-[#6d28d9] hover:to-[#9333ea]
          text-white font-medium rounded-2xl py-4 text-base
          shadow-[0_0_24px_rgba(139,92,246,0.3)]
          hover:shadow-[0_0_36px_rgba(139,92,246,0.45)]
          transition-all duration-200 hover:scale-[1.01]"
      >
        Continue to Dataset
        <ArrowRight size={18} />
      </button>
    </div>
  );
}
