"use client";

// La striscia dei giri della Engineer Console (#060): le fasi del debrief sopra, i giri
// sotto con lo scarto dal migliore. Una fase si ascolta con un clic; fra un giro e
// l'altro c'è una fessura: un clic taglia lì una fase nuova (o unisce due fasi). Il
// play fa scorrere le fasi come un replay commentato.
import { Fragment } from "react";
import type { Debrief, TipoFase } from "@/lib/api";
import { tempoGiro } from "@/lib/formato";
import { COLORS } from "@/lib/theme";

export const COLORE_FASE: Record<TipoFase, string> = {
  avvio: "#bdbdbd",
  giro: COLORS.best,
  calo: COLORS.accent,
  tenuta: COLORS.ok,
};

const ALTEZZA_BARRA = 34;

export default function StrisciaGiri({
  debrief,
  attiva,
  inRiproduzione,
  occupato,
  onFase,
  onPlay,
  onTaglio,
  onFasiDiGigi,
}: {
  debrief: Debrief;
  attiva: number;
  inRiproduzione: boolean;
  occupato: boolean;
  onFase: (i: number) => void;
  onPlay: () => void;
  onTaglio: (giro: number) => void;
  onFasiDiGigi: () => void;
}) {
  const perNumero = new Map(debrief.giri.map((g) => [g.numero, g]));
  const massimo = Math.max(1, ...debrief.giri.map((g) => g.delta_ms));

  const fessura = (giro: number, tagliata: boolean) => (
    <button
      type="button"
      key={`t-${giro}`}
      onClick={() => onTaglio(giro)}
      disabled={occupato}
      title={tagliata ? `Unisci: togli il taglio prima del giro ${giro}` : `Taglia qui: una fase nuova dal giro ${giro}`}
      aria-label={tagliata ? `Togli il taglio prima del giro ${giro}` : `Taglia una fase nuova dal giro ${giro}`}
      className="group relative flex w-3 shrink-0 cursor-pointer justify-center self-stretch disabled:cursor-wait"
    >
      <span
        className={`transition group-hover:w-0.5 group-hover:bg-white ${tagliata ? "w-0.5 bg-accent" : "w-px bg-transparent"}`}
      />
    </button>
  );

  return (
    <div
      className="rounded-2xl border border-line bg-surface px-3 pb-2.5 pt-3"
      title={`Clic su una fase per ascoltarla · clic fra due giri per tagliare o unire le fasi${
        debrief.fuori_ritmo.length ? ` · fuori ritmo: ${debrief.fuori_ritmo.map((n) => `G${n}`).join(", ")}` : ""
      }`}
    >
      <div className="flex items-start gap-3">
        <button
          type="button"
          onClick={onPlay}
          disabled={debrief.fasi.length < 2}
          aria-label={inRiproduzione ? "Metti in pausa il debrief" : "Riascolta il debrief"}
          title={inRiproduzione ? "Pausa" : "Riascolta il debrief, fase per fase"}
          className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent text-[0.7rem] text-white transition hover:bg-accent-hover disabled:opacity-40"
        >
          {inRiproduzione ? "❚❚" : "▶"}
        </button>

        <div className="flex min-w-0 flex-1">
          {debrief.fasi.map((f, i) => {
            const on = i === attiva;
            const colore = COLORE_FASE[f.tipo];
            return (
              <Fragment key={`${i}-${f.giri[0]}`}>
                {i > 0 && fessura(f.giri[0], true)}
                <div className="flex min-w-0 flex-col gap-1.5" style={{ flexGrow: f.giri.length, flexBasis: 0 }}>
                  <button
                    type="button"
                    onClick={() => onFase(i)}
                    className="truncate border-b-2 pb-1 text-left font-mono text-[0.58rem] uppercase tracking-[0.14em] transition"
                    style={{ borderColor: on ? colore : "#2a2a2a", color: on ? colore : "#6a6a6a" }}
                    title={`Ascolta: ${f.nome}`}
                  >
                    {f.nome}
                  </button>
                  <div className="flex">
                    {f.giri.map((n, j) => {
                      const g = perNumero.get(n);
                      const alt = g?.migliore ? 3 : Math.max(3, Math.round(((g?.delta_ms ?? 0) / massimo) * ALTEZZA_BARRA));
                      return (
                        <Fragment key={n}>
                          {j > 0 && fessura(n, false)}
                          <button
                            type="button"
                            onClick={() => onFase(i)}
                            className="flex min-w-0 flex-1 flex-col gap-1"
                            title={
                              g
                                ? `Giro ${n} · ${tempoGiro(g.tempo_ms)}${g.migliore ? " · il tuo migliore" : ` · +${(g.delta_ms / 1000).toFixed(3)} s dal migliore`}`
                                : `Giro ${n}`
                            }
                          >
                            <span className="flex w-full items-end" style={{ height: ALTEZZA_BARRA }}>
                              <span
                                className="w-full rounded-sm transition-colors"
                                style={{
                                  height: alt,
                                  background: g?.migliore ? COLORS.best : on ? (f.tipo === "calo" ? COLORS.warn : "#8a8a8a") : "#2a2a2a",
                                }}
                              />
                            </span>
                            <span
                              className="truncate font-mono text-[0.58rem]"
                              style={{ color: g?.migliore ? COLORS.best : on ? COLORS.text : COLORS.muted }}
                            >
                              {/* Scritto solo il giro migliore: gli altri si leggono dalle barre (tempo nel tooltip). */}
                              {g?.migliore ? tempoGiro(g.tempo_ms) : `G${n}`}
                            </span>
                          </button>
                        </Fragment>
                      );
                    })}
                  </div>
                </div>
              </Fragment>
            );
          })}
        </div>
      </div>

      {debrief.manuale && (
        <div className="mt-1.5 flex justify-end pl-11">
          <button
            type="button"
            onClick={onFasiDiGigi}
            disabled={occupato}
            className="font-mono text-[0.56rem] uppercase tracking-widest text-subtle transition hover:text-white"
          >
            Fasi tagliate da te · torna a quelle di Gigi
          </button>
        </div>
      )}
    </div>
  );
}
