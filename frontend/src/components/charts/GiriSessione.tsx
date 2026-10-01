"use client";

// Tab «Giri» della Telemetria (L4, riordinato nella #051): a sinistra la tabella dei giri
// con il distacco dal migliore disegnato nella cella, a destra i settori. Tutto dal report:
// stato del giro (di ritmo, migliore, box, invalido), delta e perdite per settore sono
// decisi dal motore.
import type { Report } from "@/lib/api";
import { delta, ETICHETTA_FONTE_CARBURANTE, numero, perdita, secondi, tempoGiro } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { COLORS } from "@/lib/theme";

export default function GiriSessione({ report }: { report: Report }) {
  if (report.giri.length === 0) {
    return (
      <Riquadro titolo="Giri">
        <p className="text-sm text-subtle">
          Questa sessione non ha giri misurati: si possono analizzare il setup e il racconto, non i tempi.
        </p>
      </Riquadro>
    );
  }
  // scala delle barre = il distacco più grande fra i giri di ritmo (i fuori ritmo escono dalla scala)
  const scala = Math.max(0, ...report.giri.filter((g) => g.di_ritmo).map((g) => g.delta_migliore_ms ?? 0));
  // senza split in nessun giro (es. MoTeC senza settori) spariscono colonne e riquadro dei settori
  const haSplit = report.giri.some((g) => g.splits_ms.some((v) => v));
  // Il consumo giro per giro è una misura solo dalla shared memory: dal setup o dai litri
  // scritti a mano è lo stesso numero su ogni riga, e la tabella lo deve dire.
  const fonteConsumo = report.carburante.fonte;
  const consumoStimato = fonteConsumo === "setup" || fonteConsumo === "manuale";

  return (
    <div className={`grid items-start gap-4 ${haSplit ? "lg:grid-cols-[minmax(0,1fr)_320px]" : ""}`}>
      <Riquadro titolo="Tempi sul giro">
        <div className="pw-scroll overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse font-mono text-[0.78rem]">
            <thead>
              <tr className="border-b border-line text-left text-[0.58rem] uppercase tracking-widest text-muted">
                <th className="py-2 pr-3">Giro</th>
                <th className="py-2 pr-3">Tempo</th>
                {haSplit && (
                  <>
                    <th className="py-2 pr-3">S1</th>
                    <th className="py-2 pr-3">S2</th>
                    <th className="py-2 pr-3">S3</th>
                  </>
                )}
                <th className="py-2 pr-3">Δ migliore</th>
                <th className="py-2 pr-3">Carburante{consumoStimato && fonteConsumo ? ` · ${ETICHETTA_FONTE_CARBURANTE[fonteConsumo]}` : ""}</th>
                <th className="py-2">Stato</th>
              </tr>
            </thead>
            <tbody>
              {report.giri.map((g) => (
                <tr key={g.numero} className="border-b border-line/60">
                  <td className="py-1.5 pr-3 text-subtle">{g.numero}</td>
                  <td className="py-1.5 pr-3" style={{ color: g.migliore ? STATE.best : g.valido ? COLORS.text : COLORS.muted }}>
                    {tempoGiro(g.tempo_ms)}
                  </td>
                  {haSplit && [0, 1, 2].map((i) => {
                    const settore = report.settori[i];
                    const valore = g.splits_ms[i];
                    const migliore = settore && valore === settore.migliore_ms;
                    return (
                      <td key={i} className="py-1.5 pr-3" style={{ color: migliore ? STATE.best : COLORS.subtle }}>
                        {valore ? (valore >= 60000 ? tempoGiro(valore) : (valore / 1000).toFixed(3)) : "—"}
                      </td>
                    );
                  })}
                  <td className="py-1.5 pr-3 text-subtle">
                    {g.migliore ? "—" : <Distacco ms={g.delta_migliore_ms} scala={scala} diRitmo={g.di_ritmo} />}
                  </td>
                  <td className="py-1.5 pr-3 text-subtle">{g.carburante_usato_l !== null ? `${numero(g.carburante_usato_l, 2)} l` : "—"}</td>
                  <td className="py-1.5">
                    <span className="flex flex-wrap gap-1">
                      {g.migliore && <Stato testo="migliore" colore={STATE.best} />}
                      {/* senza tempo = uscita o rientro a metà pista: non è un errore del pilota */}
                      {!g.valido && g.tempo_ms !== null && <Stato testo="invalido" colore={STATE.alarm} />}
                      {g.tempo_ms === null && <Stato testo="incompleto" colore={COLORS.muted} />}
                      {g.in_pit && <Stato testo="box" colore={COLORS.subtle} />}
                      {g.valido && g.tempo_ms !== null && !g.di_ritmo && <Stato testo="fuori ritmo" colore={COLORS.muted} />}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[0.7rem] text-muted">
          In viola {haSplit ? "il giro e i settori migliori" : "il giro migliore"}. «Fuori ritmo» = oltre il +10% dal migliore: contato, ma escluso da
          medie, costanza e degrado.{!haSplit && " Questa sessione non ha i tempi dei settori."}
          {fonteConsumo === "setup" && " Il carburante è la stima salvata da ACC nel setup, uguale per ogni giro: non è misurato."}
          {fonteConsumo === "manuale" && " Il carburante è la media dei litri che hai scritto, ripartita sui giri: non è misurato giro per giro."}
        </p>
      </Riquadro>

      {haSplit && (
        <Riquadro titolo="Settori">
          {report.settori.length === 0 ? (
            <p className="text-sm text-subtle">{report.ritmo.motivo_teorico ?? "Settori non disponibili."}</p>
          ) : (
            <>
              <ul className="flex flex-col">
                {report.settori.map((s) => (
                  <li key={s.numero} className="border-b border-line/60 py-2 font-mono first:pt-0">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="text-sm text-white">S{s.numero}</span>
                      <span className="text-sm text-warn">
                        {perdita(s.perdita_media_ms)} <span className="text-[0.65rem] text-muted">a giro</span>
                      </span>
                    </div>
                    <div className="mt-1 text-[0.7rem] leading-relaxed text-subtle">
                      migliore <span style={{ color: STATE.best }}>{secondi(s.migliore_ms)}</span> · media {secondi(s.media_ms)}
                    </div>
                    <div className="text-[0.7rem] leading-relaxed text-muted">
                      dispersione {s.deviazione_ms} ms
                      {s.perdita_sul_giro_migliore_ms !== null && (
                        <> · nel migliore {s.perdita_sul_giro_migliore_ms === 0 ? "pari" : delta(s.perdita_sul_giro_migliore_ms)}</>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[0.7rem] text-muted">
                «A giro» = quanto perdi in media sul tuo migliore di quel settore; «nel migliore» = quanto ci ha lasciato il
              giro migliore.
                {report.ritmo.giro_teorico_ms !== null && (
                  <>
                    {" "}Giro teorico {tempoGiro(report.ritmo.giro_teorico_ms)} su {report.ritmo.giri_per_teorico} giri con tutti i
                    settori · {report.ritmo.lasciato_sul_tavolo_ms} ms dal migliore.
                  </>
                )}
              </p>
            </>
          )}
        </Riquadro>
      )}
    </div>
  );
}

// Il distacco dal migliore: il numero e, accanto, una barra in scala sui giri di ritmo.
// Prende il posto del grafico a barre che ripeteva la colonna. I giri fuori ritmo sono
// fuori scala: solo il numero, spento.
function Distacco({ ms, scala, diRitmo }: { ms: number | null; scala: number; diRitmo: boolean }) {
  if (ms === null) return <>—</>;
  if (!diRitmo) return <span className="text-muted">{delta(ms)}</span>;
  const quota = scala > 0 ? Math.min(ms / scala, 1) : 0;
  return (
    <span className="flex items-center gap-2">
      <span className="w-[4.5rem] shrink-0">{delta(ms)}</span>
      <span className="relative h-1.5 w-14 shrink-0 rounded-full" style={{ background: INSTRUMENT.track }}>
        <span
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: `${Math.max(quota * 100, ms > 0 ? 4 : 0)}%`, background: INSTRUMENT.ink }}
        />
      </span>
    </span>
  );
}

function Stato({ testo, colore }: { testo: string; colore: string }) {
  return (
    <span className="rounded border px-1 py-px text-[0.5rem] uppercase tracking-widest" style={{ color: colore, borderColor: `${colore}66` }}>
      {testo}
    </span>
  );
}

export function Riquadro({ titolo, children, azioni }: { titolo: string; children: React.ReactNode; azioni?: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="font-mono text-xs uppercase tracking-wider text-subtle">{titolo}</div>
        {azioni}
      </div>
      {children}
    </div>
  );
}
