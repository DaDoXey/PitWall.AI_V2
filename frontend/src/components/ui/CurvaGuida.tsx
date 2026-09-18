"use client";

// La scheda di UNA curva, così come la racconta la guida del tracciato.
//
// Vive in un componente suo perché deve comparire in due posti con lo stesso
// aspetto (decisione del 18/09): nella sezione Tracciati, dove si legge il
// circuito prima di scendere in pista, e in sessione accanto al verdetto del
// motore, dove si legge dopo aver sbagliato. Un lavoro solo, e il pilota
// riconosce la stessa cosa nelle due pagine.
//
// Due cose che questo componente NON fa, per scelta:
//   * non riscrive niente — il testo è quello della guida parola per parola;
//     le guide sono contenuto da mostrare, non contesto da dare all'LLM;
//   * non riempie i buchi — un campo `null` è una riga che non viene disegnata,
//     mai un «n.d.» che sembra un dato.
import type { GuidaCurva } from "@/lib/api";

const STRESS_COLORE: Record<string, string> = {
  alto: "text-accent",
  medio: "text-warn",
  basso: "text-subtle",
};

function Riga({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-t border-line py-2 first:border-t-0 sm:grid sm:grid-cols-[9rem_1fr] sm:gap-4">
      <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted sm:pt-0.5">
        {label}
      </div>
      <div className="mt-0.5 text-sm leading-relaxed text-subtle sm:mt-0">{children}</div>
    </div>
  );
}

/** Titolo della curva: numero, nome se documentato, tipo e marcia. */
export function TitoloCurva({ curva }: { curva: GuidaCurva }) {
  return (
    <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      <span className="font-mono text-xs text-muted">T{curva.n}</span>
      {/* Il nome manca quando nessuna fonte lo documenta: non si inventa. */}
      <span className="font-display text-sm font-bold tracking-wide">
        {curva.nome ?? `Curva ${curva.n}`}
      </span>
      {curva.tipo && (
        <span className="font-mono text-[0.6rem] uppercase tracking-wider text-muted">
          {curva.tipo}
        </span>
      )}
      {curva.marcia_indicativa && (
        <span className="font-mono text-[0.6rem] uppercase tracking-wider text-subtle">
          {curva.marcia_indicativa}
        </span>
      )}
    </span>
  );
}

export default function CurvaGuida({ curva }: { curva: GuidaCurva }) {
  const gomme = curva.gomme ?? null;
  const freni = curva.freni ?? null;
  const limits = curva.track_limits ?? null;
  const sorpasso = curva.sorpasso ?? null;

  return (
    <div className="px-1 pb-1">
      {curva.riferimento_frenata && (
        <Riga label="Riferimento">{curva.riferimento_frenata}</Riga>
      )}
      {curva.insidia && <Riga label="L'insidia">{curva.insidia}</Riga>}
      {curva.costo_errore && <Riga label="Costo dell'errore">{curva.costo_errore}</Riga>}

      {sorpasso && (sorpasso.come || sorpasso.come_ci_si_difende) && (
        <Riga label={sorpasso.possibile ? "Si sorpassa" : "Sorpasso difficile"}>
          {sorpasso.come && <p>{sorpasso.come}</p>}
          {sorpasso.come_ci_si_difende && (
            <p className="mt-1 text-subtle/80">Difesa: {sorpasso.come_ci_si_difende}</p>
          )}
        </Riga>
      )}

      {(gomme?.stress || freni?.stress || limits?.rischio) && (
        <Riga label="Stress">
          <div className="flex flex-wrap gap-x-6 gap-y-1 font-mono text-xs">
            {gomme?.stress && (
              <span>
                <span className="text-muted">gomme </span>
                <span className="text-subtle">{gomme.stress}</span>
              </span>
            )}
            {freni?.stress && (
              <span>
                <span className="text-muted">freni </span>
                <span className={STRESS_COLORE[freni.stress] ?? "text-subtle"}>{freni.stress}</span>
              </span>
            )}
            {limits?.rischio && (
              <span>
                <span className="text-muted">track limits </span>
                <span className={STRESS_COLORE[limits.rischio] ?? "text-subtle"}>
                  {limits.rischio}
                </span>
              </span>
            )}
          </div>
          {(gomme?.note || freni?.note || limits?.note) && (
            <p className="mt-1 text-subtle/80">
              {[gomme?.note, freni?.note, limits?.note].filter(Boolean).join(" · ")}
            </p>
          )}
        </Riga>
      )}

      {curva.differenza_gara_qualifica && (
        <Riga label="Gara / qualifica">{curva.differenza_gara_qualifica}</Riga>
      )}

      {/* La progressione è la parte «corso»: gli stessi metri di pista raccontati
          a tre livelli, così si sa cosa spostare quando il giro pulito c'è già.
          Le guide del blocco 1 non ce l'hanno e semplicemente non la mostrano. */}
      {curva.progressione &&
        (curva.progressione.prendi_il_giro ||
          curva.progressione.guadagni ||
          curva.progressione.al_limite) && (
          <Riga label="Come si spinge">
            <div className="flex flex-col gap-2">
              {(
                [
                  ["Prendi il giro", curva.progressione.prendi_il_giro],
                  ["Guadagni", curva.progressione.guadagni],
                  ["Al limite", curva.progressione.al_limite],
                ] as const
              )
                .filter(([, testo]) => !!testo)
                .map(([titolo, testo], i) => (
                  <div key={titolo} className="flex gap-3">
                    <span className="mt-0.5 font-mono text-[0.55rem] uppercase tracking-widest text-accent">
                      {i + 1}
                    </span>
                    <p>
                      <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                        {titolo} ·{" "}
                      </span>
                      {testo}
                    </p>
                  </div>
                ))}
            </div>
          </Riga>
        )}

      {/* Onestà sulla fonte: i consigli che nessuna fonte documenta sono
          «mestiere», e lo dicono. Il pilota deve poter pesare quello che legge. */}
      {curva.origine === "mestiere" && (
        <div className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-muted">
          consiglio di mestiere
          {curva.confidence ? ` · confidenza ${curva.confidence}` : ""}
        </div>
      )}
    </div>
  );
}
