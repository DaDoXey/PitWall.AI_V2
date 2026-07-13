"use client";

// A Lezione con Gigi — dettaglio (megaprompt #8, FASE 3). Template unico per le
// 8 lezioni: Sintesi · Perché conta · Quando usarla · Come si fa · Errori comuni ·
// Aggancio PitWall (condizionale) · Approfondisci (video card). Read-only da
// lib/lessons.ts. Video: thumbnail statica YouTube che apre in nuova scheda,
// NESSUN iframe; videoId "TODO" → stato "video in arrivo" pulito.
import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { lessonBySlug, type Lesson } from "@/lib/lessons";

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mb-2 font-mono text-xs uppercase tracking-widest text-muted">
      {children}
    </h2>
  );
}

function VideoCard({ video }: { video: Lesson["video"] }) {
  const pending = video.videoId === "TODO";
  if (pending) {
    // Stato pulito in attesa dell'URL confermato: niente thumbnail rotta.
    return (
      <div className="rounded-xl border border-dashed border-line bg-inset p-4">
        <div className="text-sm text-subtle">{video.title}</div>
        <div className="mt-1 font-mono text-[0.65rem] uppercase tracking-wider text-muted">
          {video.channel} · video in arrivo
        </div>
      </div>
    );
  }
  return (
    <a
      href={`https://www.youtube.com/watch?v=${video.videoId}`}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-center gap-4 rounded-xl border border-line bg-surface p-3 transition duration-200 hover:-translate-y-1 hover:border-accent/50"
    >
      {/* Thumbnail statica YouTube (nessun iframe/embed) */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={`https://img.youtube.com/vi/${video.videoId}/hqdefault.jpg`}
        alt=""
        className="h-20 w-36 shrink-0 rounded-lg border border-line object-cover"
      />
      <div className="min-w-0">
        <div className="truncate text-sm font-semibold transition-colors group-hover:text-accent">
          {video.title}
        </div>
        <div className="mt-1 font-mono text-[0.65rem] uppercase tracking-wider text-muted">
          {video.channel} · si apre su YouTube ↗
        </div>
      </div>
    </a>
  );
}

export default function LezioneDettaglio() {
  const { slug } = useParams<{ slug: string }>();
  const lesson = lessonBySlug(slug);
  if (!lesson) notFound();

  return (
    <div className="max-w-3xl">
      <Link
        href="/lezioni"
        className="mb-4 inline-block font-mono text-xs uppercase tracking-wider text-muted transition-colors hover:text-accent"
      >
        ← Tutte le lezioni
      </Link>
      <PageHeader
        title={lesson.title}
        subtitle={`Lezione ${String(lesson.number).padStart(2, "0")} · A Lezione con Gigi`}
      />

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="flex flex-col gap-6"
      >
        {/* Sintesi: lead in evidenza, idioma filetto sinistro */}
        <motion.p
          variants={fadeInUp}
          className="border-l-2 border-line pl-4 text-base leading-relaxed text-subtle"
        >
          {lesson.summary}
        </motion.p>

        <motion.section variants={fadeInUp}>
          <SectionTitle>Perché conta</SectionTitle>
          <p className="text-sm leading-relaxed text-subtle">{lesson.whyItMatters}</p>
        </motion.section>

        {lesson.whenToUse && (
          <motion.section variants={fadeInUp}>
            <SectionTitle>Quando usarla</SectionTitle>
            <p className="text-sm leading-relaxed text-subtle">{lesson.whenToUse}</p>
          </motion.section>
        )}

        <motion.section variants={fadeInUp}>
          <SectionTitle>Come si fa</SectionTitle>
          <ul className="flex flex-col gap-2">
            {lesson.howTo.map((step, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed text-subtle">
                <span className="shrink-0 font-mono text-xs text-muted">{i + 1}.</span>
                {step}
              </li>
            ))}
          </ul>
        </motion.section>

        <motion.section variants={fadeInUp}>
          <SectionTitle>Errori comuni</SectionTitle>
          <ul className="flex flex-col gap-2">
            {lesson.commonMistakes.map((m, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed text-subtle">
                <span className="shrink-0 text-accent">✕</span>
                {m}
              </li>
            ))}
          </ul>
        </motion.section>

        {lesson.pitwallLink && (
          <motion.section
            variants={fadeInUp}
            className="rounded-xl border border-l-4 border-line border-l-accent bg-surface p-4"
          >
            <SectionTitle>Aggancio PitWall</SectionTitle>
            <p className="text-sm leading-relaxed text-subtle">{lesson.pitwallLink.label}</p>
            <Link
              href={lesson.pitwallLink.href}
              className="mt-2 inline-block font-mono text-xs uppercase tracking-wider text-accent transition-colors hover:text-accent-hover"
            >
              Apri →
            </Link>
          </motion.section>
        )}

        <motion.section variants={fadeInUp} className="pb-8">
          <SectionTitle>Approfondisci</SectionTitle>
          <VideoCard video={lesson.video} />
          {lesson.videoNote && (
            <p className="mt-2 text-xs italic leading-relaxed text-muted">
              {lesson.videoNote}
            </p>
          )}
        </motion.section>
      </motion.div>
    </div>
  );
}
