"use client";

// Tab «Curve» della Telemetria (L4, confronto esteso in L5). Due viste:
// 1. il riepilogo per curva del motore (curve ricavate dal profilo di velocità, perdita
//    rispetto al tuo miglior passaggio su quel tratto);
// 2. due giri sovrapposti SULLA DISTANZA (velocità, freno, gas, delta tempo), dalla rotta
//    `/tracce`: nel tempo due giri scivolerebbero, sulla stessa griglia di posizione no.
//    Il giro B può venire da un'ALTRA sessione con la stessa vettura e la stessa pista —
//    tipicamente un giro di riferimento importato da MoTeC (L5 · Fase 4).
// Aggancio della guida (Entry #047): sulle piste con le ancore ogni tratto del motore
// porta il nome delle curve della guida che contiene, un clic apre la scheda della curva
// con la mappa zoomata, e il confronto segna l'inizio delle curve della guida.
import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  getBundle,
  getCatalogTrack,
  getGuidaTracciato,
  getTracce,
  type Aggancio,
  type GuidaTracciato,
  type Report,
  type Riassunto,
  type Tracce,
} from "@/lib/api";
import { useAssets } from "@/lib/assets";
import CurvaGuida, { TitoloCurva } from "@/components/ui/CurvaGuida";
import { etichettaFonte, numero, perdita, secondi, tempoGiro } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { useSessione } from "@/lib/sessione";
import { COLORS } from "@/lib/theme";
import { Riquadro } from "@/components/charts/GiriSessione";

const COLORE_B = COLORS.blue;
const CANALI = ["physics.speedKmh", "physics.brake", "physics.gas", "pitwall.tempo_ms"];
const PUNTI = 800;
const ZOOM_MAPPA = 2.5;

