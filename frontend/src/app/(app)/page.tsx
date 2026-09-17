"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageHeader from "@/components/ui/PageHeader";
import { IconConsole, IconSetup, IconTelemetry } from "@/components/ui/NavIcons";
import CountUp from "@/components/ui/CountUp";
import { CarCard, TrackCard } from "@/components/ui/SessionBriefing";
import { CosaRegge, ElencoVerdetto, NoteDati, StatoSessione } from "@/components/ui/Verdetto";
import Sparkline from "@/components/charts/Sparkline";
import { fadeInUp, staggerContainer, useReducedMotion } from "@/lib/motion";
import type { Finestra, Report, Riassunto } from "@/lib/api";
import { useSessione } from "@/lib/sessione";
import { data, ETICHETTA_FONTE_CARBURANTE, ETICHETTA_TIPO, etichettaFonte, giri, numero, RUOTE, tempoGiro } from "@/lib/formato";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE } from "@/lib/instrument";

// Ordine di default delle card KPI. Il drag&drop lo riordina; ordine e taglie
// (normale/estesa) sono persistiti in localStorage (sopravvivono al refresh).
// v2 (L4): KPI nuovi, letti dal report del motore — l'ordine della v1 non vale più.
const KPI_ORDER = ["best", "teorico", "costanza", "degrado", "consumo", "pressione", "temperatura"] as const;
const STORE_KEY = "pw_dashboard_kpi_v2";

