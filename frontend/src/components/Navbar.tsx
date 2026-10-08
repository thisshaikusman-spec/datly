import { Link, useLocation } from 'react-router-dom';
import { DatlyLogo } from './DatlyLogo';

export function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="w-full flex items-center justify-between py-6 px-6 md:px-12 max-w-7xl mx-auto z-10 relative">
      {/* Logo */}
      <Link
        to="/"
        className="flex items-center hover:opacity-85 transition-opacity"
        aria-label="DATLY Home"
      >
        <DatlyLogo size="sm" reducedMotion={true} />
      </Link>

      {/* Nav links — centered */}
      <div className="hidden md:flex items-center gap-8 text-sm text-white/70 font-medium absolute left-1/2 -translate-x-1/2">
        <Link to="/" className={`hover:text-white transition-colors ${pathname === '/' ? 'text-white' : ''}`}>
          Home
        </Link>
        <Link to="/chat" className={`hover:text-white transition-colors ${pathname === '/chat' ? 'text-white' : ''}`}>
          Chat
        </Link>
      </div>

      {/* Action link */}
      <div className="flex items-center gap-3">
        <Link
          to="/chat"
          className="text-xs sm:text-sm font-medium px-4 py-1.5 rounded-full bg-white/10 hover:bg-white/15 text-white border border-white/10 transition-colors"
        >
          Open App
        </Link>
      </div>
    </nav>
  );
}
