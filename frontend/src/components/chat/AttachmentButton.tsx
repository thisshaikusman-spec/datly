import { useRef } from 'react';
import { Plus } from 'lucide-react';

const FILE_ACCEPT = '.csv,.xlsx,.json,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/json';
interface Props {
  open: boolean;
  onToggle: () => void;
  onFile?: (file: File) => void;
  onFiles?: (files: File[]) => void;
}

export function AttachmentButton({ open, onToggle, onFile, onFiles }: Props) {
  const fileRef  = useRef<HTMLInputElement>(null);

  const pick = (ref: React.RefObject<HTMLInputElement | null>) => {
    onToggle(); // close menu
    ref.current?.click();
  };

  return (
    <div className="relative shrink-0">
      {/* Trigger */}
      <button
        id="attachment-btn"
        onClick={onToggle}
        aria-label="Add attachment"
        aria-expanded={open}
        className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200
          ${open
            ? 'bg-[#8b5cf6]/20 text-[#a78bfa] border border-[#8b5cf6]/40'
            : 'text-white/35 hover:text-white/70 hover:bg-white/6'}`}
      >
        <Plus size={20} strokeWidth={2} className={`transition-transform duration-200 ${open ? 'rotate-45' : ''}`} />
      </button>

      {/* Dropdown menu */}
      {open && (
        <div
          className="absolute bottom-full left-0 mb-2 w-44 rounded-xl border border-white/10 bg-[#1e1e1e] shadow-[0_8px_32px_rgba(0,0,0,0.6)] overflow-hidden z-50"
          role="menu"
        >
          {/* Gradient top edge */}
          <div className="h-px bg-gradient-to-r from-[#7c3aed]/40 via-[#8b5cf6]/60 to-[#f97316]/40" />

          <button
            id="attach-file-btn"
            role="menuitem"
            onClick={() => pick(fileRef)}
            className="w-full flex items-center gap-3 px-4 py-3 text-sm text-white/70 hover:text-white hover:bg-white/5 transition-colors"
          >
            <span className="w-7 h-7 rounded-lg bg-[#8b5cf6]/12 border border-[#8b5cf6]/20 flex items-center justify-center shrink-0">
              <Plus size={14} className="text-[#a78bfa]" />
            </span>
            Add file
          </button>



          <div className="h-px bg-gradient-to-r from-[#f97316]/20 via-transparent to-transparent" />
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept={FILE_ACCEPT}
        multiple
        className="sr-only"
        onChange={e => {
          const files = Array.from(e.target.files || []);
          if (files.length > 0) {
            if (onFiles) {
              onFiles(files);
            } else if (onFile) {
              files.forEach(f => onFile(f));
            }
          }
          e.target.value = '';
        }}
      />
    </div>
  );
}
