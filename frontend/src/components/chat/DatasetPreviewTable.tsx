import type { Dataset } from '../../lib/datasetParser';

export function DatasetPreviewTable({ dataset }: { dataset: Dataset }) {
  if (!dataset.preview || dataset.preview.length === 0) return null;
  
  const columns = dataset.schema.map(c => c.name);

  return (
    <div className="flex flex-col gap-2 mt-4">
      <h3 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-1">Preview</h3>
      <div className="w-full overflow-x-auto rounded-xl border border-white/10 bg-white/[0.02] scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.03]">
              {columns.map(col => (
                <th key={col} className="px-3 py-2 font-mono font-medium text-white/40 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {dataset.preview.slice(0, 3).map((row, i) => (
              <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                {columns.map(col => (
                  <td key={col} className="px-3 py-2 text-white/70 font-mono text-[11px] whitespace-nowrap truncate max-w-[150px]">
                    {String(row[col] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
