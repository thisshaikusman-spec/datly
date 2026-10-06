import { X, FileSpreadsheet, Braces, FileText, AlertCircle } from 'lucide-react';

export interface AttachedFile {
  kind: 'file';
  file: File;
  error?: string;
}

export type Attachment = AttachedFile;

// ─── Validation ────────────────────────────────────────────────────────────────
const MAX_FILE  = 50 * 1024 * 1024;  // 50 MB
const FILE_EXTS  = ['.csv', '.xlsx', '.json'];

export function validateFile(file: File): string | undefined {
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!FILE_EXTS.includes(ext))  return `Unsupported format "${ext}". Use CSV, XLSX or JSON.`;
  if (file.size === 0)           return 'The file is empty.';
  if (file.size > MAX_FILE)      return `Exceeds 50 MB limit (${(file.size / 1024 / 1024).toFixed(1)} MB).`;
}


function formatBytes(n: number) {
  if (n < 1024)        return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}

const EXT_ICON: Record<string, React.ReactNode> = {
  CSV:  <FileSpreadsheet size={14} className="text-[#4ade80]" />,
  XLSX: <FileSpreadsheet size={14} className="text-[#60a5fa]" />,
  JSON: <Braces          size={14} className="text-[#fb923c]" />,
};
const EXT_COLORS: Record<string, string> = {
  CSV:  'from-[#22c55e]/15 to-[#16a34a]/8 border-[#22c55e]/20',
  XLSX: 'from-[#3b82f6]/15 to-[#1d4ed8]/8 border-[#3b82f6]/20',
  JSON: 'from-[#f97316]/15 to-[#c2410c]/8 border-[#f97316]/20',
};

interface Props {
  attachment: Attachment;
  onRemove: () => void;
}

export function AttachmentPreview({ attachment, onRemove }: Props) {

  const ext = attachment.file.name.slice(attachment.file.name.lastIndexOf('.') + 1).toUpperCase();
  const colors = EXT_COLORS[ext] ?? 'from-[#8b5cf6]/15 to-[#7c3aed]/8 border-[#8b5cf6]/20';
  const icon   = EXT_ICON[ext]  ?? <FileText size={14} className="text-[#a78bfa]" />;

  return (
    <div className="flex flex-col gap-1">
      <div className={`inline-flex items-center gap-2.5 pr-2 pl-3 py-1.5 rounded-xl bg-gradient-to-r ${colors} border max-w-[240px]`}>
        <span className="shrink-0">{icon}</span>
        <div className="min-w-0 flex-1">
          <p className="text-white/80 text-xs font-medium truncate">{attachment.file.name}</p>
          <p className="text-white/35 text-[10px]">{formatBytes(attachment.file.size)}</p>
        </div>
        <button
          onClick={onRemove}
          aria-label="Remove file"
          className="shrink-0 w-4 h-4 text-white/30 hover:text-white/70 transition-colors"
        >
          <X size={12} strokeWidth={2.5} />
        </button>
      </div>
      {attachment.error && (
        <p className="text-red-400 text-xs flex items-center gap-1">
          <AlertCircle size={11} /> {attachment.error}
        </p>
      )}
    </div>
  );
}
