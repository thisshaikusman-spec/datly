/**
 * Audio Player & Speech Synthesis Service
 * Provides rock-solid speech playback and bypasses browser autoplay restrictions.
 * Fixes Chromium garbage-collection bug, audio context priming, and auto-speech playback.
 */

const SILENT_AUDIO_URI = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';

let sharedAudio: HTMLAudioElement | null = null;
let sharedAudioContext: AudioContext | null = null;
let isPrimed = false;
let currentOnEndCallback: (() => void) | null = null;
let activeUtterance: SpeechSynthesisUtterance | null = null;
let resumeTimer: any = null;
let cachedVoices: SpeechSynthesisVoice[] = [];

// Cache available voices as soon as browser loads them
if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  const loadVoices = () => {
    try {
      cachedVoices = window.speechSynthesis.getVoices();
    } catch {}
  };
  loadVoices();
  window.speechSynthesis.onvoiceschanged = loadVoices;
}

/**
 * Prime audio context and HTMLAudioElement during user interactions
 * so subsequent programmatic play calls bypass browser autoplay blocking.
 */
export function primeAudio() {
  if (typeof window === 'undefined') return;

  try {
    // 1. Resume AudioContext if available (strongest browser unlock signal)
    if (!sharedAudioContext) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        sharedAudioContext = new AudioCtx();
      }
    }
    if (sharedAudioContext && sharedAudioContext.state === 'suspended') {
      sharedAudioContext.resume().catch(() => {});
    }

    // 2. Unlock HTMLAudioElement with silent audio
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

    // 3. Resume SpeechSynthesis queue
    if ('speechSynthesis' in window) {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }
    }
  } catch (err) {
    console.debug('[AudioPlayer] Priming error:', err);
  }
}

// Auto-register primeAudio on user interactions across the window
if (typeof window !== 'undefined') {
  const handleInteraction = () => {
    primeAudio();
  };
  window.addEventListener('click', handleInteraction, { passive: true });
  window.addEventListener('keydown', handleInteraction, { passive: true });
  window.addEventListener('touchstart', handleInteraction, { passive: true });
}

export interface PlayOptions {
  text: string;
  audioUrl?: string;
  rate?: number;
  languageCode?: string;
  onStart?: () => void;
  onEnd?: () => void;
}

/**
 * Stop any current speech or audio playback immediately.
 */
