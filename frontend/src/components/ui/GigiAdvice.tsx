"use client";

// Blocco "Gigi consiglia" per la Sidebar (megaprompt #5, FASE 4): CTA sulla
// prossima azione + mini-elenco degli ultimi consigli (non più una sola riga).
// I consigli vengono dai suggested_params reali (vedi lib/advice.ts). Tutto punta
// alla Console per l'analisi completa. Colore accent solo sulla CTA (azione), niente glow.
import Link from "next/link";
import { buildAdvice } from "@/lib/advice";
import type { SessionData } from "@/lib/telemetry";

export default function GigiAdvice({ data }: { data: SessionData }) {
  const advice = buildAdvice(data);
  const top = advice[0];
  const recent = advice.slice(0, 3);

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

      {/* Mini-elenco: ultimi consigli (fino a 3), non solo l'ultimo */}
      {recent.length > 0 && (
        <div className="mt-2 flex flex-col gap-1">
          <div className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">Ultimi consigli</div>
          {recent.map((a) => (
            <Link
              key={a.key}
              href="/console"
              className="flex items-center gap-2 font-mono text-[0.58rem] text-subtle transition hover:text-white"
              title={`${a.label} · vai alla Console`}
            >
              <span className="h-1 w-1 shrink-0 rounded-full bg-line-strong" />
              <span className="truncate">{a.label}</span>
              <span className="ml-auto shrink-0 text-[0.5rem] uppercase tracking-widest text-muted">{a.group}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
