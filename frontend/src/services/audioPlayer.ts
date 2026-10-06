/**
 * Audio Player & Speech Synthesis Service
 * Provides zero-latency speech playback and bypasses browser autoplay restrictions
 * by priming the audio context on user interactions (click, Enter, mic).
 */

const SILENT_AUDIO_URI = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';

let sharedAudio: HTMLAudioElement | null = null;
let isPrimed = false;
let currentOnEndCallback: (() => void) | null = null;

/**
 * Prime audio context during a user gesture so subsequent programmatic play calls succeed.
 */
export function primeAudio() {
  if (typeof window === 'undefined') return;

  try {
    if (!sharedAudio) {
      sharedAudio = new Audio();
      sharedAudio.preload = 'auto';
    }

    if (!isPrimed) {
      sharedAudio.src = SILENT_AUDIO_URI;
      const promise = sharedAudio.play();
      if (promise) {
        promise
          .then(() => {
            isPrimed = true;
            if (sharedAudio && sharedAudio.src === SILENT_AUDIO_URI) {
              sharedAudio.pause();
              sharedAudio.currentTime = 0;
            }
          })
          .catch(() => {});
      }
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.resume();
    }
  } catch (err) {
    console.debug('[AudioPlayer] Priming error:', err);
  }
}

// Auto-register primeAudio on first interaction anywhere on page
if (typeof window !== 'undefined') {
  const handleFirstInteraction = () => {
    primeAudio();
  };
  window.addEventListener('click', handleFirstInteraction, { passive: true });
  window.addEventListener('keydown', handleFirstInteraction, { passive: true });
  window.addEventListener('touchstart', handleFirstInteraction, { passive: true });
}

export interface PlayOptions {
  text: string;
  audioUrl?: string;
  rate?: number;
  onStart?: () => void;
  onEnd?: () => void;
}

/**
 * Stop any current speech or audio playback immediately.
 */
export function stopAudio() {
  if (currentOnEndCallback) {
    const cb = currentOnEndCallback;
    currentOnEndCallback = null;
    cb();
  }

  if (sharedAudio) {
    try {
      sharedAudio.pause();
      sharedAudio.currentTime = 0;
      sharedAudio.onended = null;
      sharedAudio.onerror = null;
    } catch {}
  }

  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
    } catch {}
  }
}

/**
 * Speak text out loud.
 * Uses provided audioUrl if valid and working; automatically falls back to Web Speech API
 * with crisp 1.25x speed and zero latency.
 */
export function playSpeech({
  text,
  audioUrl,
  rate = 1.25,
  onStart,
  onEnd
}: PlayOptions) {
  stopAudio();
  currentOnEndCallback = onEnd || null;

  const handleEnd = () => {
    currentOnEndCallback = null;
    onEnd?.();
  };

  const speakWithWebSpeech = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window) || !text) {
      handleEnd();
      return;
    }

    try {
      window.speechSynthesis.cancel();

      // Delay by 40ms to avoid Chromium's cancel() race condition
      setTimeout(() => {
        try {
          window.speechSynthesis.resume();

          // Strip markdown characters (*, _, #, `, etc.) for smooth speech
          const cleanText = text
            .replace(/[*_#`~]/g, '')
            .replace(/\s+/g, ' ')
            .trim();

          if (!cleanText) {
            handleEnd();
            return;
          }

          const utterance = new SpeechSynthesisUtterance(cleanText);
          utterance.rate = rate;
          utterance.pitch = 1.0;

          // Attempt to pick an Indian English or natural voice if available
          const voices = window.speechSynthesis.getVoices();
          if (voices && voices.length > 0) {
            const preferred = voices.find(
              v => v.lang.includes('en-IN') || v.lang.includes('ta') || v.name.includes('India') || v.name.includes('Google')
            );
            if (preferred) {
              utterance.voice = preferred;
            }
          }

          utterance.onstart = () => {
            onStart?.();
          };

          utterance.onend = () => {
            handleEnd();
          };

          utterance.onerror = (e) => {
            // Ignore normal cancel/interrupted events
            if (e.error !== 'interrupted' && e.error !== 'canceled') {
              handleEnd();
            }
          };

          onStart?.();
          window.speechSynthesis.speak(utterance);
        } catch {
          handleEnd();
        }
      }, 40);
    } catch {
      handleEnd();
    }
  };

  // If we have a backend audio URL, attempt to play it first
  if (audioUrl) {
    try {
      if (!sharedAudio) {
        sharedAudio = new Audio();
      }
      sharedAudio.src = audioUrl;
      sharedAudio.playbackRate = rate;

      sharedAudio.onended = () => {
        handleEnd();
      };

      sharedAudio.onerror = () => {
        // Fall back to Web Speech synthesis seamlessly
        speakWithWebSpeech();
      };

      const playPromise = sharedAudio.play();
      if (playPromise) {
        playPromise
          .then(() => {
            onStart?.();
          })
          .catch(() => {
            // Autoplay blocked or media error -> fallback to speech synthesis immediately
            speakWithWebSpeech();
          });
      }
    } catch {
      speakWithWebSpeech();
    }
  } else {
    // Zero latency immediate speech synthesis
    speakWithWebSpeech();
  }
}
