"use client";

import { motion } from "framer-motion";
import { fadeInUp } from "@/lib/motion";

export default function PageHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className="mb-6 border-l-4 border-accent pl-4"
    >
      <h1 className="font-display text-2xl font-bold tracking-wide">{title}</h1>
      {subtitle && (
        <p className="mt-1 font-mono text-xs uppercase tracking-widest text-muted">
          {subtitle}
        </p>
      )}
    </motion.div>
  );
}
