import { useState, useCallback } from 'react';
import { Navbar } from '../components/Navbar';
import { Hero } from '../components/Hero';
import { ProductPreview } from '../components/ProductPreview';
import { WaveBackground } from '../components/WaveBackground';
import { LogoIntro } from '../components/LogoIntro';

import { RotateCcw } from 'lucide-react';

export function Landing() {
  const [introDone, setIntroDone] = useState(false);
  const [triggerReplay, setTriggerReplay] = useState<{ fn: () => void } | null>(null);

  const handleReplay = () => {
    if (triggerReplay?.fn) {
      setIntroDone(false);
      triggerReplay.fn();
    }
  };

  const handleReplayReady = useCallback((fn: () => void) => {
    setTriggerReplay({ fn });
  }, []);

  return (
    <div className="min-h-screen w-full relative selection:bg-[#8b5cf6]/30 selection:text-white flex flex-col font-sans bg-[#141414] text-white overflow-x-hidden">
      <WaveBackground />

      {!introDone && (
        <div className="fixed inset-0 z-50">
          <LogoIntro
            onComplete={() => setIntroDone(true)}
            onReplayReady={handleReplayReady}
          />
        </div>
      )}

      <div
        className="flex-1 flex flex-col relative transition-opacity duration-1000 z-10 w-full"
        style={{ opacity: introDone ? 1 : 0, pointerEvents: introDone ? 'auto' : 'none' }}
      >
        <Navbar />
        <main className="flex-1 flex flex-col items-center">
          <Hero />
          <ProductPreview />
        </main>

        <footer className="w-full py-8 flex items-center justify-center border-t border-white/5 bg-black/20 mt-16">
          <button
            onClick={handleReplay}
            className="flex items-center gap-2 text-white/40 hover:text-white/80 transition-colors text-sm font-medium px-4 py-2"
          >
            <RotateCcw size={14} />
            Replay Intro
          </button>
        </footer>
      </div>


    </div>
  );
}
