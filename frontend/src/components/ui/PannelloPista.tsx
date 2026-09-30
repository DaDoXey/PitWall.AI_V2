"use client";

// «La pista» nella colonna di sinistra (Entry #048, scelta di Edoardo del 29/09): lo
// spazio sotto la navigazione è la pista della sessione aperta — la mappa verificata e,
// sotto, DOVE PERDI: le curve che costano di più, in ordine, con lo stesso numero sulla
// mappa. Quando la pista è ancorata, ogni curva porta il nome della guida.
//
// Perché qui: la mappa non compare in nessuna pagina della sessione (solo in Tracciati),
// e il posto dove perdi è la cosa da avere sott'occhio mentre si gira fra Dashboard,
// Telemetria e Setup.
//
// Lo spazio lo decide lo schermo (misurato con un ResizeObserver): la mappa prende la
// sua altezza, l'elenco tante righe quante ne entrano (fino a 5). Tarato e verificato
// sullo schermo di Edoardo (1536×~696 px di pagina): il pannello arriva in fondo alla
// colonna, senza vuoti sopra o sotto.
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAssets } from "@/lib/assets";
import { useSessione } from "@/lib/sessione";
import { STATE } from "@/lib/instrument";
import { perdita } from "@/lib/formato";

// Sotto questa perdita media il motore non ne fa una voce del verdetto: qui neanche.
const PERDITA_MINIMA_MS = 30;
const MAX_RIGHE = 5;
const RIGA = 26; // px di una riga dell'elenco
// Intestazione, margini, cornice della mappa, titolo dell'elenco.
const FISSO = 92; // misurato sullo schermo di Edoardo: 14 + 12 + 16 + 12 + 17 + 20
const MAPPA_MINIMA = 64;
const LARGHEZZA_MAPPA = 192; // colonna 240 − margini 32 − cornice 16

