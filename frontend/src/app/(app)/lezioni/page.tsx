"use client";

// A Lezione con Gigi — indice (megaprompt #8, FASE 2). Disclosure progressiva:
// la card mostra SOLO numero + titolo + sintesi (una riga) + eventuale tag
// "aggancio PitWall"; il contenuto completo vive in /lezioni/[slug] (FASE 3).
// Dati read-only da lib/lessons.ts (fonte: content pack in docs/).
import Link from "next/link";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { LESSONS } from "@/lib/lessons";

export default function LezioniPage() {
  return (
    <div>
      <PageHeader
        title="A Lezione con Gigi"
        subtitle="Gigi · i fondamentali per andare più forte"
      />

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2"
      >
        {LESSONS.map((l) => (
          <motion.div key={l.slug} variants={fadeInUp}>
            <Link
              href={`/lezioni/${l.slug}`}
              className="group block h-full rounded-xl border border-line bg-surface p-5 transition duration-200 hover:-translate-y-1 hover:border-accent/50"
            >
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-xs text-muted">
                  {String(l.number).padStart(2, "0")}
                </span>
                <h2 className="font-display text-base font-bold tracking-wide transition-colors group-hover:text-accent">
                  {l.title}
                </h2>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-subtle">{l.summary}</p>
              {l.pitwallLink && (
                <span className="mt-3 inline-block rounded border border-line bg-inset px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-wider text-muted">
                  aggancio PitWall
                </span>
              )}
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
