"use client";

// A Lezione con Gigi — indice (megaprompt #8, FASE 2). Disclosure progressiva:
// la card mostra SOLO numero + titolo + sintesi (una riga) + eventuale tag
// «nell'app» (la lezione rimanda a una pagina di PitWall); il contenuto completo vive in /lezioni/[slug] (FASE 3).
// Dati read-only da lib/lessons.ts (fonte: content pack in docs/).
import Link from "next/link";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { LESSONS, lezioniConsigliate } from "@/lib/lessons";
import { useProfile } from "@/lib/profile";
import { useSessione } from "@/lib/sessione";

export default function LezioniPage() {
  const { report } = useSessione();
  const { profile } = useProfile();
  const consigliate = lezioniConsigliate(report?.verdetto ?? [], profile?.weakAreas ?? []);

  return (
    <div>
      <PageHeader
        title="A Lezione con Gigi"
        subtitle="Gigi · i fondamentali per andare più forte"
      />

      {/* Le lezioni che c'entrano con la sessione aperta e col tuo profilo, col perché. */}
      {consigliate.length > 0 && (
        <motion.section
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
          className="mb-5 rounded-xl border border-l-4 border-line border-l-accent bg-surface p-4"
        >
          <div className="mb-2 font-mono text-[0.6rem] uppercase tracking-widest text-accent">Consigliate per te</div>
          <div className="flex flex-col divide-y divide-line">
            {consigliate.map(({ lesson, motivo }) => (
              <Link
                key={lesson.slug}
                href={`/lezioni/${lesson.slug}`}
                className="group flex flex-wrap items-baseline gap-x-3 gap-y-0.5 py-2 first:pt-0 last:pb-0"
              >
                <span className="font-mono text-xs text-muted">{String(lesson.number).padStart(2, "0")}</span>
                <span className="font-display text-sm font-bold tracking-wide transition-colors group-hover:text-accent">
                  {lesson.title}
                </span>
                <span className="min-w-0 flex-1 truncate text-[0.75rem] text-subtle">{motivo}</span>
                <span className="font-mono text-xs text-muted transition-colors group-hover:text-accent">→</span>
              </Link>
            ))}
          </div>
        </motion.section>
      )}

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
              className="group flex h-full flex-col rounded-xl border border-line bg-surface p-5 transition duration-200 hover:-translate-y-1 hover:border-accent/50"
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
                <div className="mt-auto pt-3">
                  <span className="inline-block rounded border border-line bg-inset px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-wider text-muted">
                    nell&apos;app
                  </span>
                </div>
              )}
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