export default function PannelloPista() {
  const { report, catalogo } = useSessione();
  const [zona, setZona] = useState<HTMLDivElement | null>(null);
  const [altezza, setAltezza] = useState(0);
  // Altezza/larghezza della mappa, misurata al caricamento: gli SVG delle mappe dichiarano
  // solo il viewBox, quindi la larghezza è piena e l'altezza la decide il disegno.
  const [rapporto, setRapporto] = useState<number | null>(null);
  const pista = report?.track ? catalogo?.tracks.find((t) => t.id === report.track) : undefined;
  const assets = useAssets("tracks", pista?.id);
  useEffect(() => setRapporto(null), [pista?.id]);

  useEffect(() => {
    if (!zona) return;
    const osserva = new ResizeObserver(([voce]) => setAltezza(voce.contentRect.height));
    osserva.observe(zona);
    return () => osserva.disconnect();
  }, [zona]);

  const contenuto = () => {
    if (!report || !pista || altezza < 70) return null;

    const aggancio = report.aggancio && report.aggancio.curve.length > 0 ? report.aggancio : null;
    const perdite = [...(report.curve?.riepilogo ?? [])]
      .filter((r) => r.perdita_media_ms >= PERDITA_MINIMA_MS)
      .sort((a, b) => b.perdita_media_ms - a.perdita_media_ms);
    const scheda = `/tracciati/${encodeURIComponent(pista.id)}`;
    const mappa = pista.mappa_verificata ? assets.map : undefined;

    // Prima la mappa (con almeno due righe sotto), poi le righe riempiono il resto.
    const naturale = LARGHEZZA_MAPPA * (rapporto ?? 0.6);
    const righeMinime = Math.min(perdite.length || 1, 2);
    let altezzaMappa = mappa ? Math.min(naturale, altezza - FISSO - RIGA * righeMinime) : 0;
    if (altezzaMappa < MAPPA_MINIMA) altezzaMappa = 0;
    const righe = Math.max(0, Math.min(MAX_RIGHE, perdite.length, Math.floor((altezza - FISSO - altezzaMappa) / RIGA)));
    const mostrate = perdite.slice(0, righe);
    const nomeTratto = (curva: number) => (aggancio ? aggancio.tratti[String(curva)] ?? null : null);
    // Il punto sulla mappa di ogni riga: la prima curva della guida del tratto.
    const punto = (curva: number) =>
      aggancio?.curve.filter((c) => c.tratto === curva && c.mappa).sort((a, b) => a.n - b.n)[0]?.mappa ?? null;
    const motivo = report.dati_mancanti.find((d) => d.startsWith("analisi per curva"));

    return (
      <>
        <div className="flex items-baseline justify-between gap-2 px-1">
          <span className="font-mono text-[0.58rem] uppercase tracking-[0.18em] text-muted">La pista</span>
          <Link href={scheda} className="truncate font-mono text-[0.58rem] uppercase tracking-widest text-accent hover:underline">
            {pista.short_name || pista.name} · {pista.ha_guida ? "guida" : "scheda"} →
          </Link>
        </div>

        {altezzaMappa > 0 && (
          <Link
            href={scheda}
            title={`Apri ${pista.short_name || pista.name} in Tracciati`}
            className="flex justify-center rounded-lg bg-[#f4f1ea] p-2 transition hover:opacity-90"
          >
            <div className="relative" style={{ width: rapporto ? Math.min(LARGHEZZA_MAPPA, altezzaMappa / rapporto) : "100%" }}>
              {/* eslint-disable-next-line @next/next/no-img-element -- asset statico locale */}
              <img
                src={mappa}
                alt={`Mappa di ${pista.short_name || pista.name}`}
                className="block h-auto w-full"
                onLoad={(e) => {
                  const r = e.currentTarget.getBoundingClientRect();
                  if (r.width > 0 && r.height > 0) setRapporto(r.height / r.width);
                }}
              />
              {mostrate.slice(0, 3).map((r, i) => {
                const p = punto(r.curva);
                if (!p) return null;
                return (
                  <span
                    key={r.curva}
                    className="absolute -translate-x-1/2 -translate-y-1/2"
                    style={{ left: `${p.x * 100}%`, top: `${p.y * 100}%` }}
                  >
                    {i === 0 && (
                      <span className="absolute inset-0 rounded-full opacity-50 motion-safe:animate-ping" style={{ background: STATE.alarm }} />
                    )}
                    <Numero n={i + 1} primo={i === 0} />
                  </span>
                );
              })}
            </div>
          </Link>
        )}

        <div className="flex flex-col">
          <span className="mb-1 px-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">Dove perdi</span>
          {mostrate.length > 0 ? (
            mostrate.map((r, i) => {
              const nome = nomeTratto(r.curva);
              return (
                <Link
                  key={r.curva}
                  href="/telemetry"
                  title={`C${r.curva}${nome ? ` · ${nome}` : ""}: perdita media a giro. Il dettaglio è in Telemetria → Curve.`}
                  className="flex items-center gap-2 rounded-md px-1 transition hover:bg-raised"
                  style={{ height: RIGA }}
                >
                  <Numero n={i + 1} primo={i === 0} />
                  <span className="min-w-0 flex-1 truncate text-[0.74rem] text-white">
                    C{r.curva}
                    {nome && <span className="text-subtle"> · {nome}</span>}
                  </span>
                  <span className="shrink-0 font-mono text-[0.68rem]" style={{ color: STATE.warn }}>
                    {perdita(r.perdita_media_ms)}
                  </span>
                </Link>
              );
            })
          ) : (
            <span className="px-1 text-[0.7rem] leading-snug text-subtle">
              {motivo
                ? motivo.replace(/^analisi per curva non possibile: /, "Curve non misurabili: ")
                : "Nessuna curva sopra i tre centesimi a giro."}
            </span>
          )}
        </div>
      </>
    );
  };

  const dentro = contenuto();
  return (
    // Nessun margine sul contenitore: vuoto deve valere zero pixel, o ruba spazio alla
    // navigazione sugli schermi bassi.
    <div ref={setZona} className="min-h-0 flex-1 basis-0 overflow-hidden">
      {dentro && <div className="flex flex-col gap-3 px-4 pb-3 pt-2">{dentro}</div>}
    </div>
  );
}

/** Il numero di una curva nell'elenco e sulla mappa: il primo in rosso, gli altri scuri. */
function Numero({ n, primo }: { n: number; primo: boolean }) {
  return (
    <span
      className="relative flex h-4 w-4 shrink-0 items-center justify-center rounded-full font-mono text-[0.55rem] font-bold text-white ring-1 ring-white/80"
      style={{ background: primo ? STATE.alarm : "#3a3a3f" }}
    >
      {n}
    </span>
  );
}