export default function Dashboard() {
  const { report, sessione, caricamento, errore, nomi } = useSessione();
  const [order, setOrder] = useState<string[]>([...KPI_ORDER]);
  const [sizes, setSizes] = useState<Set<string>>(new Set()); // KPI "estese" (col-span-2)
  const [selected, setSelected] = useState<string | null>(null); // KPI aperto nel modal
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);
  // Lato del bersaglio puntato dal cursore (fix INC-V2-005): il drop inserisce
  // PRIMA o DOPO la card sorvolata, non "al suo indice".
  const [overSide, setOverSide] = useState<"before" | "after" | null>(null);
  const dragFrom = useRef<number | null>(null);

  // Ripristina ordine/taglie da localStorage (persistenza oltre la sessione).
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return;
      const p = JSON.parse(raw) as { order?: string[]; extended?: string[] };
      if (Array.isArray(p.order)) {
        const valid = p.order.filter((id) => (KPI_ORDER as readonly string[]).includes(id));
        const missing = (KPI_ORDER as readonly string[]).filter((id) => !valid.includes(id));
        setOrder([...valid, ...missing]);
      }
      if (Array.isArray(p.extended)) setSizes(new Set(p.extended));
    } catch {
      /* localStorage non disponibile: si resta sui default */
    }
  }, []);

  if (!report || !sessione)
    return (
      <div>
        <PageHeader title="Dashboard" subtitle="Il verdetto della sessione" />
        <StatoSessione errore={errore} caricamento={caricamento || !report} />
      </div>
    );

  const kpis = buildKpis(report);
  const byId = Object.fromEntries(kpis.map((k) => [k.id, k]));
  const ordered = order.map((id) => byId[id]).filter(Boolean) as Kpi[];
  const openKpi = selected ? byId[selected] : null;

  function persist(o: string[], sz: Set<string>) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ order: o, extended: [...sz] }));
    } catch {
      /* no-op */
    }
  }

  // Riordino (persistito): `insert` è la posizione di INSERZIONE nell'array
  // com'era prima della rimozione (bersaglio + eventuale +1 se lato "after").
  function reorder(insert: number) {
    const from = dragFrom.current;
    dragFrom.current = null;
    setDraggingId(null);
    setOverIndex(null);
    setOverSide(null);
    if (from === null) return;
    if (from < insert) insert -= 1;
    if (from === insert) return;
    const next = [...order];
    const [moved] = next.splice(from, 1);
    next.splice(insert, 0, moved);
    setOrder(next);
    persist(next, sizes);
  }

  function toggleSize(id: string) {
    const next = new Set(sizes);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSizes(next);
    persist(order, next);
  }

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Il verdetto della sessione" />

      <SchedaSessione report={report} sessione={sessione} pista={nomi.pista(report.track)} vettura={nomi.vettura(report.car)} />

      {/* Il verdetto viene prima dei numeri: è la ragione per cui si apre la pagina. */}
      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <Titoletto>Verdetto · ordinato per gravità</Titoletto>
          <ElencoVerdetto voci={report.verdetto} />
        </section>
        <section className="flex flex-col gap-4">
          {report.cosa_regge.length > 0 && (
            <div>
              <Titoletto>Cosa regge</Titoletto>
              <CosaRegge punti={report.cosa_regge} />
            </div>
          )}
          <NoteDati note={report.dati_mancanti} />
        </section>
      </div>

      {/* KPI: ingresso a cascata; ogni card apre il dettaglio in-page e si può trascinare */}
      <div className="mb-1 flex items-baseline justify-between">
        <Titoletto>Indicatori sessione</Titoletto>
        <div className="font-mono text-[0.56rem] uppercase tracking-widest text-muted">trascina per riordinare · click per dettaglio</div>
      </div>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
        // Fallback per gap e "buchi" del grid: drop = inserisci in fondo (INC-V2-005).
        onDragOver={(e) => {
          e.preventDefault();
          if (draggingId === null) return;
          setOverIndex(ordered.length - 1);
          setOverSide("after");
        }}
        onDrop={(e) => {
          e.preventDefault();
          reorder(ordered.length);
        }}
      >
        {ordered.map((k, i) => {
          const extended = sizes.has(k.id);
          const isDragging = draggingId === k.id;
          const isTarget = overIndex === i && draggingId !== null && !isDragging;
          return (
            <motion.div
              key={k.id}
              variants={fadeInUp}
              draggable
              onDragStart={() => {
                dragFrom.current = i;
                setDraggingId(k.id);
              }}
              onDragEnd={() => {
                setDraggingId(null);
                setOverIndex(null);
                setOverSide(null);
              }}
              onDragOver={(e) => {
                e.preventDefault();
                e.stopPropagation();
                const r = e.currentTarget.getBoundingClientRect();
                setOverIndex(i);
                setOverSide(e.clientX < r.left + r.width / 2 ? "before" : "after");
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                reorder(i + (overSide === "after" ? 1 : 0));
              }}
              className={`relative rounded-xl transition ${extended ? "sm:col-span-2" : ""} ${
                isDragging ? "scale-[0.98] opacity-50" : ""
              }`}
            >
              {isTarget && (
                <span
                  aria-hidden="true"
                  className={`pointer-events-none absolute inset-y-1 w-0.5 rounded-full bg-accent ${
                    overSide === "before" ? "-left-[9px]" : "-right-[9px]"
                  }`}
                />
              )}
              <KpiCard kpi={k} extended={extended} onOpen={() => setSelected(k.id)} />
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleSize(k.id);
                }}
                title={extended ? "Riduci" : "Estendi"}
                aria-label={extended ? "Riduci card" : "Estendi card"}
                className="absolute right-2 top-2 z-20 flex h-6 w-6 items-center justify-center rounded border border-line bg-surface/80 font-mono text-xs text-muted transition hover:border-accent hover:text-accent"
              >
                {extended ? "⤡" : "⤢"}
              </button>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Schede di contesto dal catalogo ACC: chi è questa pista e questa vettura. */}
      {(report.track || report.car) && (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
          {report.track && <TrackCard track={report.track} />}
          {report.car && <CarCard car={report.car} />}
        </motion.div>
      )}

      {/* Prossime azioni */}
      <div className="mt-8">
        <Titoletto>Prossime azioni</Titoletto>
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {ACTIONS.map((a) => (
            <motion.div key={a.href} variants={fadeInUp}>
              <ActionCard {...a} />
            </motion.div>
          ))}
        </motion.div>
      </div>

      <AnimatePresence>{openKpi && <KpiModal kpi={openKpi} onClose={() => setSelected(null)} />}</AnimatePresence>
    </div>
  );
}

