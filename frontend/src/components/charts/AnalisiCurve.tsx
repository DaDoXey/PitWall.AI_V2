"use client";

// Tab «Curve» della Telemetria (L4, confronto esteso in L5). Due viste:
// 1. il riepilogo per curva del motore (curve ricavate dal profilo di velocità, perdita
//    rispetto al tuo miglior passaggio su quel tratto);
// 2. due giri sovrapposti SULLA DISTANZA (velocità, freno, gas, delta tempo), dalla rotta
//    `/tracce`: nel tempo due giri scivolerebbero, sulla stessa griglia di posizione no.
//    Il giro B può venire da un'ALTRA sessione con la stessa vettura e la stessa pista —
//    tipicamente un giro di riferimento importato da MoTeC (L5 · Fase 4).
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getBundle, getTracce, type Report, type Riassunto, type Tracce } from "@/lib/api";
import { etichettaFonte, numero, secondi, tempoGiro } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { useSessione } from "@/lib/sessione";
import { COLORS } from "@/lib/theme";
import { Riquadro } from "@/components/charts/GiriSessione";

const COLORE_B = COLORS.blue;
const CANALI = ["physics.speedKmh", "physics.brake", "physics.gas", "pitwall.tempo_ms"];
const PUNTI = 800;

export default function AnalisiCurve({ report, idSessione }: { report: Report; idSessione: string }) {
  const curve = report.curve;
  const motivo =
    report.dati_mancanti.find((d) => d.startsWith("analisi per curva")) ??
    (report.ha_canali
      ? "Analisi per curva non disponibile."
      : "Questa sessione non ha la telemetria: le curve si ricavano dai canali registrati su PC (velocità e posizione in pista).");

  return (
    <div className="flex flex-col gap-4">
      {curve ? (
        <TabellaCurve report={report} />
      ) : (
        <Riquadro titolo="Curve">
          <p className="text-sm text-subtle">{motivo}</p>
        </Riquadro>
      )}
      {/* Il confronto non ha bisogno dell'analisi per curva: basta un giro con i canali. */}
      {report.ha_canali && <Confronto report={report} idSessione={idSessione} />}
    </div>
  );
}

