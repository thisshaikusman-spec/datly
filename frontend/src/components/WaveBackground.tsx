import { useEffect, useRef } from 'react';

// ─── Types ────────────────────────────────────────────────────────────────────
interface WaveLine {
  baseY: number;          // original Y center of this wave band
  amplitude: number;      // natural amplitude
  frequency: number;      // horizontal frequency
  phase: number;          // phase offset
  color: string;          // rgb string
  opacity: number;
  lineWidth: number;
  mouseInfluence: number; // 0–1 multiplier of how strongly this line reacts
}

interface Star {
  x: number;
  y: number;
  baseRadius: number;
  sparkle: boolean;       // 4-point cross sparkle vs plain dot
  color: string;          // rgba string (base)
  phase: number;          // twinkle phase offset
  speed: number;          // twinkle speed (radians/ms)
  baseAlpha: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const WAVE_SEGMENTS = 160;        // horizontal sample points per wave line
const INFLUENCE_RADIUS_VW = 0.30; // mouse influence radius = 30% of viewport width
const SPRING = 0.07;              // spring strength (return to origin)
const DAMPING = 0.72;             // velocity damping
const LERP_MOUSE = 0.06;          // mouse smoothing
const STAR_COUNT = 80;

const STAR_COLORS = [
  '200,160,255', // violet
  '139,92,246',  // DATLY purple
  '180,130,255', // light purple
  '240,240,255', // near-white
  '249,150,80',  // warm orange
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function lerp(a: number, b: number, t: number) { return a + (b - a) * t; }

function buildWaveLines(_W: number, H: number): WaveLine[] {
  const lines: WaveLine[] = [];

  // ─ Background tier (3 bands of 6 lines each, very subtle)
  const bgBands = [0.10, 0.30, 0.55, 0.72, 0.88];
  bgBands.forEach((band, bi) => {
    const spread = H * 0.10;
    for (let k = -2; k <= 3; k++) {
      lines.push({
        baseY:  H * band + k * spread * 0.5,
        amplitude: 16 + bi * 4,
        frequency: 0.0038 + bi * 0.0006,
        phase: bi * 1.4 + k * 0.55,
        color: bi % 2 === 0 ? '100,60,210' : '60,80,200',
        opacity: 0.055 + (k === 0 ? 0.015 : 0),
        lineWidth: 0.55,
        mouseInfluence: 0.25,
      });
    }
  });

  // ─ Middle tier (richer purple/violet, slightly more mouse reactive)
  const midBands = [0.20, 0.42, 0.65, 0.82];
  midBands.forEach((band, bi) => {
    const spread = H * 0.08;
    for (let k = -2; k <= 3; k++) {
      lines.push({
        baseY:  H * band + k * spread * 0.55,
        amplitude: 24 + bi * 5,
        frequency: 0.0045 + bi * 0.0005,
        phase: bi * 2.1 + k * 0.7 + 0.9,
        color: bi % 2 === 0 ? '139,80,230' : '90,110,235',
        opacity: 0.08 + (k === 0 ? 0.02 : 0),
        lineWidth: 0.75,
        mouseInfluence: 0.48,
      });
    }
  });

  // ─ Foreground tier (DATLY purple + warm orange, most reactive)
  const fgDefs = [
    { band: 0.18, color: '139,92,246', amp: 36 },
    { band: 0.38, color: '160,90,244', amp: 32 },
    { band: 0.55, color: '200,105,60', amp: 28 },
    { band: 0.70, color: '130,80,240', amp: 34 },
    { band: 0.85, color: '110,130,245', amp: 30 },
  ];
  fgDefs.forEach((def, bi) => {
    const spread = H * 0.065;
    for (let k = -2; k <= 3; k++) {
      lines.push({
        baseY:  H * def.band + k * spread * 0.55,
        amplitude: def.amp,
        frequency: 0.0040 + bi * 0.0004,
        phase: bi * 1.8 + k * 0.8 + 0.4,
        color: def.color,
        opacity: 0.11 + (k === 0 ? 0.025 : 0),
        lineWidth: 0.95,
        mouseInfluence: 0.72,
      });
    }
  });

  return lines;
}

function buildStars(W: number, H: number): Star[] {
  const stars: Star[] = [];
  for (let i = 0; i < STAR_COUNT; i++) {
    const color = STAR_COLORS[Math.floor(Math.random() * STAR_COLORS.length)];
    stars.push({
      x: Math.random() * W,
      y: Math.random() * H,
      baseRadius: 0.4 + Math.random() * 1.8,
      sparkle: Math.random() < 0.25,
      color,
      phase: Math.random() * Math.PI * 2,
      speed: 0.0003 + Math.random() * 0.0008,   // radians/ms — very slow
      baseAlpha: 0.25 + Math.random() * 0.50,
    });
  }
  return stars;
}

// ─── Component ────────────────────────────────────────────────────────────────
export function WaveBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ─ Resize / DPR ───────────────────────────────────────────────────
    let W = 0, H = 0;
    let waveLines: WaveLine[] = [];
    let stars: Star[] = [];

    // Per-point displacement + velocity storage
    // [lineIndex][pointIndex] = { dy, vy }
    type PointState = { dy: number; vy: number };
    let pointStates: PointState[][] = [];

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      canvas.width  = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      waveLines  = buildWaveLines(W, H);
      stars      = buildStars(W, H);

      // Initialise displacement states
      pointStates = waveLines.map(() =>
        Array.from({ length: WAVE_SEGMENTS + 1 }, () => ({ dy: 0, vy: 0 }))
      );
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    // ─ Mouse state ─────────────────────────────────────────────────────
    const rawMouse  = { x: -99999, y: -99999 };
    const smMouse   = { x: -99999, y: -99999 };
    let hasMouseMoved = false;

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      rawMouse.x = e.clientX - rect.left;
      rawMouse.y = e.clientY - rect.top;
      hasMouseMoved = true;
      if (!rafRunning) startRaf();
    };
    const onMouseLeave = () => {
      rawMouse.x = -99999;
      rawMouse.y = -99999;
    };

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('mouseleave', onMouseLeave, { passive: true });

