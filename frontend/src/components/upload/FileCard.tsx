import { X, ArrowRight, AlertCircle } from 'lucide-react';

interface Props {
  file: File;
  error?: string;
  onRemove: () => void;
  onContinue: () => void;
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function extLabel(name: string) {
  return name.slice(name.lastIndexOf('.') + 1).toUpperCase();
}

const EXT_COLORS: Record<string, string> = {
  CSV:  'from-[#22c55e]/20 to-[#16a34a]/10 border-[#22c55e]/20 text-[#4ade80]',
  XLSX: 'from-[#3b82f6]/20 to-[#1d4ed8]/10 border-[#3b82f6]/20 text-[#60a5fa]',
  JSON: 'from-[#f97316]/20 to-[#c2410c]/10 border-[#f97316]/20 text-[#fb923c]',
};

export function FileCard({ file, error, onRemove, onContinue }: Props) {
  const ext = extLabel(file.name);
  const colors = EXT_COLORS[ext] ?? 'from-[#8b5cf6]/20 to-[#7c3aed]/10 border-[#8b5cf6]/20 text-[#a78bfa]';

  return (
    <div className="w-full space-y-4">
      {/* File info card */}
      <div className="w-full flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4">
        {/* File type badge */}
        <div className={`shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br ${colors} border flex items-center justify-center`}>
          <span className="font-mono text-sm font-semibold">{ext}</span>
        </div>

        {/* Details */}
        <div className="flex-1 min-w-0">
          <p className="text-white/90 font-medium truncate text-sm">{file.name}</p>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-white/35 text-xs">{ext} file</span>
            <span className="w-1 h-1 rounded-full bg-white/15" />
            <span className="text-white/35 text-xs">{formatBytes(file.size)}</span>
          </div>
        </div>

        {/* Remove */}
        <button
          onClick={onRemove}
          aria-label="Remove file"
          className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center border border-white/8 bg-white/5 text-white/30 hover:text-white/70 hover:border-white/20 transition-all"
        >
          <X size={14} />
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/8 px-4 py-3">
          <AlertCircle size={16} className="text-red-400 shrink-0 mt-0.5" />
          <p className="text-red-300/90 text-sm leading-relaxed">{error}</p>
        </div>
      )}

      {/* Continue button — only if no error */}
      {!error && (
        <button
          id="upload-continue-btn"
          onClick={onContinue}
          className="w-full flex items-center justify-center gap-2
            bg-gradient-to-r from-[#7c3aed] to-[#a855f7]
            hover:from-[#6d28d9] hover:to-[#9333ea]
            text-white font-medium rounded-2xl py-4 text-base
            shadow-[0_0_24px_rgba(139,92,246,0.3)]
            hover:shadow-[0_0_32px_rgba(139,92,246,0.45)]
            transition-all duration-200 hover:scale-[1.01]"
        >
          Continue to processing
          <ArrowRight size={18} />
        </button>
      )}
    </div>
  );
}
