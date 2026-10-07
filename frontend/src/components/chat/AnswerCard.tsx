import { useState, useRef, useEffect } from 'react';
import { Volume2, Pause } from 'lucide-react';
import type { AnalysisResponse, ClarificationOption } from '../../services/api';
import { playSpeech, stopAudio, primeAudio } from '../../services/audioPlayer';
import { VerificationDetails } from './VerificationDetails';
import { ChartRenderer } from './ChartRenderer';
import { ClarificationCard } from './ClarificationCard';

interface AnswerCardProps {
  analysis: AnalysisResponse;
  audioUrl?: string;            // Optional TTS audio URL from backend
  autoPlay?: boolean;           // Autoplay voice response
  onClarify?: (option: ClarificationOption) => void;
}

export function AnswerCard({ analysis, audioUrl, autoPlay, onClarify }: AnswerCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState<number>(1.25); // Fast, crisp default (1.25x)
  const hasAutoPlayedRef = useRef(false);
  const playedAudioUrlRef = useRef(false);

  const startPlayback = (currentSpeed = speed, targetAudioUrl = audioUrl) => {
    if (!analysis.answer) return;
    primeAudio();
    playSpeech({
      text: analysis.answer,
      audioUrl: targetAudioUrl,
      rate: currentSpeed,
      languageCode: analysis.language_code,
      onStart: () => setIsPlaying(true),
      onEnd: () => setIsPlaying(false)
    });
  };

  const handlePlayPause = () => {
    if (isPlaying) {
      stopAudio();
      setIsPlaying(false);
    } else {
      startPlayback(speed, audioUrl);
    }
  };

  const handleSpeedToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    const nextSpeed = speed === 1.0 ? 1.25 : speed === 1.25 ? 1.5 : 1.0;
    setSpeed(nextSpeed);
    if (isPlaying) {
      startPlayback(nextSpeed, audioUrl);
    }
  };

  // Instant automatic playback on mount when autoPlay is enabled
  useEffect(() => {
    if (autoPlay && !hasAutoPlayedRef.current && analysis.answer) {
      hasAutoPlayedRef.current = true;
      const timer = setTimeout(() => {
        startPlayback(speed, audioUrl);
      }, 80);
      return () => clearTimeout(timer);
    }
  }, [autoPlay, analysis.answer]);

  // When backend TTS audio arrives, play if speech hasn't already started
  useEffect(() => {
    if (autoPlay && audioUrl && !playedAudioUrlRef.current) {
      playedAudioUrlRef.current = true;
      if (!isPlaying) {
        startPlayback(speed, audioUrl);
      }
    }
  }, [audioUrl, autoPlay, isPlaying]);

  // Clean up audio when card unmounts
  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, []);

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
      {/* Answer text + TTS Voice playback controls */}
      <div className="flex items-start gap-3">
        <div className="text-white/90 text-sm leading-relaxed flex-1">
          {analysis.answer}
        </div>

        {/* Voice Playback Pill */}
        <div className="shrink-0 flex items-center gap-1.5 bg-white/4 border border-white/8 rounded-full px-2 py-1 transition-all duration-200">
          <button
            onClick={handlePlayPause}
            title={isPlaying ? 'Pause voice answer' : 'Play answer as speech'}
            className={`flex items-center gap-1.5 text-xs font-medium transition-colors ${
              isPlaying
                ? 'text-[#a78bfa]'
                : 'text-white/40 hover:text-white/80'
            }`}
          >
            {isPlaying ? (
              <>
                <Pause size={12} strokeWidth={2.5} className="text-[#a78bfa]" />
                {/* Animated wave bars */}
                <span className="flex items-end gap-0.5 h-3">
                  <span className="w-0.5 h-3 bg-[#a78bfa] rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-0.5 h-2 bg-[#a78bfa] rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-0.5 h-3.5 bg-[#a78bfa] rounded-full animate-bounce [animation-delay:300ms]" />
                </span>
                <span className="text-[11px] text-[#a78bfa] font-mono">Speaking</span>
              </>
            ) : (
              <>
                <Volume2 size={12} strokeWidth={2} />
                <span className="text-[11px]">Listen</span>
              </>
            )}
          </button>

          {/* Speed Toggle */}
          <button
            onClick={handleSpeedToggle}
            title="Toggle speech playback speed (1x, 1.2x, 1.4x)"
            className="text-[10px] font-mono font-semibold px-1 py-0.5 rounded bg-white/6 text-white/50 hover:text-white/90 hover:bg-white/10 transition-colors ml-0.5"
          >
            {speed}x
          </button>
        </div>
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
