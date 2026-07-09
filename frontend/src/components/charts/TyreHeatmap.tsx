"use client";

import { motion } from "framer-motion";
import { COLORS } from "@/lib/theme";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { tempToColor, type Corner, type SessionData } from "@/lib/telemetry";

// Geometria portata dalla v1 (telemetry._heatmap_html): scocca + 4 riquadri-gomma.
const BODY_LEFT_X = 78;
const BODY_RIGHT_X = 162;
const FRONT_AXLE_Y = 96;
const REAR_AXLE_Y = 230;
const WHEEL_W = 40;
const WHEEL_H = 74;

function Wheel({
  cx,
  cy,
  val,
  label,
  scale,
}: {
  cx: number;
  cy: number;
  val: number;
  label: string;
  scale: [number, number];
}) {
  const x = cx - WHEEL_W / 2;
  const y = cy - WHEEL_H / 2;
  return (
    <motion.g variants={fadeInUp}>
      <rect x={x} y={y} width={WHEEL_W} height={WHEEL_H} rx={12} fill={tempToColor(val, scale)} stroke="#000" strokeOpacity={0.35} />
      <text x={cx} y={cy - 4} textAnchor="middle" fontFamily="var(--font-mono)" fontSize={14} fontWeight={700} fill="#fff">
        {val}°
      </text>
      <text x={cx} y={cy + 20} textAnchor="middle" fontFamily="var(--font-mono)" fontSize={8} fill="#fff" opacity={0.85}>
        {label}
      </text>
    </motion.g>
  );
}

export default function TyreHeatmap({ data }: { data: SessionData }) {
  const scale = data.temp.scale;
  const [lo, hi] = scale;
  const lx = BODY_LEFT_X - WHEEL_W / 2;
  const rx = BODY_RIGHT_X + WHEEL_W / 2;
  const L = data.tyre_labels;
  const M = data.temp.max;
  const corners: { cx: number; cy: number; k: Corner }[] = [
    { cx: lx, cy: FRONT_AXLE_Y, k: "fl" },
    { cx: rx, cy: FRONT_AXLE_Y, k: "fr" },
    { cx: lx, cy: REAR_AXLE_Y, k: "rl" },
    { cx: rx, cy: REAR_AXLE_Y, k: "rr" },
  ];

  return (
    <div className="rounded-xl border border-line bg-inset p-4">
      <div className="mb-2 font-mono text-[0.72rem] uppercase tracking-wider text-subtle">Heatmap gomme · max stint</div>
      <svg viewBox="0 0 240 290" className="w-full" style={{ maxHeight: 340 }} preserveAspectRatio="xMidYMid meet">
        <path
          d="M120 24 C150 24 162 50 162 96 L162 230 C162 256 146 268 120 268 C94 268 78 256 78 230 L78 96 C78 50 90 24 120 24 Z"
          fill="#161616"
          stroke={COLORS.lineStrong}
          strokeWidth={2}
        />
        <path d="M98 118 L142 118 L134 150 L106 150 Z" fill="#0e0e0e" stroke={COLORS.line} />
        <rect x={104} y={158} width={32} height={46} rx={6} fill="#0e0e0e" stroke={COLORS.line} />
        <motion.g variants={staggerContainer} initial="hidden" animate="visible">
          {corners.map((c) => (
            <Wheel key={c.k} cx={c.cx} cy={c.cy} val={M[c.k]} label={L[c.k]} scale={scale} />
          ))}
        </motion.g>
      </svg>
      <div className="mt-2 flex items-center gap-2">
        <span className="font-mono text-[9px] text-muted">{lo}°</span>
        <span
          className="h-2 flex-1 rounded"
          style={{ background: `linear-gradient(90deg, ${tempToColor(lo, scale)}, ${tempToColor(hi, scale)})` }}
        />
        <span className="font-mono text-[9px] text-muted">{hi}°</span>
      </div>
    </div>
  );
}
