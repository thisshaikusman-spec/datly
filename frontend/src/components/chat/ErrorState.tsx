import { AlertTriangle } from 'lucide-react';

export function ErrorState({ message, onRetry }: { message: string, onRetry?: () => void }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 text-red-400">
        <AlertTriangle size={16} />
        <span className="text-sm">{message}</span>
      </div>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="self-start px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-300 rounded-lg text-xs font-medium transition-colors border border-red-500/20"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
