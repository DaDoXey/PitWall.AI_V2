"use client";

import { motion } from "framer-motion";
import { fadeInUp } from "@/lib/motion";

export default function PageHeader({
  title,
  subtitle,
  azioni,
}: {
  title: string;
  subtitle?: string;
  /** a destra del titolo (es. lo stato di Gigi nella Console) */
  azioni?: React.ReactNode;
}) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className="mb-6 flex flex-wrap items-end justify-between gap-3 border-l-4 border-accent pl-4"
    >
      <div>
        <h1 className="font-display text-2xl font-bold tracking-wide">{title}</h1>
        {subtitle && (
          <p className="mt-1 font-mono text-xs uppercase tracking-widest text-muted">
            {subtitle}
          </p>
        )}
      </div>
      {azioni}
    </motion.div>
  );
}
