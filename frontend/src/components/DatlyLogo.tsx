import { useEffect, useState } from 'react';

export interface DatlyLogoProps {
  animate?: boolean;
  reducedMotion?: boolean;
  onAnimationComplete?: () => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function DatlyLogo({
  animate = false,
  reducedMotion = false,
  onAnimationComplete,
  size = 'lg',
  className = ''
}: DatlyLogoProps) {
  // If static or reduced motion, pixels and wordmark are visible immediately
  const isImmediatelyVisible = !animate || reducedMotion;
  const [pixelsVisible, setPixelsVisible] = useState(isImmediatelyVisible);
  const [wordmarkVisible, setWordmarkVisible] = useState(isImmediatelyVisible);

  useEffect(() => {
    if (reducedMotion || !animate) {
      setPixelsVisible(true);
      setWordmarkVisible(true);
      if (onAnimationComplete) {
        onAnimationComplete();
      }
      return;
    }

    // Start pixel animation
    setPixelsVisible(true);
    
    // 14 pixels * 85ms = 1190ms, wait ~1300ms
    const wordmarkTimer = setTimeout(() => {
      setWordmarkVisible(true);
    }, 1300);

    // total time ~2500ms
    const completeTimer = setTimeout(() => {
      if (onAnimationComplete) {
        onAnimationComplete();
      }
    }, 2500);

    return () => {
      clearTimeout(wordmarkTimer);
      clearTimeout(completeTimer);
    };
  }, [animate, reducedMotion, onAnimationComplete]);

  // order of animation for pixels (0 to 13)
  const pixelPositions = [
    { x: 4, y: 0 },
    { x: 4, y: 1 },
    { x: 4, y: 2 },
    { x: 4, y: 3 },
    { x: 4, y: 4 },
    { x: 4, y: 5 },
    { x: 3, y: 5 },
    { x: 2, y: 5 },
    { x: 1, y: 5 },
    { x: 0, y: 4 },
    { x: 0, y: 3 },
    { x: 1, y: 2 },
    { x: 2, y: 2 },
    { x: 3, y: 2 },
  ];

  // Interpolate color based on pos
  const getColor = (x: number, y: number) => {
    const v = (x + (5 - y)) / 9; // 0 to 1
    // Blue: #3b82f6, Violet: #8b5cf6, Pink: #ec4899, Orange: #f97316
    if (v < 0.2) return '#3b82f6';
    if (v < 0.5) return '#8b5cf6';
    if (v < 0.8) return '#ec4899';
    return '#f97316';
  };

  const svgSizeClass = size === 'sm'
    ? 'w-6 h-auto sm:w-7'
    : size === 'md'
    ? 'w-9 h-auto sm:w-10'
    : 'w-[3rem] sm:w-[4rem] md:w-[5rem] h-auto';

  const textSizeClass = size === 'sm'
    ? 'text-xl sm:text-2xl font-semibold tracking-tight'
    : size === 'md'
    ? 'text-3xl sm:text-4xl font-semibold tracking-tight'
    : 'text-5xl sm:text-6xl md:text-7xl font-medium tracking-tighter';

  const gapClass = size === 'sm' ? 'gap-2 sm:gap-2.5' : size === 'md' ? 'gap-3' : 'gap-4';

  return (
    <div className={`flex items-center select-none ${gapClass} ${className}`}>
      <svg
        viewBox="0 0 144 174"
        className={`${svgSizeClass} shrink-0 overflow-visible`}
        aria-hidden="true"
      >
        {pixelPositions.map((pos, i) => {
          const v = (pos.x + (5 - pos.y)) / 9;
          const heatmapOpacity = 0.35 + (v * 0.65);
          
          return (
            <rect
              key={i}
              x={pos.x * 30}
              y={pos.y * 30}
              width={24}
              height={24}
              rx={6}
              fill={getColor(pos.x, pos.y)}
              className="transition-all duration-500 ease-out"
              style={{
                opacity: (pixelsVisible || reducedMotion) ? heatmapOpacity : 0,
                transform: (pixelsVisible || reducedMotion) ? 'scale(1)' : 'scale(0.1)',
                transitionDelay: (!reducedMotion && animate && pixelsVisible) ? `${i * 85}ms` : '0ms',
                transformOrigin: `${pos.x * 30 + 12}px ${pos.y * 30 + 12}px`
              }}
            />
          );
        })}
      </svg>
      <div className={`font-mono flex leading-none ${textSizeClass}`} style={{ color: '#f3f2ee' }}>
        {['d', 'a', 't', 'l', 'y'].map((char, i) => (
          <span
            key={i}
            className="transition-all duration-700 ease-out inline-block"
            style={{
              opacity: (wordmarkVisible || reducedMotion) ? 1 : 0,
              transform: (wordmarkVisible || reducedMotion) ? 'translateY(0) scale(1)' : 'translateY(0.5em) scale(0.6)',
              color: (wordmarkVisible || reducedMotion) ? '#f3f2ee' : '#ec4899', 
              transitionDelay: (!reducedMotion && animate && wordmarkVisible) ? `${i * 100}ms` : '0ms',
            }}
          >
            {char}
          </span>
        ))}
      </div>
    </div>
  );
}
