"use client";

// Numero che sale al mount (stile timing screen). Riutilizzabile in tutta la v2.
// Reduced-motion → mostra subito il valore finale, nessuna animazione.
import { useEffect } from "react";
import { animate, motion, useMotionValue, useTransform } from "framer-motion";
import { DUR, EASE, useReducedMotion } from "@/lib/motion";

export default function CountUp({
  value,
  decimals = 0,
  suffix = "",
  duration = DUR.slow,
  className,
}: {
  value: number;
  decimals?: number;
  suffix?: string;
  duration?: number;
  className?: string;
}) {
  const reduce = useReducedMotion();
  const mv = useMotionValue(reduce ? value : 0);
  const text = useTransform(mv, (v) => `${v.toFixed(decimals)}${suffix}`);

  useEffect(() => {
    if (reduce) {
      mv.set(value);
      return;
    }
    const controls = animate(mv, value, { duration, ease: EASE });
    return () => controls.stop();
  }, [value, duration, reduce, mv]);

  // font-mono per coerenza coi numeri esistenti.
  return <motion.span className={className}>{text}</motion.span>;
}
