"use client";

// Gauge pressioni a LANCETTA (megaprompt #2, FASE 2): scala semicircolare fissa
// con tacche, lancetta sottile che punta al valore, colore SOLO sulla lancetta/
// mozzo/numero (stato), banda finestra neutra. Nessun glow/drop-shadow — resa
// "strumento analogico" (token instrument.ts).
//
// L4 (16/09/2026): lo stato NON si calcola più qui. La finestra è quella indicativa
// di Kunos e il giudizio «fuori» lo dà il motore di analisi (quota di tempo fuori
// oltre soglia): il gauge riceve `fuori` e un'etichetta, e li mostra.
import CountUp from "@/components/ui/CountUp";
import { INSTRUMENT, STATE, STROKE } from "@/lib/instrument";

const MIN = 24.0;
const MAX = 28.0;
const TICK_STEP = 0.5;

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
  fuori,
  stato,
}: {
  label: string;
  value: number;
  window: [number, number] | null;
  fuori: boolean;
  stato: string;
}) {
  const color = win === null ? INSTRUMENT.ink : fuori ? STATE.warn : STATE.ok;

  const cx = 80;
  const cy = 78;
  const r = 58;
  const needle = polar(cx, cy, r - 10, angleFor(value));

  const ticks: number[] = [];
  for (let v = MIN; v <= MAX + 1e-6; v += TICK_STEP) ticks.push(Number(v.toFixed(1)));

  return (
    <div className="flex flex-col items-center">
      <div className="font-mono text-[0.7rem] uppercase tracking-wider text-subtle">{label}</div>
      <svg viewBox="0 0 160 96" className="w-full max-w-[180px]">
        <path d={arcPath(cx, cy, r, 180, 0)} fill="none" stroke={INSTRUMENT.grid} strokeWidth={2} strokeLinecap="round" />
        {/* Finestra indicativa Kunos: zona neutra, nessun colore di stato */}
        {win && <path d={arcPath(cx, cy, r, angleFor(win[0]), angleFor(win[1]))} fill="none" stroke={INSTRUMENT.track} strokeWidth={4} />}
        {ticks.map((tv) => {
          const a = angleFor(tv);
          const major = Number.isInteger(tv);
          const o = polar(cx, cy, r, a);
          const i = polar(cx, cy, r - (major ? 8 : 5), a);
          return <line key={tv} x1={o.x} y1={o.y} x2={i.x} y2={i.y} stroke={INSTRUMENT.tick} strokeWidth={major ? STROKE.tick : STROKE.hairline} />;
        })}
        <line x1={cx} y1={cy} x2={needle.x} y2={needle.y} stroke={color} strokeWidth={STROKE.needle} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={3} fill={color} />
      </svg>
      <div className="-mt-2 font-mono text-lg" style={{ color }}>
        <CountUp value={value} decimals={1} />
        <span className="text-xs text-subtle"> psi</span>
      </div>
      <div className="text-center font-mono text-[0.58rem] uppercase tracking-wider" style={{ color }}>
        {stato}
      </div>
    </div>
  );
}
