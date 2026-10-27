// Decorative hero chart: a candlestick tape that scrolls forever. The series is built to end where it
// starts, so two copies side by side loop seamlessly. Pure CSS motion; frozen under reduced motion.

type Candle = { o: number; c: number; h: number; l: number };

const N = 36;
const W = 720;
const H = 400;
const PAD = 24;

const CANDLES: Candle[] = (() => {
  let seed = 4127;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const closes: number[] = [];
  let p = 0;
  for (let i = 0; i < N; i++) closes.push((p += (rnd() - 0.5) * 7 + Math.sin(i / 4) * 2));
  // Remove net drift so the last close equals the first open: the loop has no seam.
  const drift = closes[N - 1] / N;
  let prev = 100;
  return closes.map((c, i) => {
    const close = 100 + c - drift * (i + 1);
    const o = prev;
    prev = close;
    return { o, c: close, h: Math.max(o, close) + rnd() * 3, l: Math.min(o, close) - rnd() * 3 };
  });
})();

const lo = Math.min(...CANDLES.map((k) => k.l));
const hi = Math.max(...CANDLES.map((k) => k.h));
const y = (v: number) => PAD + ((hi - v) / (hi - lo)) * (H - PAD * 2);
const step = W / N;
const x = (i: number) => step * i + step / 2;
// Both edges sit at 100 (first open == last close), so copies placed W apart join without a gap.
const EDGE = y(100).toFixed(1);
const LINE = `M0 ${EDGE} ${CANDLES.map((k, i) => `L${x(i).toFixed(1)} ${y(k.c).toFixed(1)}`).join(" ")} L${W} ${EDGE}`;
const AREA = `${LINE} L${W} ${H} L0 ${H} Z`;

function Tape({ offset }: { offset: number }) {
  return (
    <g transform={`translate(${offset} 0)`}>
      <path d={AREA} fill="url(#qf-area)" />
      {CANDLES.map((k, i) => {
        const color = k.c >= k.o ? "hsl(var(--success))" : "hsl(var(--destructive))";
        const top = y(Math.max(k.o, k.c));
        return (
          <g key={i}>
            <line x1={x(i)} x2={x(i)} y1={y(k.h)} y2={y(k.l)} stroke={color} strokeWidth={2} />
            <rect
              x={x(i) - step * 0.32}
              y={top}
              width={step * 0.64}
              height={Math.max(3, Math.abs(y(k.o) - y(k.c)))}
              rx={2}
              fill={color}
            />
          </g>
        );
      })}
      <path d={LINE} fill="none" stroke="hsl(var(--primary))" strokeWidth={2.5} strokeLinejoin="round" />
    </g>
  );
}

export function MarketChart({ className }: { className?: string }) {
  return (
    <div aria-hidden className={`qf-chart ${className ?? ""}`}>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full overflow-hidden">
        <defs>
          <linearGradient id="qf-area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="hsl(var(--primary))" stopOpacity="0.28" />
            <stop offset="1" stopColor="hsl(var(--primary))" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.2, 0.4, 0.6, 0.8].map((f) => (
          <line key={f} x1={0} x2={W} y1={H * f} y2={H * f} stroke="hsl(var(--border))" strokeDasharray="2 8" />
        ))}
        <g className="qf-tape">
          <Tape offset={0} />
          <Tape offset={W} />
        </g>
      </svg>
    </div>
  );
}
