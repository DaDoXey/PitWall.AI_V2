"use client";

// Mini-trend SVG hand-rolled (no Recharts): decorativo-informativo, si legge a
// colpo d'occhio. Coerente con PressureGauge/TyreHeatmap (già SVG) e leggero:
// non trascina il bundle Recharts sulla Dashboard.
//
// Responsività: il viewBox definisce l'aspetto (≈5:1); la SVG scala UNIFORME a
// tutta la larghezza (`w-full` + height:auto) → niente `preserveAspectRatio="none"`
// che prima stirava solo in orizzontale (linea schiacciata, pallino finale ovale).
// Lo stroke resta costante via `vectorEffect="non-scaling-stroke"`.
//
// Motion (F9): la linea si "disegna" (pathLength 0→1), l'area sfuma e il pallino
// finale compare a fine tratto. pathLength/opacity NON sono transform → reduced-
// motion non li riduce da solo: useReducedMotion() degrada allo stato finale.
import { useId } from "react";
import { motion } from "framer-motion";
import { DUR, EASE, useReducedMotion } from "@/lib/motion";

export default function Sparkline({
  data,
  color,
  width = 240, // coordinate del viewBox: fissano l'aspetto, non i pixel resi
  height = 48,
  strokeWidth = 1.75,
  fill = true,
  className,
}: {
  data: number[];
  color: string;
  width?: number;
  height?: number;
  strokeWidth?: number;
  fill?: boolean;
  className?: string;
}) {
  const gid = useId();
  const reduce = useReducedMotion();
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1; // serie piatta → linea centrata, niente /0
  const pad = strokeWidth + 2;

  const x = (i: number) => (i / (data.length - 1)) * (width - pad * 2) + pad;
  const y = (v: number) => height - pad - ((v - min) / span) * (height - pad * 2);

  const pts = data.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  const line = `M ${pts.join(" L ")}`;
  const area = `${line} L ${x(data.length - 1).toFixed(1)},${(height - pad).toFixed(1)} L ${x(0).toFixed(1)},${(height - pad).toFixed(1)} Z`;
  const lastX = x(data.length - 1);
  const lastY = y(data[data.length - 1]);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={`block w-full ${className ?? ""}`}
      style={{ height: "auto" }}
      aria-hidden="true"
    >
      {fill && (
        <>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.22} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <motion.path
            d={area}
            fill={`url(#${gid})`}
            initial={reduce ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: DUR.base, ease: EASE, delay: DUR.slow * 0.5 }}
          />
        </>
      )}
      <motion.path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
        initial={reduce ? false : { pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: DUR.slow, ease: EASE }}
      />
      <motion.circle
        cx={lastX}
        cy={lastY}
        r={strokeWidth + 0.75}
        fill={color}
        initial={reduce ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: DUR.fast, delay: DUR.slow }}
      />
    </svg>
  );
}
