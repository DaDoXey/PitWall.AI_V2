"use client";

import { motion } from "framer-motion";
import { COLORS } from "@/lib/theme";
import { DUR, EASE, useReducedMotion } from "@/lib/motion";
import CountUp from "@/components/ui/CountUp";

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
  const reduce = useReducedMotion();
  const t = Math.max(0, Math.min(1, (value - MIN) / (MAX - MIN))); // riempimento proporzionale (frazione dell'arco)
  const tip = polar(cx, cy, r, angleFor(value)); // marker sul valore corrente
  const tickAt = (deg: number) => ({ i: polar(cx, cy, r - 9, deg), o: polar(cx, cy, r + 7, deg) });
  const tLo = tickAt(angleFor(lo));
  const tHi = tickAt(angleFor(hi));

  return (
    <div className="flex flex-col items-center">
      <div className="font-mono text-[0.7rem] uppercase tracking-wider text-subtle">{label}</div>
      <svg viewBox="0 0 160 96" className="w-full max-w-[180px]">
        {/* Track di fondo: anello spesso */}
        <path d={arcPath(cx, cy, r, 180, 0)} fill="none" stroke={COLORS.raised} strokeWidth={13} strokeLinecap="round" />
        {/* Riempimento proporzionale al valore, glow HUD; draw-in da min → valore
            (pathLength 0→t). pathLength non è transform → reduced-motion via guardia. */}
        <motion.path
          d={arcPath(cx, cy, r, 180, 0)}
          fill="none"
          stroke={color}
          strokeWidth={13}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
          initial={reduce ? false : { pathLength: 0 }}
          animate={{ pathLength: t }}
          transition={{ duration: DUR.slow, ease: EASE }}
        />
        {/* Tacche ai bordi della finestra ottimale */}
        <line x1={tLo.i.x} y1={tLo.i.y} x2={tLo.o.x} y2={tLo.o.y} stroke={COLORS.ok} strokeWidth={2} strokeLinecap="round" />
        <line x1={tHi.i.x} y1={tHi.i.y} x2={tHi.o.x} y2={tHi.o.y} stroke={COLORS.ok} strokeWidth={2} strokeLinecap="round" />
        {/* Marker del valore corrente: compare a fine sweep */}
        <motion.circle
          cx={tip.x}
          cy={tip.y}
          r={3.5}
          fill={color}
          initial={reduce ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: DUR.fast, delay: DUR.slow }}
        />
      </svg>
      <div className="-mt-2 font-mono text-lg" style={{ color }}>
        <CountUp value={value} decimals={1} />
        <span className="text-xs text-subtle"> psi</span>
      </div>
      <div className="font-mono text-[0.6rem] uppercase tracking-wider" style={{ color }}>
        {inWin ? "● in finestra" : "▼ bassa"}
      </div>
    </div>
  );
}
