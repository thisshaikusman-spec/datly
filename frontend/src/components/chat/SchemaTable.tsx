import type { ColumnSchema } from '../../lib/datasetParser';

export function SchemaTable({ schema }: { schema: ColumnSchema[] }) {
  const getRoleColor = (role: string) => {
    switch (role) {
      case 'ID':       return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
      case 'Text':     return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      case 'Category': return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
      case 'Numeric':  return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
      case 'Date':     return 'text-green-400 bg-green-400/10 border-green-400/20';
      default:         return 'text-white/60 bg-white/5 border-white/10';
    }
  };

  return (
    <div className="flex flex-col gap-2 mt-4">
      <h3 className="text-xs text-white/50 uppercase tracking-wider font-semibold mb-1">Schema detected</h3>
      <div className="w-full overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.02]">
              <th className="px-3 py-2 font-medium text-white/50 w-1/3">Column</th>
              <th className="px-3 py-2 font-medium text-white/50 w-1/3">Data Type</th>
              <th className="px-3 py-2 font-medium text-white/50 w-1/3">Semantic Role</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {schema.map(col => (
              <tr key={col.name} className="hover:bg-white/[0.02] transition-colors">
                <td className="px-3 py-2 text-white/80 font-mono text-[11px]">{col.name}</td>
                <td className="px-3 py-2 text-white/60">{col.dataType}</td>
                <td className="px-3 py-2">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] border ${getRoleColor(col.role)}`}>
                    {col.role}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
