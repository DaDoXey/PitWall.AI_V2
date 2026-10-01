"use client";

// La radio con Gigi (#060). In onda c'è un messaggio solo: quello della fase ascoltata
// (le altre fasi si raggiungono dalla striscia dei giri o con «La prossima»). Sotto, la
// conversazione: le domande preparate e le risposte che il debrief sa dare da solo; la
// prova (i numeri uno per uno) esce solo chiedendo «Perché?». In fondo la casella per
// scrivere a Gigi, spenta finché non c'è il modello (#061: dal vivo).
import { useEffect, useRef } from "react";
import Link from "next/link";
import Onda from "@/components/console/Onda";
import { DOMANDE, type Domanda, type Messaggio } from "@/lib/debrief";
import { COLORS } from "@/lib/theme";

const CHIP = "rounded-full border border-line-strong bg-surface px-3 py-1.5 text-[0.78rem] text-[#d6d6d6] transition hover:border-accent hover:text-white";

export default function Radio({
  messaggio,
  nomeFase,
  conversazione,
  dalVivo,
  onProssima,
  onDomanda,
}: {
  messaggio: Messaggio | undefined;
  nomeFase?: string;
  conversazione: Messaggio[];
  dalVivo: boolean;
  onProssima: () => void;
  onDomanda: (d: Domanda) => void;
}) {
  const lista = useRef<HTMLDivElement>(null);
  const ultimo = conversazione[conversazione.length - 1]?.id;

  // Arriva una risposta nuova: la conversazione scende in fondo.
  useEffect(() => {
    lista.current?.scrollTo({ top: lista.current.scrollHeight, behavior: "smooth" });
  }, [ultimo]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      {messaggio && (
        <div className="flex shrink-0 flex-col gap-3 rounded-2xl border border-[#3a0b15] bg-[#140609] px-5 py-4">
          <div className="flex items-center gap-2.5">
            <span className="font-mono text-[0.58rem] font-semibold tracking-[0.18em] text-accent">GIGI</span>
            <Onda seme={messaggio.id} barre={30} colore={COLORS.accent} viva />
            {nomeFase && (
              <span className="ml-auto truncate font-mono text-[0.56rem] uppercase tracking-[0.14em] text-muted">{nomeFase}</span>
            )}
          </div>
          <p className="text-[1.2rem] font-medium leading-snug text-white">{messaggio.testo}</p>
          {messaggio.collegamenti && messaggio.collegamenti.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {messaggio.collegamenti.map((c) => (
                <Link
                  key={c.href}
                  href={c.href}
                  className="rounded-full border border-line-strong px-2.5 py-0.5 text-[0.72rem] text-[#cfcfcf] transition hover:border-accent hover:text-white"
                >
                  {c.etichetta} →
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex shrink-0 flex-wrap gap-1.5">
        <button type="button" onClick={onProssima} className={CHIP}>
          La prossima
        </button>
        {DOMANDE.map((d) => (
          <button key={d.id} type="button" onClick={() => onDomanda(d.id)} className={CHIP}>
            {d.testo}
          </button>
        ))}
      </div>

      <div ref={lista} className="pw-scroll -mx-1 flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto px-1">
        {conversazione.map((m) =>
          m.da === "tu" ? (
            <p key={m.id} className="ml-10 self-end rounded-2xl rounded-br-md bg-raised px-3.5 py-1.5 text-[0.88rem] text-white">
              {m.testo}
            </p>
          ) : (
            <div key={m.id} className="mr-10 flex flex-col gap-1 self-start rounded-2xl rounded-bl-md border border-line px-3.5 py-2">
              <span className="font-mono text-[0.54rem] font-semibold tracking-[0.18em] text-accent">GIGI</span>
              <p className="text-[0.9rem] leading-snug text-[#e6e6e6]">{m.testo}</p>
              {m.prova && <p className="font-mono text-[0.68rem] leading-relaxed text-[#9a9a9a]">{m.prova}</p>}
            </div>
          ),
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2.5 rounded-full border border-line bg-[#0e0e0e] py-1 pl-4 pr-1">
        <label htmlFor="radio-gigi" className="sr-only">
          Scrivi a Gigi
        </label>
        <input
          id="radio-gigi"
          type="text"
          disabled={!dalVivo}
          placeholder={dalVivo ? "Scrivi a Gigi…" : "Gigi dal vivo è spento · usa le domande qui sopra"}
          className="min-w-0 flex-1 bg-transparent py-1.5 text-[0.85rem] text-white placeholder:text-muted focus:outline-none disabled:cursor-not-allowed"
        />
        <button
          type="button"
          disabled={!dalVivo}
          aria-label="Premi per parlare"
          title={dalVivo ? "Premi per parlare" : "Arriva con Gigi dal vivo"}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent transition hover:bg-accent-hover disabled:opacity-40"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <rect x="9" y="3" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0" />
            <path d="M12 18v3" />
          </svg>
        </button>
      </div>
    </div>
  );
}