export function stopAudio() {
  if (resumeTimer) {
    clearInterval(resumeTimer);
    resumeTimer = null;
  }

  if (activeUtterance) {
    activeUtterance.onstart = null;
    activeUtterance.onend = null;
    activeUtterance.onerror = null;
    activeUtterance = null;
  }

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
 * Check if audio or speech synthesis is currently active.
 */
export function isSpeaking(): boolean {
  const audioPlaying = sharedAudio && !sharedAudio.paused && !sharedAudio.ended;
  const synthSpeaking = typeof window !== 'undefined' && 'speechSynthesis' in window && window.speechSynthesis.speaking;
  return Boolean(audioPlaying || synthSpeaking || activeUtterance);
}

/**
 * Speak text out loud.
 * Prioritizes high-quality Sarvam audioUrl when present; seamlessly uses Web Speech API
 * with anti-garbage-collection retention and zero-latency playback.
 */
export function playSpeech({
  text,
  audioUrl,
  rate = 1.25,
  languageCode,
  onStart,
  onEnd
}: PlayOptions) {
  stopAudio();
  currentOnEndCallback = onEnd || null;

  const handleEnd = () => {
    if (resumeTimer) {
      clearInterval(resumeTimer);
      resumeTimer = null;
    }
    activeUtterance = null;
    const cb = currentOnEndCallback;
    currentOnEndCallback = null;
    cb?.();
  };

  const speakWithWebSpeech = () => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window) || !text) {
      handleEnd();
      return;
    }

    try {
      // Clean text: strip markdown characters, tables, links, and excess whitespace
      const cleanText = text
        .replace(/\|[^\n]+\|/g, '')             // remove markdown tables
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [title](url) -> title
        .replace(/[*_#`~>]/g, ' ')               // remove markdown formatting
        .replace(/\s+/g, ' ')                    // normalize spaces
        .trim();

      if (!cleanText) {
        handleEnd();
        return;
      }

      // Resume synthesis if paused
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }

      // Create new utterance and retain module reference to defeat Chromium GC bug
      const utterance = new SpeechSynthesisUtterance(cleanText);
      activeUtterance = utterance;

      utterance.rate = rate;
      utterance.pitch = 1.0;

      // Detect language from text or options
      const isTamil = /[\u0B80-\u0BFF]/.test(cleanText) || languageCode?.toLowerCase().startsWith('ta');
      const isHindi = /[\u0900-\u097F]/.test(cleanText) || languageCode?.toLowerCase().startsWith('hi');
      const isTelugu = /[\u0C00-\u0C7F]/.test(cleanText) || languageCode?.toLowerCase().startsWith('te');

      // Select most natural voice
      const voices = cachedVoices.length > 0 ? cachedVoices : window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        let preferred: SpeechSynthesisVoice | undefined;
        if (isTamil) {
          preferred = voices.find(v => v.lang.toLowerCase().startsWith('ta'));
        } else if (isHindi) {
          preferred = voices.find(v => v.lang.toLowerCase().startsWith('hi'));
        } else if (isTelugu) {
          preferred = voices.find(v => v.lang.toLowerCase().startsWith('te'));
        }

        if (!preferred) {
          preferred = voices.find(
            v => v.lang.includes('en-IN') || v.name.includes('India') || v.name.includes('Google') || v.lang.startsWith('en')
          );
        }

        if (preferred) {
          utterance.voice = preferred;
          utterance.lang = preferred.lang;
        } else if (isTamil) {
          utterance.lang = 'ta-IN';
        } else if (isHindi) {
          utterance.lang = 'hi-IN';
        } else if (isTelugu) {
          utterance.lang = 'te-IN';
        }
      }

      utterance.onstart = () => {
        onStart?.();
        // Prevent Chromium 14-second speech pause bug
        if (resumeTimer) clearInterval(resumeTimer);
        resumeTimer = setInterval(() => {
          if (typeof window !== 'undefined' && 'speechSynthesis' in window && window.speechSynthesis.speaking) {
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
          } else {
            if (resumeTimer) {
              clearInterval(resumeTimer);
              resumeTimer = null;
            }
          }
        }, 8000);
      };

      utterance.onend = () => {
        handleEnd();
      };

      utterance.onerror = (e) => {
        if (e.error !== 'interrupted' && e.error !== 'canceled') {
          console.warn('[AudioPlayer] Web Speech error:', e.error);
        }
        handleEnd();
      };

      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn('[AudioPlayer] Web Speech exception:', err);
      handleEnd();
    }
  };

  // If a high-fidelity backend audio URL is provided, try playing it first
  if (audioUrl) {
    try {
      if (!sharedAudio) {
        sharedAudio = new Audio();
      }
      sharedAudio.src = audioUrl;
      sharedAudio.playbackRate = rate;

      sharedAudio.onplay = () => {
        onStart?.();
      };

      sharedAudio.onended = () => {
        handleEnd();
      };

      sharedAudio.onerror = () => {
        console.warn('[AudioPlayer] Audio URL error, falling back to Web Speech.');
        speakWithWebSpeech();
      };

      const playPromise = sharedAudio.play();
      if (playPromise) {
        playPromise
          .then(() => {
            onStart?.();
          })
          .catch(err => {
            console.warn('[AudioPlayer] Audio URL play blocked/failed, falling back to Web Speech:', err);
            speakWithWebSpeech();
          });
      }
    } catch {
      speakWithWebSpeech();
    }
  } else {
    // Instant zero-latency speech synthesis
    speakWithWebSpeech();
  }
}
