"use client";

// Reduced-motion centralizzato per tutta la v2: con reducedMotion="user" framer
// disabilita da solo i transform/layout quando l'utente ha attivo prefers-reduced-
// motion. I casi non-transform (CountUp, pulse) usano useReducedMotion() nel
// componente. Wrappa i children in layout.tsx.
import { MotionConfig } from "framer-motion";

export default function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
