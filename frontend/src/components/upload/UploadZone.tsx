import { useCallback, useRef, useState } from 'react';
import { UploadCloud, FolderOpen } from 'lucide-react';

const ACCEPTED = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json'];
const ACCEPTED_EXT = ['.csv', '.xlsx', '.json'];
const MAX_BYTES = 50 * 1024 * 1024; // 50 MB

interface Props {
  onFile: (file: File, error?: string) => void;
}

export function UploadZone({ onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const validate = useCallback((file: File): string | null => {
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!ACCEPTED_EXT.includes(ext)) return `Unsupported format "${ext}". Please use CSV, XLSX, or JSON.`;
    if (file.size === 0) return 'The file appears to be empty.';
    if (file.size > MAX_BYTES) return `File exceeds 50 MB limit (${(file.size / 1024 / 1024).toFixed(1)} MB).`;
    return null;
  }, []);

  const handle = useCallback((file: File) => {
    const err = validate(file);
    onFile(file, err ?? undefined);
  }, [validate, onFile]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handle(file);
  }, [handle]);

  const onInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handle(file);
    e.target.value = '';
  }, [handle]);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      aria-label="Drop your dataset here or click to browse"
      className={`
        group relative w-full rounded-2xl border-2 border-dashed
        flex flex-col items-center justify-center gap-5
        py-16 px-8 cursor-pointer select-none
        transition-all duration-300
        ${dragging
          ? 'border-[#8b5cf6] bg-[#8b5cf6]/8 shadow-[0_0_32px_rgba(139,92,246,0.25)]'
          : 'border-white/10 bg-white/[0.03] hover:border-[#8b5cf6]/50 hover:bg-[#8b5cf6]/5 hover:shadow-[0_0_24px_rgba(139,92,246,0.12)]'}
      `}
    >
      {/* Gradient corner accents */}
      <span className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-[#8b5cf6]/40 rounded-tl-2xl pointer-events-none" />
      <span className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-[#f97316]/40 rounded-tr-2xl pointer-events-none" />
      <span className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-[#f97316]/40 rounded-bl-2xl pointer-events-none" />
      <span className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-[#8b5cf6]/40 rounded-br-2xl pointer-events-none" />

      {/* Icon */}
      <div className={`
        w-20 h-20 rounded-2xl flex items-center justify-center
        bg-gradient-to-br from-[#7c3aed]/20 to-[#f97316]/10
        border border-white/8 transition-transform duration-300
        ${dragging ? 'scale-110' : 'group-hover:scale-105'}
      `}>
        <UploadCloud
          size={34}
          strokeWidth={1.4}
          className={`transition-colors duration-300 ${dragging ? 'text-[#a78bfa]' : 'text-white/40 group-hover:text-[#8b5cf6]'}`}
        />
      </div>

      {/* Text */}
      <div className="text-center">
        <p className="text-white/80 text-lg font-medium mb-1">
          {dragging ? 'Release to upload' : 'Drop your dataset here'}
        </p>
        <p className="text-white/30 text-sm mb-4">or</p>
        <span className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-white/10 bg-white/5 text-white/60 text-sm hover:text-white hover:bg-white/8 transition-all">
          <FolderOpen size={15} />
          Browse files
        </span>
      </div>

      {/* Formats */}
      <div className="flex items-center gap-2 mt-2">
        {['CSV', 'XLSX', 'JSON'].map((fmt) => (
          <span key={fmt} className="px-2.5 py-0.5 rounded-full bg-white/5 border border-white/8 text-white/35 text-xs font-mono tracking-wider">
            {fmt}
          </span>
        ))}
      </div>

      <p className="text-white/20 text-xs">Max 50 MB</p>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(',') + ',' + ACCEPTED_EXT.join(',')}
        className="sr-only"
        onChange={onInput}
        tabIndex={-1}
      />
    </div>
  );
}
