import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

export function Hero() {
  const navigate = useNavigate();

  const goToChat = () => navigate('/chat');

  return (
    <div className="flex flex-col items-center justify-center pt-28 pb-24 px-6 text-center z-10 relative w-full">
      {/* Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 text-white/70 text-xs font-mono tracking-wider mb-10 shadow-sm">
        <span className="w-2 h-2 rounded-full bg-[#8b5cf6] animate-pulse"></span>
        AI-POWERED DATA ANALYST
      </div>

      {/* Headline */}
      <h1 className="text-5xl md:text-7xl font-semibold tracking-tight text-[#f3f2ee] max-w-4xl mx-auto leading-[1.1] mb-6">
        Your data has answers.<br />
        <span className="font-serif italic font-light text-white/80 pr-2">Just ask.</span>
      </h1>

      {/* Description */}
      <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto leading-relaxed font-light mb-12">
        DATLY turns your CSV, Excel and JSON data into answers, visualizations and insights through natural language.
      </p>

      {/* ── Large Chatbox CTA ── */}
      <style>{`
        @keyframes border-glow {
          0%, 100% { opacity: 0.5; }
          50%       { opacity: 1; }
        }
        .chatbox-cta {
          transition: transform 0.22s cubic-bezier(.34,1.56,.64,1), box-shadow 0.22s ease;
        }
        .chatbox-cta:hover {
          transform: translateY(-2px) scale(1.012);
          box-shadow:
            0 0 0 1px rgba(139,92,246,0.55),
            0 0 24px 4px rgba(139,92,246,0.22),
            0 0 40px 8px rgba(249,115,22,0.1);
        }
        .chatbox-cta:hover .chatbox-border-glow {
          opacity: 1;
        }
        .chatbox-border-glow {
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        .send-btn {
          transition: background 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
        }
        .chatbox-cta:hover .send-btn {
          background: linear-gradient(135deg, #7c3aed, #f97316);
          box-shadow: 0 0 14px rgba(139,92,246,0.5);
          transform: scale(1.08);
        }
      `}</style>

      <div className="w-full max-w-[720px] px-2">
        {/* Gradient glow border layer */}
        <div className="relative">
          {/* Outer glow ring (always subtle, brightens on hover) */}
          <div
            className="chatbox-border-glow absolute -inset-[1.5px] rounded-2xl pointer-events-none z-0"
            style={{
              background: 'linear-gradient(135deg, #7c3aed 0%, #8b5cf6 45%, #f97316 100%)',
              borderRadius: '1rem',
            }}
          />

          {/* Clickable chatbox */}
          <button
            id="hero-chatbox-cta"
            onClick={goToChat}
            aria-label="Open DATLY chat"
            className="chatbox-cta relative z-10 w-full flex items-center gap-4
              bg-[#1a1a1a]/90 backdrop-blur-md
              border border-white/10
              rounded-2xl px-6 h-[68px] cursor-pointer text-left
              shadow-[0_4px_32px_rgba(0,0,0,0.4)]"
            style={{ boxShadow: '0 0 0 1px rgba(255,255,255,0.06), 0 4px 32px rgba(0,0,0,0.4)' }}
          >
            {/* Placeholder text */}
            <span className="flex-1 text-white/30 text-base md:text-lg font-light select-none truncate">
              Find insights. Just ask…
            </span>

            {/* Send arrow */}
            <span
              className="send-btn shrink-0 w-9 h-9 rounded-xl
                flex items-center justify-center
                bg-white/8 border border-white/10"
            >
              <ArrowRight size={17} className="text-white/60" strokeWidth={2} />
            </span>
          </button>
        </div>

        <p className="text-white/20 text-xs mt-3 text-center">
          Click to open the AI data analyst
        </p>
      </div>
    </div>
  );
}
