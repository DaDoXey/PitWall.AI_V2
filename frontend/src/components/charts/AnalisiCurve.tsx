"use client";

// Tab «Curve» della Telemetria (L4). Due viste:
// 1. il riepilogo per curva del motore (curve ricavate dal profilo di velocità, perdita
//    rispetto al tuo miglior passaggio su quel tratto);
// 2. due giri sovrapposti SULLA DISTANZA (velocità, freno, gas), dalla rotta
//    `/tracce`: nel tempo due giri scivolerebbero, sulla stessa griglia di posizione no.
import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getTracce, type Report, type Tracce } from "@/lib/api";
import { numero, secondi, tempoGiro } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { COLORS } from "@/lib/theme";
import { Riquadro } from "@/components/charts/GiriSessione";

const COLORE_B = COLORS.blue;

export default function AnalisiCurve({ report, idSessione }: { report: Report; idSessione: string }) {
  const curve = report.curve;
  if (!curve) {
    const motivo =
      report.dati_mancanti.find((d) => d.startsWith("analisi per curva")) ??
      (report.ha_canali
        ? "Analisi per curva non disponibile."
        : "Questa sessione non ha la telemetria: le curve si ricavano dai canali registrati su PC (velocità e posizione in pista).");
    return (
      <Riquadro titolo="Curve">
        <p className="text-sm text-subtle">{motivo}</p>
      </Riquadro>
    );
  }

  const perNumero = new Map(curve.curve.map((c) => [c.numero, c]));
  const peggiore = Math.max(...curve.riepilogo.map((r) => r.perdita_media_ms));

  return (
    <div className="flex flex-col gap-4">
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

      <Confronto report={report} idSessione={idSessione} />
    </div>
  );
}

function Confronto({ report, idSessione }: { report: Report; idSessione: string }) {
  const confrontabili = report.giri.filter((g) => g.tempo_ms !== null && !g.in_pit);
  const migliore = report.ritmo.miglior_giro_numero ?? confrontabili[0]?.numero ?? null;
  // Il giro B di partenza è l'ultimo di ritmo: di solito racconta lo stint che cala.
  const ultimoDiRitmo = [...confrontabili].reverse().find((g) => g.di_ritmo && g.numero !== migliore)?.numero ?? null;
  const [giroA, setGiroA] = useState<number | null>(migliore);
  const [giroB, setGiroB] = useState<number | null>(ultimoDiRitmo);
  const [tracce, setTracce] = useState<Tracce | null>(null);
  const [errore, setErrore] = useState<string | null>(null);

  useEffect(() => {
    setGiroA(migliore);
    setGiroB(ultimoDiRitmo);
    // Al cambio di sessione si riparte dai giri di default.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idSessione]);

  useEffect(() => {
    const giri = [giroA, giroB].filter((g): g is number => g !== null);
    if (giri.length === 0) return;
    let vivo = true;
    setErrore(null);
    getTracce(idSessione, [...new Set(giri)], ["physics.speedKmh", "physics.brake", "physics.gas"], 800)
      .then((t) => vivo && setTracce(t))
      .catch((e) => vivo && setErrore(e instanceof Error ? e.message : "Tracce non disponibili"));
    return () => {
      vivo = false;
    };
  }, [idSessione, giroA, giroB]);

  if (confrontabili.length === 0) return null;

  const trovaGiro = (n: number | null) => tracce?.giri.find((g) => g.giro === n);
  const a = trovaGiro(giroA);
  const b = giroB !== giroA ? trovaGiro(giroB) : undefined;
  const asse = tracce?.metri ?? tracce?.posizione.map((p) => p * 100) ?? [];
  const unita = tracce?.metri ? "m" : "% giro";
  const righe = asse.map((x, i) => ({
    x,
    va: a?.canali["physics.speedKmh"]?.[i],
    vb: b?.canali["physics.speedKmh"]?.[i],
    fa: a?.canali["physics.brake"]?.[i],
    fb: b?.canali["physics.brake"]?.[i],
    ga: a?.canali["physics.gas"]?.[i],
    gb: b?.canali["physics.gas"]?.[i],
  }));
  const apici = (report.curve?.curve ?? []).map((c) => ({
    n: c.numero,
    x: tracce?.metri ? c.apice_m : c.apice * 100,
  }));

  const selettore = (valore: number | null, cambia: (n: number) => void, colore: string, etichetta: string) => (
    <label className="flex items-center gap-2 font-mono text-[0.62rem] uppercase tracking-widest text-muted">
      <span className="h-2 w-2 rounded-full" style={{ background: colore }} />
      {etichetta}
      <select
        value={valore ?? ""}
        onChange={(e) => cambia(Number(e.target.value))}
        className="rounded-md border border-line bg-inset px-2 py-1 text-[0.72rem] normal-case tracking-normal text-white focus:border-accent focus:outline-none"
      >
        {confrontabili.map((g) => (
          <option key={g.numero} value={g.numero}>
            Giro {g.numero} · {tempoGiro(g.tempo_ms)}
            {g.migliore ? " (migliore)" : ""}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <Riquadro
      titolo="Due giri a confronto, sulla distanza"
      azioni={
        <div className="flex flex-wrap gap-3">
          {selettore(giroA, setGiroA, STATE.best, "A")}
          {selettore(giroB, setGiroB, COLORE_B, "B")}
        </div>
      }
    >
      {errore ? (
        <p className="text-sm text-warn">{errore}</p>
      ) : !tracce ? (
        <p className="text-sm text-subtle">Caricamento tracce…</p>
      ) : (
        <div className="flex flex-col gap-1">
          <Pista titolo="Velocità · km/h" righe={righe} chiavi={["va", "vb"]} altezza={220} apici={apici} unita={unita} />
          <Pista titolo="Freno · 0-1" righe={righe} chiavi={["fa", "fb"]} altezza={90} dominio={[0, 1]} apici={apici} unita={unita} />
          <Pista titolo="Gas · 0-1" righe={righe} chiavi={["ga", "gb"]} altezza={90} dominio={[0, 1]} apici={apici} unita={unita} asseX />
          <p className="mt-1 text-[0.7rem] text-muted">
            Linee verticali: apice delle curve (C1…). Canali della registrazione ricampionati su {tracce.punti} punti di
            posizione.
          </p>
        </div>
      )}
    </Riquadro>
  );
}

function Pista({
  titolo,
  righe,
  chiavi,
  altezza,
  dominio,
  apici,
  unita,
  asseX,
}: {
  titolo: string;
  righe: Record<string, number | undefined>[];
  chiavi: [string, string];
  altezza: number;
  dominio?: [number, number];
  apici: { n: number; x: number | null | undefined }[];
  unita: string;
  asseX?: boolean;
}) {
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
            formatter={(v: number, nome: string) => [v?.toFixed(2), nome.endsWith("a") ? "Giro A" : "Giro B"]}
          />
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
          <Line type="linear" dataKey={chiavi[0]} stroke={STATE.best} strokeWidth={1.5} dot={false} isAnimationActive={false} />
          <Line type="linear" dataKey={chiavi[1]} stroke={COLORE_B} strokeWidth={1.2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