function Titoletto({ children }: { children: React.ReactNode }) {
  return <div className="mb-2 font-mono text-[0.6rem] uppercase tracking-widest text-muted">{children}</div>;
}

// ─────────────────────────────────────────────
// Scheda della sessione aperta
// ─────────────────────────────────────────────
function SchedaSessione({ report, sessione, pista, vettura }: { report: Report; sessione: Riassunto; pista: string; vettura: string }) {
  const r = report.ritmo;
  const quando = sessione.demo ? null : data(sessione.iniziata_il ?? sessione.importato_il);
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className="mb-6 rounded-xl border border-l-4 border-line border-l-accent bg-surface p-5"
    >
      <div className="flex flex-wrap items-center gap-2 font-mono text-[0.6rem] uppercase tracking-widest text-accent">
        <span>{ETICHETTA_TIPO[report.tipo_sessione] ?? "Sessione"}</span>
        <span className="text-muted">·</span>
        <span className={sessione.demo ? "text-ok" : "text-subtle"}>{etichettaFonte(sessione.fonte, sessione.piattaforma)}</span>
        {report.mescola && (
          <>
            <span className="text-muted">·</span>
            <span className="text-subtle">gomme da {report.mescola}</span>
          </>
        )}
        {quando && (
          <>
            <span className="text-muted">·</span>
            <span className="text-subtle">{quando}</span>
          </>
        )}
      </div>
      <div className="mt-1 font-display text-2xl font-bold">{pista}</div>
      <div className="text-sm text-subtle">{vettura}</div>
      <div className="mt-4 flex flex-wrap gap-x-8 gap-y-3 border-t border-line pt-3 text-sm">
        <Stat
          label="Giri"
          value={`${report.giri_totali}${report.giri_buttati ? ` · ${report.giri_buttati} buttati` : ""}`}
        />
        <Stat label="Miglior giro" value={r.miglior_giro_ms ? `${tempoGiro(r.miglior_giro_ms)} · giro ${r.miglior_giro_numero}` : "—"} color={STATE.best} />
        <Stat label="Giro teorico" value={tempoGiro(r.giro_teorico_ms)} />
        <Stat
          label="Consumo"
          value={
            report.carburante.calcolabile
              ? `${numero(report.carburante.consumo_medio_l_giro, 2)} l/giro${report.carburante.fonte ? ` · ${ETICHETTA_FONTE_CARBURANTE[report.carburante.fonte]}` : ""}`
              : "—"
          }
        />
        <Stat label="Telemetria" value={report.ha_canali ? "sì" : "no"} />
      </div>
    </motion.div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-0.5 font-mono" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// KPI: modello dati. Tutti letti dal report del motore: qui niente medie, niente
// soglie — solo la scelta di cosa mostrare e in che unità.
// ─────────────────────────────────────────────
type Kpi = {
  id: string;
  label: string;
  valueNum: number | null; // null = non calcolabile (si mostra `display` o «—»)
  display?: string; // valore testuale (tempi sul giro) al posto del CountUp
  suffix: string;
  decimals: number;
  note: string;
  detail: string; // "come si calcola" mostrato nel modal
  color: string;
  series?: number[];
  xs?: number[]; // numeri di giro della serie
  refLines?: number[];
  unit?: string; // unità dell'asse del grafico
  refs: string[];
};

function finestraKpi(id: string, label: string, f: Finestra | null, report: Report): Kpi {
  if (!f) {
    const motivo = !report.ha_canali
      ? "Serve la telemetria della sessione"
      : report.mescola !== "asciutto"
        ? "Finestra Kunos solo per gomme da asciutto"
        : "Non misurata";
    return { id, label, valueNum: null, suffix: "", decimals: 0, note: motivo, detail: motivo, color: COLORS.muted, refs: [] };
  }
  const fuori = f.ruote_fuori;
  const nomi = RUOTE.filter((r) => fuori.includes(r.key)).map((r) => r.label);
  return {
    id,
    label,
    valueNum: RUOTE.length - fuori.length,
    suffix: "/4",
    decimals: 0,
    note: fuori.length === 0 ? `Tutte dentro ${f.min}–${f.max} ${f.unita}` : `Fuori: ${nomi.join(", ")}`,
    detail: `Ruote rimaste dentro la finestra indicativa Kunos (${f.min}–${f.max} ${f.unita}) nei giri completi fuori dai box. Una ruota conta «fuori» quando ci passa almeno il 20% del tempo.`,
    color: fuori.length === 0 ? STATE.ok : STATE.warn,
    refs: [
      ...RUOTE.map((r) => `${r.label}: dentro ${numero(f.dentro_pct[r.key], 0)}% · sotto ${numero(f.sotto_pct[r.key], 0)}% · sopra ${numero(f.sopra_pct[r.key], 0)}%`),
      `Fonte: ${f.fonte}`,
    ],
  };
}

function buildKpis(report: Report): Kpi[] {
  const r = report.ritmo;
  const conTempo = report.giri.filter((g) => g.tempo_ms !== null);
  const ritmici = conTempo.filter((g) => g.di_ritmo);
  const gomme = report.gomme_e_freni?.gomme ?? null;
  const d = report.degrado;
  const dalGiro = d.dal_giro ?? 1;
  const giriDegrado = ritmici.filter((g) => g.numero >= dalGiro);
  const conConsumo = report.giri.filter((g) => g.carburante_usato_l !== null);

  return [
    {
      id: "best",
      label: "Miglior giro",
      valueNum: r.miglior_giro_ms,
      display: tempoGiro(r.miglior_giro_ms),
      suffix: "",
      decimals: 0,
      note: r.miglior_giro_ms ? `Giro ${r.miglior_giro_numero} · media ${tempoGiro(r.media_ms)}` : "Nessun giro valido",
      detail: "Il giro valido più veloce della sessione; la media è sui giri di ritmo (entro il +10% dal migliore).",
      color: STATE.best,
      series: conTempo.map((g) => (g.tempo_ms as number) / 1000),
      xs: conTempo.map((g) => g.numero),
      refLines: r.miglior_giro_ms ? [r.miglior_giro_ms / 1000] : undefined,
      unit: "s",
      refs: [`Giri di ritmo: ${report.giri_di_ritmo}`, `Esclusi dal ritmo: ${report.giri_esclusi_dal_ritmo}`],
    },
    {
      id: "teorico",
      label: "Giro teorico",
      valueNum: r.giro_teorico_ms,
      display: tempoGiro(r.giro_teorico_ms),
      suffix: "",
      decimals: 0,
      note:
        r.lasciato_sul_tavolo_ms !== null
          ? `${r.lasciato_sul_tavolo_ms} ms lasciati sul tavolo`
          : r.motivo_teorico ?? "Non calcolabile",
      detail: "Somma dei tuoi tre settori migliori. La differenza con il miglior giro è il tempo che sai già fare ma non hai messo insieme.",
      color: r.lasciato_sul_tavolo_ms === null ? COLORS.muted : r.lasciato_sul_tavolo_ms < 100 ? STATE.ok : STATE.warn,
      refs: [
        ...report.settori.map((s) => `S${s.numero}: migliore ${(s.migliore_ms / 1000).toFixed(3)} s · perdita media ${s.perdita_media_ms} ms`),
        ...(r.giri_per_teorico ? [`Costruito su ${r.giri_per_teorico} giri con tutti i settori`] : []),
      ],
    },
    {
      id: "costanza",
      label: "Costanza",
      valueNum: report.costanza.deviazione_ms,
      suffix: " ms",
      decimals: 0,
      note: report.costanza.deviazione_ms !== null
        ? `${report.costanza.giudizio} · ${numero(report.costanza.percentuale_entro_mezzo_secondo, 0)}% entro 0,5 s`
        : report.costanza.giudizio ?? "Non calcolabile",
      detail: "Deviazione standard dei tempi sui giri di ritmo: quanto assomigli a te stesso giro dopo giro.",
      color: report.costanza.giudizio === "da cronometro" || report.costanza.giudizio === "solida" ? STATE.ok : report.costanza.deviazione_ms === null ? COLORS.muted : STATE.warn,
      series: ritmici.map((g) => (g.delta_migliore_ms ?? 0) / 1000),
      xs: ritmici.map((g) => g.numero),
      refLines: [0],
      unit: "s dal migliore",
      refs: [`Scarto massimo: ${report.costanza.scarto_max_ms ?? "—"} ms`, `Giri entro 0,5 s: ${report.costanza.giri_entro_mezzo_secondo}`],
    },
    {
      id: "degrado",
      label: "Degrado",
      valueNum: d.calcolabile ? d.pendenza_ms_giro : null,
      suffix: " ms/giro",
      decimals: 0,
      note: d.calcolabile ? `Dal giro ${d.dal_giro} · R² ${d.r_quadro}${d.significativo ? " · calo dimostrato" : ""}` : d.motivo ?? "Non calcolabile",
      detail: "Pendenza dei tempi dal giro migliore in poi (regressione lineare). Un calo conta solo se la retta spiega i dati (R² ≥ 0,3).",
      color: !d.calcolabile ? COLORS.muted : d.significativo ? STATE.warn : STATE.ok,
      series: giriDegrado.map((g) => (g.tempo_ms as number) / 1000),
      xs: giriDegrado.map((g) => g.numero),
      unit: "s",
      refs: d.calcolabile ? [`Giri considerati: ${d.giri_considerati}`, `Se continua per 10 giri: ${d.perdita_su_10_giri_ms} ms`] : [],
    },
    {
      id: "consumo",
      label: "Consumo",
      valueNum: report.carburante.calcolabile ? report.carburante.consumo_medio_l_giro : null,
      suffix: " l/giro",
      decimals: 2,
      note: report.carburante.calcolabile
        ? report.carburante.fonte === "manuale"
          ? `Inserito da te: media ripartita su ${giri(report.carburante.giri_misurati)}`
          : report.carburante.fonte === "setup"
            ? "Dal setup: stima salvata da ACC, non misurata"
            : `Misurato su ${giri(report.carburante.giri_misurati)}`
        : report.carburante.motivo ?? "Non calcolabile",
      detail: "Carburante usato giro per giro, misurato dal serbatoio registrato (non stimato).",
      color: report.carburante.calcolabile ? STATE.ok : COLORS.muted,
      series: conConsumo.map((g) => g.carburante_usato_l as number),
      xs: conConsumo.map((g) => g.numero),
      refLines: report.carburante.consumo_medio_l_giro ? [report.carburante.consumo_medio_l_giro] : undefined,
      unit: "l",
      refs: [],
    },
    finestraKpi("pressione", "Pressioni in finestra", gomme?.finestra_pressione ?? null, report),
    finestraKpi("temperatura", "Temperature al core", gomme?.finestra_temperatura ?? null, report),
  ];
}

// Shortcut di navigazione — stesse icone line-style della Sidebar.
const ACTIONS = [
  { href: "/console", icon: IconConsole, label: "Engineer Console", hint: "Chiedi a Gigi della sessione" },
  { href: "/telemetry", icon: IconTelemetry, label: "Telemetria", hint: "Giri, curve, gomme e freni" },
  { href: "/setup", icon: IconSetup, label: "Setup", hint: "I parametri toccati dal verdetto" },
];

// Pallino di stato: pulse discreto quando lo stato richiede attenzione.
function StatusDot({ color, pulse }: { color: string; pulse: boolean }) {
  const reduce = useReducedMotion();
  if (!pulse || reduce) return <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />;
  return (
    <motion.span
      className="h-1.5 w-1.5 shrink-0 rounded-full"
      style={{ background: color }}
      animate={{ opacity: [1, 0.35, 1], scale: [1, 1.25, 1] }}
      transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

function ValoreKpi({ kpi, size }: { kpi: Kpi; size: string }) {
  return (
    <div className={`block font-mono ${size}`} style={{ color: kpi.valueNum === null ? COLORS.muted : kpi.color }}>
      {kpi.valueNum === null ? "—" : kpi.display ?? <CountUp value={kpi.valueNum} decimals={kpi.decimals} suffix={kpi.suffix} />}
    </div>
  );
}

// Card KPI: in formato normale mostra la sparkline; in formato ESTESO lo stesso
// grafico della modale (KpiChart condiviso) — statico, il click apre la modale.
function KpiCard({ kpi, extended, onOpen }: { kpi: Kpi; extended: boolean; onOpen: () => void }) {
  const { label, note, color, series, refLines } = kpi;
  const attenzione = color === STATE.warn || color === STATE.alarm;
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group flex h-full w-full cursor-pointer flex-col justify-start rounded-xl border border-line bg-surface p-4 text-left transition duration-200 hover:-translate-y-1 hover:border-accent/50 hover:shadow-[0_12px_30px_-14px_rgba(232,0,45,0.4)]"
    >
      <div className="pr-7 font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-2">
        <ValoreKpi kpi={kpi} size="text-3xl" />
      </div>
      <div className="mt-2 flex items-center gap-1.5 text-xs" style={{ color: kpi.valueNum === null ? COLORS.subtle : color }}>
        <StatusDot color={kpi.valueNum === null ? COLORS.muted : color} pulse={attenzione} />
        {note}
      </div>
      {series && series.length >= 2 &&
        (extended ? (
          <div className="pointer-events-none mt-3 rounded-lg border border-line bg-inset p-2">
            <KpiChart series={series} xs={kpi.xs} color={color} refLines={refLines} unit={kpi.unit} height={150} showTooltip={false} />
          </div>
        ) : (
          <div className="mt-3">
            <Sparkline data={series} color={color} />
            <div className="mt-1 flex justify-between font-mono text-[0.55rem] text-muted">
              <span>giro {kpi.xs?.[0]}</span>
              <span>giro {kpi.xs?.[kpi.xs.length - 1]}</span>
            </div>
          </div>
        ))}
    </button>
  );
}

// Passo "nice" per l'asse Y (stile MoTeC): arrotonda a 1/2/5×10ⁿ.
function niceStep(range: number): number {
  const raw = (range > 1e-6 ? range : 1) / 4;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  const step = norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10;
  return step * mag;
}

// Grafico dettaglio KPI — COMPONENTE CONDIVISO tra modale e card estesa.
function KpiChart({
  series,
  xs,
  color,
  refLines,
  unit,
  height = 190,
  showTooltip = true,
}: {
  series: number[];
  xs?: number[];
  color: string;
  refLines?: number[];
  unit?: string;
  height?: number;
  showTooltip?: boolean;
}) {
  const rows = series.map((v, i) => ({ i: xs?.[i] ?? i + 1, v }));
  const pool = [...series, ...(refLines ?? [])];
  const lo = Math.min(...pool);
  const hi = Math.max(...pool);
  const pad = (hi - lo) * 0.15 || 1;
  const step = niceStep(hi - lo);
  const dLo = Math.floor((lo - pad) / step) * step;
  const dHi = Math.ceil((hi + pad) / step) * step;
  const ticks: number[] = [];
  for (let t = dLo, n = 0; t <= dHi + 1e-9 && n < 20; t += step, n++) ticks.push(Number(t.toFixed(6)));
  const decimals = step >= 1 ? 0 : step >= 0.1 ? 1 : 2;

  return (
    <div>
      {unit && <div className="mb-1 pl-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">{unit}</div>}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={rows} margin={{ top: 6, right: 16, bottom: 22, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
          <XAxis
            dataKey="i"
            stroke={INSTRUMENT.tick}
            tick={{ fill: COLORS.muted, fontSize: 10 }}
            label={{ value: "Giro", position: "insideBottom", offset: -10, style: { fill: COLORS.muted, fontSize: 10, textAnchor: "middle" } }}
          />
          <YAxis domain={[dLo, dHi]} ticks={ticks} tickFormatter={(n: number) => n.toFixed(decimals)} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={52} />
          {showTooltip && (
            <Tooltip
              contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
              labelFormatter={(l) => `Giro ${l}`}
            />
          )}
          {(refLines ?? []).map((y, idx) => (
            <ReferenceLine key={idx} y={y} stroke={COLORS.muted} strokeDasharray="4 4" strokeWidth={1} />
          ))}
          <Line type="monotone" dataKey="v" name="valore" stroke={color} strokeWidth={2} dot={{ r: 2.5, fill: color, strokeWidth: 0 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Modal dettaglio KPI (in-page): valore + grafico + riferimenti + come si calcola.
function KpiModal({ kpi, onClose }: { kpi: Kpi; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="pw-scroll max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-line bg-surface p-6"
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 16, scale: 0.98 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">{kpi.label}</div>
          <button onClick={onClose} className="font-mono text-sm text-muted transition hover:text-accent" aria-label="Chiudi">
            ✕
          </button>
        </div>
        <div className="mt-2">
          <ValoreKpi kpi={kpi} size="text-4xl" />
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-sm" style={{ color: kpi.valueNum === null ? COLORS.subtle : kpi.color }}>
          <StatusDot color={kpi.valueNum === null ? COLORS.muted : kpi.color} pulse={kpi.color === STATE.warn} />
          {kpi.note}
        </div>

        {kpi.series && kpi.series.length >= 2 && (
          <div className="mt-4 rounded-lg border border-line bg-inset p-3">
            <KpiChart series={kpi.series} xs={kpi.xs} color={kpi.color} refLines={kpi.refLines} unit={kpi.unit} />
          </div>
        )}

        {kpi.refs.length > 0 && (
          <div className="mt-4">
            <div className="mb-1.5 font-mono text-[0.55rem] uppercase tracking-widest text-muted">Riferimenti</div>
            <ul className="flex flex-col gap-1">
              {kpi.refs.map((r, idx) => (
                <li key={idx} className="flex items-center gap-2 font-mono text-[0.72rem] text-subtle">
                  <span className="h-1 w-1 shrink-0 rounded-full bg-line-strong" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="mt-4 border-t border-line pt-3 text-[0.8rem] leading-relaxed text-subtle">{kpi.detail}</p>
      </motion.div>
    </motion.div>
  );
}

function ActionCard({ href, icon: Icon, label, hint }: (typeof ACTIONS)[number]) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 rounded-xl border border-line bg-surface p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent/50"
    >
      <span className="text-muted transition-colors duration-200 group-hover:text-accent">
        <Icon size={20} />
      </span>
      <div className="flex-1">
        <div className="text-sm text-white">{label}</div>
        <div className="font-mono text-[0.62rem] text-muted">{hint}</div>
      </div>
      <span aria-hidden="true" className="font-mono text-sm text-muted transition-colors duration-200 group-hover:text-accent">
        →
      </span>
    </Link>
  );
}
