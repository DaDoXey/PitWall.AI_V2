"use client";

// Blocco "Gigi consiglia" per la Sidebar (megaprompt #7, FASE 3): SOLO la
// prossima azione (CTA) + link "vedi tutti" → Console. Il mini-elenco "Ultimi
// consigli" è stato rimosso: le voci puntavano tutte alla Console, dove i
// consigli vivono già per intero (una rappresentazione per dato).
// I consigli vengono dai suggested_params reali (vedi lib/advice.ts).
// Colore accent solo sulla CTA (azione), niente glow.
import Link from "next/link";
import { buildAdvice } from "@/lib/advice";
import type { SessionData } from "@/lib/telemetry";

export default function GigiAdvice({ data }: { data: SessionData }) {
  const advice = buildAdvice(data);
  const top = advice[0];

  return (
    <div>
      {/* CTA: prossima azione consigliata (dal consiglio in cima) */}
      {top ? (
        <Link
          href="/console"
          title="Apri la Console per l'analisi completa di Gigi"
          className="group block rounded-lg border border-l-2 border-line border-l-accent bg-inset p-2.5 transition hover:border-accent"
        >
          <div className="font-mono text-[0.5rem] uppercase tracking-widest text-accent">Prossima azione</div>
          <div className="mt-0.5 flex items-center justify-between gap-2">
            <span className="truncate text-[0.78rem] text-white">{top.label}</span>
            <span aria-hidden className="font-mono text-xs text-muted transition group-hover:text-accent">→</span>
          </div>
        </Link>
      ) : (
        <div className="rounded-lg border border-line bg-inset p-2.5 text-[0.72rem] text-muted">
          Nessun consiglio in sospeso
        </div>
      )}

      {/* Tutti i consigli vivono nella Console: qui solo il rimando */}
      <Link
        href="/console"
        className="mt-1.5 flex items-center justify-end gap-1 font-mono text-[0.58rem] text-subtle transition hover:text-white"
      >
        vedi tutti <span aria-hidden>→</span>
      </Link>
    </div>
  );
}