    // ─ Star drawing ────────────────────────────────────────────────────
    const drawStar = (star: Star, alpha: number, brightnessBonus: number) => {
      const a = Math.min(1, alpha + brightnessBonus);
      ctx.save();
      ctx.globalAlpha = a;

      if (star.sparkle) {
        // 4-point cross
        const r = star.baseRadius + brightnessBonus * 3;
        ctx.strokeStyle = `rgba(${star.color},1)`;
        ctx.lineWidth = r * 0.5;
        ctx.beginPath();
        ctx.moveTo(star.x - r * 2.5, star.y);
        ctx.lineTo(star.x + r * 2.5, star.y);
        ctx.moveTo(star.x, star.y - r * 2.5);
        ctx.lineTo(star.x, star.y + r * 2.5);
        ctx.stroke();

        // Small center dot
        ctx.fillStyle = `rgba(${star.color},1)`;
        ctx.beginPath();
        ctx.arc(star.x, star.y, r * 0.6, 0, Math.PI * 2);
        ctx.fill();
      } else {
        // Plain glowing dot
        const grd = ctx.createRadialGradient(star.x, star.y, 0, star.x, star.y, star.baseRadius * 3);
        grd.addColorStop(0,   `rgba(${star.color},1)`);
        grd.addColorStop(0.4, `rgba(${star.color},0.5)`);
        grd.addColorStop(1,   `rgba(${star.color},0)`);
        ctx.fillStyle = grd;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.baseRadius * 3, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    };

    // ─ Wave drawing ────────────────────────────────────────────────────
    const drawWaveLine = (line: WaveLine, states: PointState[]) => {
      ctx.beginPath();
      ctx.lineWidth   = line.lineWidth;
      ctx.strokeStyle = `rgba(${line.color},${line.opacity})`;

      for (let i = 0; i <= WAVE_SEGMENTS; i++) {
        const t = i / WAVE_SEGMENTS;
        const x = t * W;

        // Static shape — cosine curve with phase
        const baseY = line.baseY
          + Math.sin(x * line.frequency + line.phase) * line.amplitude
          + Math.sin(x * line.frequency * 1.65 + line.phase + 1.2) * line.amplitude * 0.3;

        const y = baseY + states[i].dy;

        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
    };

    // ─ Physics update ──────────────────────────────────────────────────
    const influenceRadius = () => W * INFLUENCE_RADIUS_VW;

    const updatePhysics = () => {
      const mx = smMouse.x;
      const my = smMouse.y;
      const R  = influenceRadius();
      const R2 = R * R;

      waveLines.forEach((line, li) => {
        const states = pointStates[li];
        for (let i = 0; i <= WAVE_SEGMENTS; i++) {
          const state = states[i];
          const t = i / WAVE_SEGMENTS;
          const x = t * W;
          const baseY = line.baseY
            + Math.sin(x * line.frequency + line.phase) * line.amplitude
            + Math.sin(x * line.frequency * 1.65 + line.phase + 1.2) * line.amplitude * 0.3;

          let force = 0;

          if (mx > -9999) {
            const dx = x  - mx;
            const dy = (baseY + state.dy) - my;
            const dist2 = dx * dx + dy * dy;
            if (dist2 < R2) {
              const dist = Math.sqrt(dist2);
              const norm = 1 - dist / R;
              const falloff = norm * norm;   // quadratic
              // Push away from mouse
              const pushDir = (baseY + state.dy) < my ? -1 : 1;
              force = pushDir * falloff * 42 * line.mouseInfluence;
            }
          }

          // Spring: pull back to 0 displacement
          const springForce = -state.dy * SPRING;
          state.vy = (state.vy + springForce + force) * DAMPING;
          state.dy += state.vy;

          // Kill micro-vibrations
          if (Math.abs(state.vy) < 0.001 && Math.abs(state.dy) < 0.001) {
            state.dy = 0;
            state.vy = 0;
          }
        }
      });
    };

    const isSettled = () =>
      pointStates.every(line => line.every(s => Math.abs(s.dy) < 0.05 && Math.abs(s.vy) < 0.05));

    // ─ Render loop ─────────────────────────────────────────────────────
    let rafId = 0;
    let rafRunning = false;
    let lastTs = 0;

    const draw = (ts: number) => {
      const dt = ts - lastTs;
      lastTs = ts;

      // Smooth mouse
      if (rawMouse.x > -9999) {
        smMouse.x = lerp(smMouse.x < -9999 ? rawMouse.x : smMouse.x, rawMouse.x, LERP_MOUSE);
        smMouse.y = lerp(smMouse.y < -9999 ? rawMouse.y : smMouse.y, rawMouse.y, LERP_MOUSE);
      } else {
        smMouse.x = -99999;
        smMouse.y = -99999;
      }

      ctx.clearRect(0, 0, W, H);

      // ─ Stars ─
      stars.forEach(star => {
        star.phase += star.speed * dt;
        const twinkle = 0.5 + 0.5 * Math.sin(star.phase);
        const alpha = star.baseAlpha * twinkle;

        // Brightness near mouse
        let bonus = 0;
        if (smMouse.x > -9999) {
          const dx = star.x - smMouse.x;
          const dy = star.y - smMouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const r = W * 0.10;
          if (dist < r) bonus = (1 - dist / r) * 0.25;
        }
        drawStar(star, alpha, bonus);
      });

      // ─ Waves ─
      if (!reduced) {
        updatePhysics();
      }
      waveLines.forEach((line, li) => drawWaveLine(line, pointStates[li]));

      // ─ Cursor glow (very subtle) ─
      if (smMouse.x > -9999 && !reduced) {
        const grd = ctx.createRadialGradient(smMouse.x, smMouse.y, 0, smMouse.x, smMouse.y, W * 0.20);
        grd.addColorStop(0,   'rgba(139,92,246,0.05)');
        grd.addColorStop(0.6, 'rgba(249,115,22,0.02)');
        grd.addColorStop(1,   'rgba(0,0,0,0)');
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, W, H);
      }

      // ─ Keep running? ─
      // Continue if mouse is active OR waves haven't settled yet
      const stillMoving = rawMouse.x > -9999 || !isSettled();
      if (stillMoving) {
        rafId = requestAnimationFrame(draw);
      } else {
        rafRunning = false;
        hasMouseMoved = false;
      }
    };

    const startRaf = () => {
      if (rafRunning) return;
      rafRunning = true;
      lastTs = performance.now();
      rafId = requestAnimationFrame(draw);
    };

    // Always run the star twinkle (cheap) but pause wave physics when idle
    // We do this by always running rAF just for stars when page is idle
    let starRafId = 0;
    const drawStarsOnly = (_ts: number) => {
      // Only draw stars when waves are settled and mouse is away
      if (hasMouseMoved || rawMouse.x > -9999) {
        starRafId = requestAnimationFrame(drawStarsOnly);
        return; // full loop handles this
      }

      ctx.clearRect(0, 0, W, H);
      stars.forEach(star => {
        star.phase += star.speed * 16; // ~60fps estimate
        const twinkle = 0.5 + 0.5 * Math.sin(star.phase);
        drawStar(star, star.baseAlpha * twinkle, 0);
      });
      waveLines.forEach((line, li) => drawWaveLine(line, pointStates[li]));

      starRafId = requestAnimationFrame(drawStarsOnly);
    };
    starRafId = requestAnimationFrame(drawStarsOnly);

    return () => {
      cancelAnimationFrame(rafId);
      cancelAnimationFrame(starRafId);
      ro.disconnect();
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseleave', onMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'none',
        display: 'block',
        background: '#141414',
      }}
    />
  );
}
