import { useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

export function FloatingChatButton() {
  const navigate = useNavigate();

  return (
    <>
      <style>{`
        @keyframes glow-pulse {
          0%, 100% { box-shadow: 0 0 14px 2px rgba(139,92,246,0.4), 0 0 28px 6px rgba(251,146,60,0.15); }
          50%       { box-shadow: 0 0 22px 6px rgba(139,92,246,0.6), 0 0 40px 12px rgba(251,146,60,0.25); }
        }
        .chat-fab {
          animation: glow-pulse 3s ease-in-out infinite;
          transition: transform 0.22s cubic-bezier(.34,1.56,.64,1), box-shadow 0.22s ease;
        }
        .chat-fab:hover {
          transform: scale(1.12);
          box-shadow: 0 0 0 2px rgba(139,92,246,0.5), 0 0 0 4px rgba(251,146,60,0.3), 0 0 30px 8px rgba(139,92,246,0.5);
          animation: none;
        }
      `}</style>

      <button
        id="datly-chat-fab"
        onClick={() => navigate('/chat')}
        aria-label="Open DATLY AI chat"
        className="chat-fab fixed bottom-7 right-7 z-50 w-14 h-14 rounded-2xl
          flex items-center justify-center cursor-pointer select-none
          bg-gradient-to-br from-[#7c3aed] via-[#8b5cf6] to-[#f97316]"
      >
        <Sparkles size={22} className="text-white" strokeWidth={1.8} />
      </button>
    </>
  );
}
