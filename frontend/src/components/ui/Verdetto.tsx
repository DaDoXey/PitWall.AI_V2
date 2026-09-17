"use client";

// Il verdetto del motore di analisi, come lo vede il pilota (L4).
// Solo presentazione: ordine, gravità, prove e azioni arrivano già decisi dal backend.
// Tre blocchi separati di proposito: le perdite (spietate, con prova e azione), ciò
// che regge (dimostrato, niente complimenti a vuoto) e le note sui dati (ciò che
// manca o che l'import ha dovuto interpretare: un silenzio non è un «tutto bene»).
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { Perdita, PuntoFermo } from "@/lib/api";
import { fadeInUp, staggerContainer } from "@/lib/motion";

const VISIBILI = 5;

export function ElencoVerdetto({ voci }: { voci: Perdita[] }) {
  const [tutte, setTutte] = useState(false);
  if (voci.length === 0) {
    return (
      <div className="rounded-xl border border-line bg-surface p-4 text-sm text-subtle">
        Nessuna perdita dimostrabile con i dati di questa sessione.
      </div>
    );
  }
  const mostrate = tutte ? voci : voci.slice(0, VISIBILI);
  return (
    <div>
      <motion.ol variants={staggerContainer} initial="hidden" animate="visible" className="flex flex-col gap-2">
        {mostrate.map((v, i) => (
          <motion.li key={`${i}-${v.titolo}`} variants={fadeInUp}>
            <VocePerdita voce={v} posizione={i + 1} />
          </motion.li>
        ))}
      </motion.ol>
      {voci.length > VISIBILI && (
        <button
          type="button"
          onClick={() => setTutte((t) => !t)}
          className="mt-2 font-mono text-[0.6rem] uppercase tracking-widest text-subtle transition hover:text-white"
        >
          {tutte ? "Mostra solo le prime 5" : `Mostra tutte (${voci.length})`}
        </button>
      )}
    </div>
  );
}

function VocePerdita({ voce, posizione }: { voce: Perdita; posizione: number }) {
  const [aperta, setAperta] = useState(posizione === 1);
  return (
    <div className="rounded-xl border border-line bg-surface">
      <button
        type="button"
        onClick={() => setAperta((a) => !a)}
        aria-expanded={aperta}
        className="flex w-full items-start gap-3 p-3 text-left"
      >
        <span className="mt-0.5 w-6 shrink-0 font-mono text-sm text-accent">{String(posizione).padStart(2, "0")}</span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm text-white">{voce.titolo}</span>
          <span className="mt-1 flex flex-wrap gap-1.5">
            <Etichetta testo={voce.categoria === "gomme" ? "gomme" : "tempo"} />
            {voce.fonte === "kunos" && <Etichetta testo="soglia Kunos" accesa />}
          </span>
        </span>
        {voce.decimi !== null && (
          <span className="shrink-0 text-right">
            <span className="block font-mono text-lg text-warn">−{(voce.decimi / 10).toFixed(2)} s</span>
            <span className="block font-mono text-[0.5rem] uppercase tracking-widest text-muted">a giro</span>
          </span>
        )}
      </button>
      <AnimatePresence initial={false}>
        {aperta && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="grid gap-2 border-t border-line px-3 pb-3 pt-2.5 sm:grid-cols-2">
              <Riquadro titolo="La prova" testo={voce.prova} />
              <Riquadro titolo="Cosa fare" testo={voce.azione} accento />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Riquadro({ titolo, testo, accento }: { titolo: string; testo: string; accento?: boolean }) {
  return (
    <div className={`rounded-lg border bg-inset p-2.5 ${accento ? "border-l-2 border-line border-l-accent" : "border-line"}`}>
      <div className={`font-mono text-[0.55rem] uppercase tracking-widest ${accento ? "text-accent" : "text-muted"}`}>
        {titolo}
      </div>
      <p className="mt-1 text-[0.8rem] leading-relaxed text-subtle">{testo}</p>
    </div>
  );
}

export function Etichetta({ testo, accesa }: { testo: string; accesa?: boolean }) {
  return (
    <span
      className={`rounded border px-1.5 py-px font-mono text-[0.5rem] uppercase tracking-widest ${
        accesa ? "border-accent/50 text-accent" : "border-line-strong text-muted"
      }`}
    >
      {testo}
    </span>
  );
}

export function CosaRegge({ punti }: { punti: PuntoFermo[] }) {
  if (punti.length === 0) return null;
  return (
    <ul className="flex flex-col gap-2">
      {punti.map((p) => (
        <li key={p.titolo} className="rounded-lg border border-l-2 border-line border-l-ok bg-surface p-3">
          <div className="text-sm text-white">{p.titolo}</div>
          <div className="mt-0.5 text-[0.78rem] text-subtle">{p.prova}</div>
        </li>
      ))}
    </ul>
  );
}

export function NoteDati({ note }: { note: string[] }) {
  const [aperte, setAperte] = useState(false);
  if (note.length === 0) return null;
  return (
    <div className="rounded-xl border border-line bg-surface p-3">
      <button
        type="button"
        onClick={() => setAperte((a) => !a)}
        aria-expanded={aperte}
        className="flex w-full items-center justify-between text-left"
      >
        <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">
          Note sui dati · {note.length}
        </span>
        <span className="font-mono text-[0.6rem] text-muted">{aperte ? "▴" : "▾"}</span>
      </button>
      {aperte && (
        <ul className="mt-2 flex flex-col gap-1.5">
          {note.map((n, i) => (
            <li key={i} className="flex gap-2 text-[0.76rem] leading-snug text-subtle">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-line-strong" />
              {n}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Stato di attesa/errore comune alle pagine che leggono la sessione aperta. */
export function StatoSessione({ errore, caricamento }: { errore: string | null; caricamento: boolean }) {
  if (errore) return <p className="text-sm text-warn">{errore}</p>;
  if (caricamento) return <p className="text-sm text-subtle">Analisi della sessione…</p>;
  return null;
}
