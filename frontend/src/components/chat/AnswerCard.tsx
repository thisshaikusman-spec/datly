import { useState, useRef } from 'react';
import { Volume2, Pause } from 'lucide-react';
import type { AnalysisResponse, ClarificationOption } from '../../services/api';
import { VerificationDetails } from './VerificationDetails';
import { ChartRenderer } from './ChartRenderer';
import { ClarificationCard } from './ClarificationCard';

interface AnswerCardProps {
  analysis: AnalysisResponse;
  audioUrl?: string;            // Optional TTS audio URL from backend
  onClarify?: (option: ClarificationOption) => void;
}

export function AnswerCard({ analysis, audioUrl, onClarify }: AnswerCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlayPause = () => {
    if (!audioUrl) return;

    if (!audioRef.current) {
      audioRef.current = new Audio(audioUrl);
      audioRef.current.onended = () => setIsPlaying(false);
      audioRef.current.onerror = () => setIsPlaying(false);
    }

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(() => setIsPlaying(false));
      setIsPlaying(true);
    }
  };

  if (!analysis.success) {
    return (
      <div className="flex flex-col gap-2">
        <p className="text-red-400">{analysis.answer || analysis.error || 'An error occurred during analysis.'}</p>
      </div>
    );
  }

  if (analysis.clarificationRequired && analysis.clarificationPrompt && analysis.clarificationOptions) {
    return (
      <ClarificationCard
        prompt={analysis.clarificationPrompt}
        options={analysis.clarificationOptions}
        onSelect={onClarify || (() => {})}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Answer text + TTS play button */}
      <div className="flex items-start gap-3">
        <div className="text-white/90 text-sm leading-relaxed flex-1">
          {analysis.answer}
        </div>

        {/* TTS Play / Pause button — only renders when voice audio is available */}
        {audioUrl && (
          <button
            onClick={handlePlayPause}
            title={isPlaying ? 'Pause voice response' : 'Play voice response'}
            className={`shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-200 mt-0.5 ${
              isPlaying
                ? 'text-[#a78bfa] bg-[#a78bfa]/15 ring-1 ring-[#a78bfa]/30'
                : 'text-white/35 hover:text-[#a78bfa] hover:bg-[#a78bfa]/10'
            }`}
          >
            {isPlaying
              ? <Pause size={13} strokeWidth={2.5} />
              : <Volume2 size={13} strokeWidth={2} />
            }
          </button>
        )}
      </div>

      {(analysis.visualizations && analysis.visualizations.length > 0) ? (
        <div className="w-full">
          <ChartRenderer specs={analysis.visualizations} />
        </div>
      ) : analysis.visualization ? (
        <div className="w-full">
          <ChartRenderer spec={analysis.visualization} />
        </div>
      ) : null}

      {analysis.verification && (
        <VerificationDetails details={analysis.verification} />
      )}
    </div>
  );
}