export default function AnalisiCurve({ report, idSessione }: { report: Report; idSessione: string }) {
  const curve = report.curve;
  const motivo =
    report.dati_mancanti.find((d) => d.startsWith("analisi per curva")) ??
    (report.ha_canali
      ? "Analisi per curva non disponibile."
      : "Questa sessione non ha la telemetria: le curve si ricavano dai canali registrati su PC (velocità e posizione in pista).");

  const guida = useGuidaAgganciata(report.aggancio);

  return (
    <div className="flex flex-col gap-4">
      {report.aggancio?.nota && <InvitoGuida report={report} idSessione={idSessione} nota={report.aggancio.nota} />}
      {curve ? (
        <TabellaCurve report={report} guida={guida} />
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

/** Sulla demo la guida non si aggancia (circuito generato): si dice perché e si offre la
 *  sessione vera della stessa pista con più giri, dove nomi, scheda e zoom ci sono.
 *  Scelta di Edoardo del 29/09: chi entra in demo deve poterli vedere. */
function InvitoGuida({ report, idSessione, nota }: { report: Report; idSessione: string; nota: string }) {
  const { elenco, nomi, apri } = useSessione();
  const vera = (elenco ?? [])
    .filter((s) => s.id !== idSessione && !s.demo && s.ha_canali && s.track === report.track)
    .sort((a, b) => b.giri - a.giri || (b.iniziata_il ?? b.importato_il ?? "").localeCompare(a.iniziata_il ?? a.importato_il ?? ""))[0];
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line border-l-2 border-l-accent bg-inset px-4 py-3">
      <p className="min-w-0 flex-1 text-[0.8rem] leading-snug text-subtle">
        {nota}
        {vera ? " Su una sessione vera della stessa pista trovi la guida curva per curva, con la mappa zoomata." : ""}
      </p>
      {vera && (
        <button
          type="button"
          onClick={() => apri(vera.id)}
          className="shrink-0 rounded-md border border-accent px-3 py-1.5 font-mono text-[0.62rem] uppercase tracking-widest text-white transition hover:bg-accent/15"
        >
          Apri {nomi.pista(vera.track)} · {nomi.vettura(vera.car)} con la guida →
        </button>
      )}
    </div>
  );
}

/** La guida della pista agganciata e la sua mappa, se il layout è verificato. */
function useGuidaAgganciata(aggancio: Aggancio | null) {
  const pista = aggancio && aggancio.curve.length > 0 ? aggancio.pista : undefined;
  const [guida, setGuida] = useState<GuidaTracciato | null>(null);
  const [mappaVerificata, setMappaVerificata] = useState(false);
  const assets = useAssets("tracks", pista);
  useEffect(() => {
    setGuida(null);
    setMappaVerificata(false);
    if (!pista) return;
    let vivo = true;
    getGuidaTracciato(pista)
      .then((g) => vivo && setGuida(g))
      .catch(() => vivo && setGuida(null));
    getCatalogTrack(pista)
      .then((t) => vivo && setMappaVerificata(t.mappa_verificata))
      .catch(() => vivo && setMappaVerificata(false));
    return () => {
      vivo = false;
    };
  }, [pista]);
  // Meglio nessuna mappa che una non verificata: stessa regola della sezione Tracciati.
  return { guida, mappa: mappaVerificata ? assets.map : undefined };
}

type GuidaAgganciata = ReturnType<typeof useGuidaAgganciata>;

function TabellaCurve({ report, guida }: { report: Report; guida: GuidaAgganciata }) {
  const curve = report.curve!;
  const aggancio = report.aggancio && report.aggancio.curve.length > 0 ? report.aggancio : null;
  const perNumero = new Map(curve.curve.map((c) => [c.numero, c]));
  const peggiore = Math.max(...curve.riepilogo.map((r) => r.perdita_media_ms));
  const [scelta, setScelta] = useState<number | null>(null);
  const trattoScelto = aggancio?.curve.find((c) => c.n === scelta)?.tratto ?? null;
  // Il clic su un tratto apre la prima curva della guida che contiene.
  const primaDelTratto = (tratto: number) =>
    aggancio?.curve.filter((c) => c.tratto === tratto).sort((a, b) => a.n - b.n)[0]?.n ?? null;

  return (
    <Riquadro titolo={`Curve riconosciute · ${curve.curve.length}`}>
      <div className="pw-scroll overflow-x-auto">
        <table className={`w-full ${aggancio ? "min-w-[820px]" : "min-w-[640px]"} border-collapse font-mono text-[0.78rem]`}>
          <thead>
            <tr className="border-b border-line text-left text-[0.58rem] uppercase tracking-widest text-muted">
              <th className="py-2 pr-3">Curva</th>
              {aggancio && <th className="py-2 pr-3">Guida</th>}
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
              const nome = aggancio?.tratti[String(r.curva)] ?? null;
              const prima = nome ? primaDelTratto(r.curva) : null;
              const attiva = trattoScelto === r.curva;
              return (
                <tr
                  key={r.curva}
                  onClick={prima !== null ? () => setScelta(attiva ? null : prima) : undefined}
                  className={`border-b border-line/60 ${prima !== null ? "cursor-pointer transition hover:bg-raised" : ""} ${attiva ? "bg-raised" : ""}`}
                  aria-selected={attiva}
                >
                  <td className="py-1.5 pr-3 text-white">C{r.curva}</td>
                  {aggancio && (
                    <td className="max-w-[16rem] py-1.5 pr-3 font-sans text-[0.78rem] text-white">
                      {nome ?? <span className="text-muted">—</span>}
                    </td>
                  )}
                  <td className="py-1.5 pr-3 text-subtle">{c?.apice_m !== null && c?.apice_m !== undefined ? `${numero(c.apice_m, 0)} m` : "—"}</td>
                  <td className="py-1.5 pr-3" style={{ color: STATE.best }}>{secondi(r.tempo_migliore_ms)}</td>
                  <td className="py-1.5 pr-3 text-white">{secondi(r.tempo_medio_ms)}</td>
                  <td className="py-1.5 pr-3" style={{ color: r.perdita_media_ms === peggiore && peggiore > 0 ? STATE.warn : COLORS.subtle }}>
                    {perdita(r.perdita_media_ms)}
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
        {aggancio && " Guida: le curve della guida il cui apice cade nel tratto. Clic su una riga per la scheda della curva."}
      </p>
      {aggancio && scelta !== null && <SchedaGuida aggancio={aggancio} n={scelta} onCambia={setScelta} guida={guida} />}
    </Riquadro>
  );
}

/** La scheda di una curva della guida: la mappa zoomata sul punto dell'ancora e il testo
 *  della guida, con le frecce per scorrere le curve nell'ordine della guida. */
function SchedaGuida({
  aggancio,
  n,
  onCambia,
  guida,
}: {
  aggancio: Aggancio;
  n: number;
  onCambia: (n: number | null) => void;
  guida: GuidaAgganciata;
}) {
  const ordinate = [...aggancio.curve].sort((a, b) => a.n - b.n);
  const i = ordinate.findIndex((c) => c.n === n);
  const curva = ordinate[i];
  if (!curva) return null;
  const testo = guida.guida?.curve?.find((g) => g.n === n) ?? null;
  const prec = ordinate[i - 1];
  const succ = ordinate[i + 1];
  const freccia =
    "rounded-md border border-line px-2.5 py-1 font-mono text-sm text-subtle transition hover:border-accent hover:text-white disabled:opacity-30 disabled:hover:border-line disabled:hover:text-subtle";
  const conMappa = Boolean(guida.mappa && curva.mappa);

  return (
    <div className="mt-4 rounded-lg border border-line bg-inset p-3">
      <div className="flex items-center gap-3">
        <button className={freccia} disabled={!prec} onClick={() => prec && onCambia(prec.n)} aria-label="Curva precedente">
          ←
        </button>
        <div className="min-w-0 flex-1">
          {testo ? (
            <TitoloCurva curva={testo} />
          ) : (
            <span className="font-display text-sm font-bold">
              T{curva.n} {curva.nome ?? ""}
            </span>
          )}
          {curva.tratto !== null && (
            <span className="ml-2 font-mono text-[0.6rem] uppercase tracking-widest text-muted">nel tratto C{curva.tratto}</span>
          )}
        </div>
        <button className={freccia} disabled={!succ} onClick={() => succ && onCambia(succ.n)} aria-label="Curva successiva">
          →
        </button>
        <button className={freccia} onClick={() => onCambia(null)} aria-label="Chiudi la scheda">
          ✕
        </button>
      </div>
      <div className={`mt-3 grid gap-4 ${conMappa ? "md:grid-cols-[minmax(0,20rem)_1fr]" : ""}`}>
        {conMappa && <MappaZoom src={guida.mappa!} x={curva.mappa!.x} y={curva.mappa!.y} alt={`Mappa del circuito, curva T${curva.n}`} />}
        <div className="min-w-0">
          {testo ? (
            <CurvaGuida curva={testo} />
          ) : (
            <p className="text-sm text-subtle">{guida.guida ? "La guida non descrive questa curva." : "Caricamento della guida…"}</p>
          )}
        </div>
      </div>
    </div>
  );
}

/** La mappa verificata ingrandita sul punto dell'ancora, che resta al centro del riquadro.
 *  Il riquadro prende le proporzioni dell'immagine (larghezza piena, altezza automatica):
 *  così le frazioni x/y dell'ancora cadono sul disegno e non su una banda vuota. */
function MappaZoom({ src, x, y, alt }: { src: string; x: number; y: number; alt: string }) {
  return (
    <div className="self-start overflow-hidden rounded-lg bg-[#f4f1ea]">
      <div
        className="relative transition-transform duration-300 ease-out"
        style={{
          transformOrigin: `${x * 100}% ${y * 100}%`,
          transform: `translate(${(0.5 - x) * 100}%, ${(0.5 - y) * 100}%) scale(${ZOOM_MAPPA})`,
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- asset statico locale */}
        <img src={src} alt={alt} className="block h-auto w-full" />
        <span
          className="absolute h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-1 ring-white"
          style={{ left: `${x * 100}%`, top: `${y * 100}%`, background: STATE.alarm }}
        />
      </div>
    </div>
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
    // Pedali in una traccia sola: gas sopra lo zero, freno sotto (in negativo).
    fa: negativo(a?.canali["physics.brake"]?.[i]),
    fb: negativo(b?.canali["physics.brake"]?.[i]),
    ga: a?.canali["physics.gas"]?.[i],
    gb: b?.canali["physics.gas"]?.[i],
    // Delta B − A in secondi allo stesso punto della pista: sopra zero, B è indietro.
    delta: tempoA && tempoB ? (tempoB[i] - tempoB[0] - (tempoA[i] - tempoA[0])) / 1000 : undefined,
  }));
  // Con la guida agganciata le linee segnano l'INIZIO delle sue curve (dove si frena, o si
  // inserisce se la curva è in pieno), sulla stessa scala dell'asse; senza, come prima,
  // l'apice dei tratti del motore.
  const curveGuida =
    report.aggancio && report.aggancio.curve.length > 0 ? [...report.aggancio.curve].sort((p, q) => p.n - q.n) : null;
  const lunghezza = tracceA?.lunghezza_stimata_m ?? null;
  const apici = curveGuida
    ? curveGuida.map((c) => ({
        chiave: `T${c.n}`,
        nome: c.nome,
        x: tracceA?.metri && lunghezza ? c.inizio * lunghezza : c.inizio * 100,
        fine: tracceA?.metri && lunghezza ? c.uscita * lunghezza : c.uscita * 100,
      }))
    : (report.curve?.curve ?? []).map((c) => ({
        chiave: `C${c.numero}`,
        nome: null,
        fine: null,
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
          <Pista
            titolo="Pedali · gas sopra, freno sotto · 0-1"
            righe={righe}
            linee={[["ga", STATE.best], ["gb", COLORE_B], ["fa", STATE.best], ["fb", COLORE_B]]}
            altezza={130}
            dominio={[-1, 1]}
            apici={apici}
            unita={unita}
            asseX
            zero
          />
          <p className="mt-1 text-[0.7rem] text-muted">
            {curveGuida
              ? "Linee verticali: inizio delle curve della guida (T1…); passa sul grafico per il nome della curva."
              : "Linee verticali: apice delle curve (C1…)."}{" "}
            I due giri sono ricampionati sugli stessi {PUNTI} punti di posizione
            {fonteB !== idSessione ? "; B viene da un'altra sessione, e la sua posizione in pista può essere ricavata dalla velocità (MoTeC)." : "."}
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
  apici: { chiave: string; nome: string | null; x: number | null | undefined; fine: number | null }[];
  unita: string;
  asseX?: boolean;
  zero?: boolean;
}) {
  const giro = (chiave: string) => (chiave.endsWith("a") ? "A" : "B");
  const nomeLinea = (chiave: string) =>
    chiave === "delta"
      ? "Delta B − A"
      : chiave.startsWith("f")
        ? `Freno ${giro(chiave)}`
        : chiave.startsWith("g")
          ? `Gas ${giro(chiave)}`
          : `Giro ${giro(chiave)}`;
  // Nel tooltip, accanto ai metri, la curva della guida in cui si è: fra il suo inizio e
  // la sua uscita (sul rettilineo niente nome).
  const curvaA = (x: number) => {
    const c = apici.find((a) => a.x !== null && a.x !== undefined && a.fine !== null && a.x <= x && x <= a.fine);
    return c ? ` · ${c.chiave}${c.nome ? ` ${c.nome}` : ""}` : "";
  };
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
          <YAxis
            domain={dominio ?? ["auto", "auto"]}
            stroke={INSTRUMENT.tick}
            tick={{ fill: COLORS.muted, fontSize: 10 }}
            width={40}
            tickFormatter={(v: number) => (dominio?.[0] === -1 ? Math.abs(v).toString() : v.toString())}
          />
          <Tooltip
            contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
            labelFormatter={(l: number) => `${l.toFixed(0)} ${unita}${curvaA(l)}`}
            formatter={(v: number, nome: string) => [
              (nome.startsWith("f") ? Math.abs(v) : v)?.toFixed(nome === "delta" ? 3 : 2),
              nomeLinea(nome),
            ]}
          />
          {zero && <ReferenceLine y={0} stroke={INSTRUMENT.tick} />}
          {apici.map((a) =>
            a.x !== null && a.x !== undefined ? (
              <ReferenceLine
                key={a.chiave}
                x={a.x}
                stroke={INSTRUMENT.track}
                strokeDasharray="3 3"
                label={titolo.startsWith("Velocità") ? { value: a.chiave, position: "top", fill: COLORS.muted, fontSize: 9 } : undefined}
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

// Il freno disegnato sotto lo zero nella traccia dei pedali.
function negativo(v: number | undefined): number | undefined {
  return v === undefined ? undefined : -v;
}
