"use client";

// La radio con Gigi (#060). In onda c'è un messaggio solo: quello della fase ascoltata
// (le altre fasi si raggiungono dalla striscia dei giri o con «La prossima»). Sotto, la
// conversazione: le domande preparate, con le risposte che il debrief sa dare da solo
// (la prova, numero per numero, esce solo chiedendo «Perché?»), e le domande scritte a
// Gigi dal vivo (#061), con la risposta del modello che arriva pezzo per pezzo.
// La casella è accesa solo se il backend ha la chat dal vivo: senza, restano le
// domande preparate. Con la chat accesa c'è anche il microfono (#075): detta nella
// casella, non invia.
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Onda from "@/components/console/Onda";
import { SectionBody } from "@/components/console/RapportoCompleto";
import type { Domanda, Messaggio } from "@/lib/debrief";
import { accoda, useDettatura } from "@/lib/dettatura";
import { COLORS } from "@/lib/theme";

const CHIP = "rounded-full border border-line-strong bg-surface px-3 py-1.5 text-[0.78rem] text-[#d6d6d6] transition hover:border-accent hover:text-white";
const MAX_CARATTERI = 1000; // come il backend

export default function Radio({
  messaggio,
  nomeFase,
  conversazione,
  domande,
  dalVivo,
  inRisposta,
  domandeDalVivo,
  maxDomande,
  onProssima,
  onDomanda,
  onScrivi,
  onNuova,
}: {
  messaggio: Messaggio | undefined;
  nomeFase?: string;
  conversazione: Messaggio[];
  domande: { id: Domanda; testo: string }[];
  dalVivo: boolean;
  inRisposta: boolean;
  domandeDalVivo: number;
  maxDomande: number;
  onProssima: () => void;
  onDomanda: (d: Domanda) => void;
  onScrivi: (testo: string) => void;
  onNuova: () => void;
}) {
  const lista = useRef<HTMLDivElement>(null);
  const [testo, setTesto] = useState("");
  // Quello che c'era nella casella quando si è acceso il microfono: il dettato si accoda lì.
  const primaDelDettato = useRef("");
  const dettatura = useDettatura((dettato) => setTesto(accoda(primaDelDettato.current, dettato, MAX_CARATTERI)));
  const ultimo = conversazione[conversazione.length - 1];
  const piena = domandeDalVivo >= maxDomande;

  // Arriva un messaggio nuovo, o Gigi sta scrivendo: la conversazione resta in fondo.
  useEffect(() => {
    lista.current?.scrollTo({ top: lista.current.scrollHeight, behavior: inRisposta ? "auto" : "smooth" });
  }, [ultimo?.id, ultimo?.testo.length, inRisposta]);

  const invia = (e: React.FormEvent) => {
    e.preventDefault();
    const domanda = testo.trim();
    if (!domanda || !dalVivo || inRisposta || piena) return;
    dettatura.ferma();
    setTesto("");
    onScrivi(domanda);
  };

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
        {domande.map((d) => (
          <button key={d.id} type="button" onClick={() => onDomanda(d.id)} className={CHIP}>
            {d.testo}
          </button>
        ))}
      </div>

      <div ref={lista} className="pw-scroll -mx-1 flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto px-1">
        {conversazione.map((m) =>
          m.da === "tu" ? (
            <p
              key={m.id}
              className={`ml-10 self-end rounded-2xl rounded-br-md bg-raised px-3.5 py-1.5 text-[0.88rem] ${m.errore ? "text-muted" : "text-white"}`}
            >
              {m.testo}
            </p>
          ) : (
            <div
              key={m.id}
              className={`mr-10 flex flex-col gap-1 self-start rounded-2xl rounded-bl-md border px-3.5 py-2 ${m.errore ? "border-[#4a3a12]" : "border-line"}`}
            >
              <div className="flex items-center gap-2">
                <span className="font-mono text-[0.54rem] font-semibold tracking-[0.18em] text-accent">
                  GIGI{m.dalVivo && !m.errore ? " · DAL VIVO" : ""}
                </span>
                {m.dalVivo && inRisposta && m.id === ultimo?.id && <Onda seme={m.id} barre={12} altezza={10} colore={COLORS.accent} viva />}
              </div>
              {m.testo &&
                (m.dalVivo && !m.errore ? (
                  // Il modello scrive con grassetti ed elenchi: stesso markdown-lite del rapporto.
                  <div className="text-[0.9rem] leading-snug text-[#e6e6e6]">
                    <SectionBody body={m.testo} />
                  </div>
                ) : (
                  <p className={`whitespace-pre-wrap text-[0.9rem] leading-snug ${m.errore ? "text-warn" : "text-[#e6e6e6]"}`}>{m.testo}</p>
                ))}
              {m.prova && <p className="whitespace-pre-line font-mono text-[0.68rem] leading-relaxed text-[#9a9a9a]">{m.prova}</p>}
            </div>
          ),
        )}
      </div>

      {dalVivo && piena ? (
        <div className="flex shrink-0 items-center justify-between gap-3 rounded-full border border-line bg-[#0e0e0e] py-1 pl-4 pr-1">
          <span className="text-[0.82rem] text-subtle">Conversazione piena: {maxDomande} domande a Gigi dal vivo.</span>
          <button
            type="button"
            onClick={onNuova}
            disabled={inRisposta}
            className="shrink-0 rounded-full bg-accent px-4 py-2 text-[0.78rem] font-semibold text-white transition hover:bg-accent-hover disabled:opacity-40"
          >
            Nuova conversazione
          </button>
        </div>
      ) : (
        <form onSubmit={invia} className="flex shrink-0 items-center gap-2.5 rounded-full border border-line bg-[#0e0e0e] py-1 pl-4 pr-1">
          <label htmlFor="radio-gigi" className="sr-only">
            Scrivi a Gigi
          </label>
          <input
            id="radio-gigi"
            type="text"
            value={testo}
            onChange={(e) => setTesto(e.target.value)}
            maxLength={MAX_CARATTERI}
            disabled={!dalVivo}
            autoComplete="off"
            placeholder={
              !dalVivo
                ? "Gigi dal vivo è spento · usa le domande qui sopra"
                : inRisposta
                  ? "Gigi sta rispondendo…"
                  : dettatura.inAscolto
                    ? "Ti ascolto… poi premi Invio"
                    : (dettatura.avviso ?? "Scrivi a Gigi…")
            }
            className="min-w-0 flex-1 bg-transparent py-1.5 text-[0.85rem] text-white placeholder:text-muted focus:outline-none disabled:cursor-not-allowed"
          />
          {dalVivo && dettatura.disponibile && (
            <button
              type="button"
              onClick={() => {
                primaDelDettato.current = testo;
                dettatura.alterna();
              }}
              disabled={inRisposta}
              aria-pressed={dettatura.inAscolto}
              aria-label={dettatura.inAscolto ? "Ferma la dettatura" : "Detta la domanda"}
              title={
                dettatura.inAscolto
                  ? "Ferma la dettatura"
                  : "Detta la domanda: compare qui, poi la invii tu. L'audio lo riconosce il browser, non PitWall."
              }
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border transition disabled:opacity-40 ${
                dettatura.inAscolto ? "pw-ascolto border-accent text-accent" : "border-line-strong text-subtle hover:border-accent hover:text-white"
              }`}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <rect x="9" y="3" width="6" height="11" rx="3" />
                <path d="M5 11a7 7 0 0 0 14 0" />
                <path d="M12 18v3" />
              </svg>
            </button>
          )}
          {dalVivo && (
            <span className="shrink-0 font-mono text-[0.58rem] text-muted" title="Domande a Gigi dal vivo in questa conversazione">
              {domandeDalVivo}/{maxDomande}
            </span>
          )}
          <button
            type="submit"
            disabled={!dalVivo || inRisposta || !testo.trim()}
            aria-label="Invia a Gigi"
            title={dalVivo ? "Invia a Gigi" : "Gigi dal vivo è spento"}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent transition hover:bg-accent-hover disabled:opacity-40"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 19V5" />
              <path d="M5 12l7-7 7 7" />
            </svg>
          </button>
        </form>
      )}
    </div>
  );
}
