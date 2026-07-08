import { COLORS } from "@/lib/theme";

const MIN = 27.0;
const MAX = 30.5;

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = (deg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy - r * Math.sin(rad) };
}

// Arco semicircolare superiore: 180° = sinistra(min), 0° = destra(max).
function arcPath(cx: number, cy: number, r: number, startDeg: number, endDeg: number) {
  const s = polar(cx, cy, r, startDeg);
  const e = polar(cx, cy, r, endDeg);
  const large = Math.abs(endDeg - startDeg) > 180 ? 1 : 0;
  const sweep = startDeg > endDeg ? 1 : 0;
  return `M ${s.x.toFixed(1)} ${s.y.toFixed(1)} A ${r} ${r} 0 ${large} ${sweep} ${e.x.toFixed(1)} ${e.y.toFixed(1)}`;
}

function angleFor(v: number) {
  const t = Math.max(0, Math.min(1, (v - MIN) / (MAX - MIN)));
  return 180 - 180 * t;
}

export default function PressureGauge({
  label,
  value,
  window: win,
}: {
  label: string;
  value: number;
  window: [number, number];
}) {
  const [lo, hi] = win;
  const inWin = value >= lo && value <= hi;
  const color = inWin ? COLORS.ok : COLORS.accent;
  const cx = 80;
  const cy = 78;
  const r = 60;
  const needle = polar(cx, cy, r - 6, angleFor(value));

  return (
    <div className="flex flex-col items-center">
      <div className="font-mono text-[0.7rem] uppercase tracking-wider text-subtle">{label}</div>
      <svg viewBox="0 0 160 96" className="w-full max-w-[180px]">
        <path d={arcPath(cx, cy, r, 180, 0)} fill="none" stroke={COLORS.raised} strokeWidth={10} strokeLinecap="round" />
        <path
          d={arcPath(cx, cy, r, angleFor(lo), angleFor(hi))}
          fill="none"
          stroke={COLORS.ok}
          strokeOpacity={0.5}
          strokeWidth={10}
          strokeLinecap="round"
        />
        <line x1={cx} y1={cy} x2={needle.x.toFixed(1)} y2={needle.y.toFixed(1)} stroke={color} strokeWidth={2.6} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={3.5} fill={color} />
      </svg>
      <div className="-mt-2 font-mono text-lg" style={{ color }}>
        {value.toFixed(1)}
        <span className="text-xs text-subtle"> psi</span>
      </div>
      <div className="font-mono text-[0.6rem] uppercase tracking-wider" style={{ color }}>
        {inWin ? "● in finestra" : "▼ bassa"}
      </div>
    </div>
  );
}