function TabellaCurve({ report }: { report: Report }) {
  const curve = report.curve!;
  const perNumero = new Map(curve.curve.map((c) => [c.numero, c]));
  const peggiore = Math.max(...curve.riepilogo.map((r) => r.perdita_media_ms));

  return (
    <Riquadro titolo={`Curve riconosciute · ${curve.curve.length}`}>
      <div className="pw-scroll overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse font-mono text-[0.78rem]">
          <thead>
            <tr className="border-b border-line text-left text-[0.58rem] uppercase tracking-widest text-muted">
              <th className="py-2 pr-3">Curva</th>
              <th className="py-2 pr-3">Apice</th>
              <th className="py-2 pr-3">Tratto migliore</th>
              <th className="py-2 pr-3">Tratto medio</th>
              <th className="py-2 pr-3">Perdita media</th>
              <th className="py-2 pr-3">V-min migliore / media</th>
              <th className="py-2">Dispersione frenata</th>
            </tr>
          </thead>
          <tbody>
            {curve.riepilogo.map((r) => {
              const c = perNumero.get(r.curva);
              return (
                <tr key={r.curva} className="border-b border-line/60">
                  <td className="py-1.5 pr-3 text-white">C{r.curva}</td>
                  <td className="py-1.5 pr-3 text-subtle">{c?.apice_m !== null && c?.apice_m !== undefined ? `${numero(c.apice_m, 0)} m` : "—"}</td>
                  <td className="py-1.5 pr-3" style={{ color: STATE.best }}>{secondi(r.tempo_migliore_ms)}</td>
                  <td className="py-1.5 pr-3 text-white">{secondi(r.tempo_medio_ms)}</td>
                  <td className="py-1.5 pr-3" style={{ color: r.perdita_media_ms === peggiore && peggiore > 0 ? STATE.warn : COLORS.subtle }}>
                    {numero(r.perdita_media_ms, 0)} ms
                  </td>
                  <td className="py-1.5 pr-3 text-subtle">
                    {numero(r.velocita_minima_migliore, 0)} / {numero(r.velocita_minima_media, 0)} km/h
                  </td>
                  <td className="py-1.5 text-subtle">
                    {r.dispersione_frenata !== null ? `${numero(r.dispersione_frenata, 1)} ${curve.lunghezza_stimata_m ? "m" : ""}` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[0.7rem] text-muted">
        Le curve sono ricavate dal profilo di velocità, non da una mappa. Perdita = tempo medio sul tratto meno il tuo
        passaggio migliore sullo stesso tratto. Tracciato stimato {curve.lunghezza_stimata_m ? `${numero(curve.lunghezza_stimata_m / 1000, 3)} km` : "—"}.
      </p>
    </Riquadro>
  );
}

type GiroScelta = { numero: number; tempo_ms: number | null; migliore?: boolean };

function Confronto({ report, idSessione }: { report: Report; idSessione: string }) {
  const { elenco, nomi } = useSessione();
  const questa = elenco?.find((s) => s.id === idSessione) ?? null;
  const giriQui: GiroScelta[] = report.giri.filter((g) => g.tempo_ms !== null && !g.in_pit);
  const migliore = report.ritmo.miglior_giro_numero ?? giriQui[0]?.numero ?? null;
  // Il giro B di partenza è l'ultimo di ritmo: di solito racconta lo stint che cala.
  const ultimoDiRitmo =
    [...report.giri].reverse().find((g) => g.tempo_ms !== null && !g.in_pit && g.di_ritmo && g.numero !== migliore)?.numero ?? null;

  // Le sessioni con cui ha senso confrontarsi: stessa vettura, stessa pista, con i canali.
  const altre = useMemo<Riassunto[]>(
    () =>
      report.car && report.track
        ? (elenco ?? []).filter((s) => s.id !== idSessione && s.ha_canali && s.car === report.car && s.track === report.track)
        : [],
    [elenco, idSessione, report.car, report.track],
  );

  const [giroA, setGiroA] = useState<number | null>(migliore);
  const [fonteB, setFonteB] = useState<string>(idSessione);
  const [giriB, setGiriB] = useState<GiroScelta[]>(giriQui);
  const [giroB, setGiroB] = useState<number | null>(ultimoDiRitmo);
  const [tracceA, setTracceA] = useState<Tracce | null>(null);
  const [tracceB, setTracceB] = useState<Tracce | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  // Al cambio di sessione si riparte dai default: con un giro solo, B è il primo riferimento.
  useEffect(() => {
    setGiroA(migliore);
    if (ultimoDiRitmo === null && altre.length > 0) {
      setFonteB(altre[0].id);
    } else {
      setFonteB(idSessione);
      setGiriB(giriQui);
      setGiroB(ultimoDiRitmo);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idSessione, altre.length]);

  // I giri della sorgente B: di questa sessione dal report, di un'altra dal suo bundle.
  useEffect(() => {
    if (fonteB === idSessione) {
      setGiriB(giriQui);
      setGiroB((g) => (giriQui.some((x) => x.numero === g) ? g : ultimoDiRitmo));
      return;
    }
    let vivo = true;
    getBundle(fonteB)
      .then((b) => {
        if (!vivo) return;
        const giri = b.giri.filter((g) => g.tempo_ms !== null && g.valido && !g.in_pit);
        const best = giri.reduce<number | null>((m, g) => (m === null || (g.tempo_ms ?? Infinity) < m ? g.tempo_ms : m), null);
        setGiriB(giri.map((g) => ({ numero: g.numero, tempo_ms: g.tempo_ms, migliore: g.tempo_ms === best })));
        setGiroB(giri.find((g) => g.tempo_ms === best)?.numero ?? null);
      })
      .catch(() => vivo && setErrore("Giri della sessione di confronto non disponibili"));
    return () => {
      vivo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fonteB, idSessione]);

  useEffect(() => {
    if (giroA === null) return;
    let vivo = true;
    setErrore(null);
    const stessa = fonteB === idSessione;
    const giri = stessa && giroB !== null ? [...new Set([giroA, giroB])] : [giroA];
    getTracce(idSessione, giri, CANALI, PUNTI)
      .then((t) => vivo && setTracceA(t))
      .catch((e) => vivo && setErrore(e instanceof Error ? e.message : "Tracce non disponibili"));
    // Finché i giri dell'altra sessione non sono arrivati, giroB può essere un numero di
    // questa: non si chiede, sarebbe un 404 per niente.
    if (!stessa && giroB !== null && giriB.some((g) => g.numero === giroB)) {
      getTracce(fonteB, [giroB], CANALI, PUNTI)
        .then((t) => vivo && setTracceB(t))
        .catch((e) => vivo && setErrore(e instanceof Error ? e.message : "Tracce di confronto non disponibili"));
    } else {
      setTracceB(null);
    }
    return () => {
      vivo = false;
    };
  }, [idSessione, giroA, fonteB, giroB, giriB]);

  if (giriQui.length === 0) return null;

  const a = tracceA?.giri.find((g) => g.giro === giroA);
  const b =
    fonteB === idSessione
      ? giroB !== giroA
        ? tracceA?.giri.find((g) => g.giro === giroB)
        : undefined
      : tracceB?.giri.find((g) => g.giro === giroB);
  const asse = tracceA?.metri ?? tracceA?.posizione.map((p) => p * 100) ?? [];
  const unita = tracceA?.metri ? "m" : "% giro";
  const tempoA = a?.canali["pitwall.tempo_ms"];
  const tempoB = b?.canali["pitwall.tempo_ms"];
  const righe = asse.map((x, i) => ({
    x,
    va: a?.canali["physics.speedKmh"]?.[i],
    vb: b?.canali["physics.speedKmh"]?.[i],
    fa: a?.canali["physics.brake"]?.[i],
    fb: b?.canali["physics.brake"]?.[i],
    ga: a?.canali["physics.gas"]?.[i],
    gb: b?.canali["physics.gas"]?.[i],
    // Delta B − A in secondi allo stesso punto della pista: sopra zero, B è indietro.
    delta: tempoA && tempoB ? (tempoB[i] - tempoB[0] - (tempoA[i] - tempoA[0])) / 1000 : undefined,
  }));
  const apici = (report.curve?.curve ?? []).map((c) => ({
    n: c.numero,
    x: tracceA?.metri ? c.apice_m : c.apice * 100,
  }));

  const sessioneB = fonteB === idSessione ? questa : altre.find((s) => s.id === fonteB) ?? null;
  const ritaglio = Boolean(questa?.ritaglio_i2 || sessioneB?.ritaglio_i2);
  const deltaFinale = righe.length && righe[righe.length - 1].delta !== undefined ? righe[righe.length - 1].delta : undefined;

  const campo =
    "rounded-md border border-line bg-inset px-2 py-1 text-[0.72rem] normal-case tracking-normal text-white focus:border-accent focus:outline-none";
  const etichetta = "flex items-center gap-2 font-mono text-[0.62rem] uppercase tracking-widest text-muted";
  const opzioni = (giri: GiroScelta[]) =>
    giri.map((g) => (
      <option key={g.numero} value={g.numero}>
        Giro {g.numero} · {tempoGiro(g.tempo_ms)}
        {g.migliore ? " (migliore)" : ""}
      </option>
    ));
  const nomeSessione = (s: Riassunto) =>
    `${etichettaFonte(s.fonte, s.piattaforma)}${s.riferimento ? " · riferimento" : ""}${s.pilota ? ` · ${s.pilota}` : ""} · best ${tempoGiro(s.miglior_giro_ms)}`;

  return (
    <Riquadro
      titolo="Due giri a confronto, sulla distanza"
      azioni={
        <div className="flex flex-wrap gap-3">
          <label className={etichetta}>
            <span className="h-2 w-2 rounded-full" style={{ background: STATE.best }} />A
            <select value={giroA ?? ""} onChange={(e) => setGiroA(Number(e.target.value))} className={campo}>
              {opzioni(giriQui)}
            </select>
          </label>
          <label className={etichetta}>
            <span className="h-2 w-2 rounded-full" style={{ background: COLORE_B }} />B
            <select value={fonteB} onChange={(e) => setFonteB(e.target.value)} className={campo} title="Da quale sessione">
              <option value={idSessione}>Questa sessione</option>
              {altre.map((s) => (
                <option key={s.id} value={s.id}>
                  {nomeSessione(s)}
                </option>
              ))}
            </select>
            <select value={giroB ?? ""} onChange={(e) => setGiroB(Number(e.target.value))} className={campo}>
              {giriB.length === 0 && <option value="">nessun altro giro</option>}
              {opzioni(giriB)}
            </select>
          </label>
        </div>
      }
    >
      {altre.length === 0 && giriQui.length < 2 && (
        <p className="mb-2 text-[0.75rem] text-subtle">
          Un giro solo e nessun&apos;altra sessione di {nomi.vettura(report.car)} a {nomi.pista(report.track)}: importa un
          giro di riferimento (Sessioni → export MoTeC) per avere con chi confrontarti.
        </p>
      )}
      {ritaglio && (
        <p className="mb-2 text-[0.72rem] text-warn">
          Un giro è un ritaglio fatto a mano in MoTeC i2: il suo inizio è dove l&apos;ha tagliato qualcuno, quindi le curve
          possono risultare spostate di qualche decina di metri. Leggi il confronto per tendenze, non al metro.
        </p>
      )}
      {errore ? (
        <p className="text-sm text-warn">{errore}</p>
      ) : !tracceA ? (
        <p className="text-sm text-subtle">Caricamento tracce…</p>
      ) : (
        <div className="flex flex-col gap-1">
          <Pista titolo="Velocità · km/h" righe={righe} linee={[["va", STATE.best], ["vb", COLORE_B]]} altezza={220} apici={apici} unita={unita} />
          {b && tempoA && tempoB && (
            <Pista
              titolo={`Delta B − A · s${deltaFinale !== undefined ? ` · al traguardo ${deltaFinale >= 0 ? "+" : ""}${deltaFinale.toFixed(3)}` : ""}`}
              righe={righe}
              linee={[["delta", COLORS.text]]}
              altezza={110}
              apici={apici}
              unita={unita}
              zero
            />
          )}
          <Pista titolo="Freno · 0-1" righe={righe} linee={[["fa", STATE.best], ["fb", COLORE_B]]} altezza={90} dominio={[0, 1]} apici={apici} unita={unita} />
          <Pista titolo="Gas · 0-1" righe={righe} linee={[["ga", STATE.best], ["gb", COLORE_B]]} altezza={90} dominio={[0, 1]} apici={apici} unita={unita} asseX />
          <p className="mt-1 text-[0.7rem] text-muted">
            Linee verticali: apice delle curve (C1…). I due giri sono ricampionati sugli stessi {PUNTI} punti di posizione;
            {fonteB !== idSessione ? " B viene da un'altra sessione, e la sua posizione in pista può essere ricavata dalla velocità (MoTeC)." : ""}
          </p>
        </div>
      )}
    </Riquadro>
  );
}

function Pista({
  titolo,
  righe,
  linee,
  altezza,
  dominio,
  apici,
  unita,
  asseX,
  zero,
}: {
  titolo: string;
  righe: Record<string, number | undefined>[];
  linee: [string, string][];
  altezza: number;
  dominio?: [number, number];
  apici: { n: number; x: number | null | undefined }[];
  unita: string;
  asseX?: boolean;
  zero?: boolean;
}) {
  const nomeLinea = (chiave: string) => (chiave === "delta" ? "Delta B − A" : chiave.endsWith("a") ? "Giro A" : "Giro B");
  return (
    <div>
      <div className="pl-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">{titolo}</div>
      <ResponsiveContainer width="100%" height={altezza}>
        <LineChart data={righe} margin={{ top: titolo.startsWith("Velocità") ? 16 : 4, right: 12, bottom: asseX ? 18 : 0, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
          <XAxis
            dataKey="x"
            type="number"
            domain={["dataMin", "dataMax"]}
            stroke={INSTRUMENT.tick}
            tick={asseX ? { fill: COLORS.muted, fontSize: 10 } : false}
            height={asseX ? 30 : 4}
            tickFormatter={(v: number) => v.toFixed(0)}
            label={asseX ? { value: unita, position: "insideBottom", offset: -6, style: { fill: COLORS.muted, fontSize: 10 } } : undefined}
          />
          <YAxis domain={dominio ?? ["auto", "auto"]} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={40} />
          <Tooltip
            contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
            labelFormatter={(l: number) => `${l.toFixed(0)} ${unita}`}
            formatter={(v: number, nome: string) => [v?.toFixed(nome === "delta" ? 3 : 2), nomeLinea(nome)]}
          />
          {zero && <ReferenceLine y={0} stroke={INSTRUMENT.tick} />}
          {apici.map((a) =>
            a.x !== null && a.x !== undefined ? (
              <ReferenceLine
                key={a.n}
                x={a.x}
                stroke={INSTRUMENT.track}
                strokeDasharray="3 3"
                label={titolo.startsWith("Velocità") ? { value: `C${a.n}`, position: "top", fill: COLORS.muted, fontSize: 9 } : undefined}
              />
            ) : null,
          )}
          {linee.map(([chiave, colore], i) => (
            <Line key={chiave} type="linear" dataKey={chiave} stroke={colore} strokeWidth={i === 0 ? 1.5 : 1.2} dot={false} isAnimationActive={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
