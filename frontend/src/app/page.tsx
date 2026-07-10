"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import CountUp from "@/components/ui/CountUp";
import Sparkline from "@/components/charts/Sparkline";
import { fadeInUp, staggerContainer, useReducedMotion } from "@/lib/motion";
import { getSession } from "@/lib/api";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";
import { COLORS } from "@/lib/theme";

// Orizzonte (giri) per la proiezione consumo — assunzione dichiarata, non un dato ACC.
const PROJECTION_LAPS = 5;

// Ordine di default delle card KPI (il drag&drop lo riordina, solo per la sessione).
const KPI_ORDER = ["temp", "press", "fuel", "trend", "spread", "outwin", "proj"] as const;

export default function Dashboard() {
  const [data, setData] = useState<SessionData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [order, setOrder] = useState<string[]>([...KPI_ORDER]);
  const [selected, setSelected] = useState<string | null>(null); // KPI aperto nel modal
  const dragFrom = useRef<number | null>(null);

  useEffect(() => {
    getSession()
      .then(setData)
      .catch(() => setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
  }, []);

  if (err)
    return (
      <div>
        <PageHeader title="Dashboard" subtitle="Riepilogo ultima sessione" />
        <p className="text-sm text-warn">{err}</p>
      </div>
    );
  if (!data)
    return (
      <div>
        <PageHeader title="Dashboard" subtitle="Riepilogo ultima sessione" />
        <p className="text-sm text-subtle">Caricamento…</p>
      </div>
    );

  const s = data.session;
  const kpis = buildKpis(data);
  const byId = Object.fromEntries(kpis.map((k) => [k.id, k]));
  const ordered = order.map((id) => byId[id]).filter(Boolean) as Kpi[];
  const openKpi = selected ? byId[selected] : null;

  // Riordino solo-sessione (useState, nessun localStorage/backend).
  function reorder(to: number) {
    const from = dragFrom.current;
    dragFrom.current = null;
    if (from === null || from === to) return;
    setOrder((prev) => {
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
  }

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Riepilogo ultima sessione" />

      {/* Card sessione */}
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="mb-4 rounded-xl border border-l-4 border-line border-l-accent bg-surface p-5"
      >
        <div className="font-mono text-[0.6rem] uppercase tracking-widest text-accent">Ultima sessione</div>
        <div className="mt-1 font-display text-2xl font-bold">{s.track}</div>
        <div className="text-sm text-subtle">
          {s.car} · {s.car_year} · stint {s.stint.toLowerCase()}
        </div>
        <div className="mt-4 flex flex-wrap gap-8 border-t border-line pt-3 text-sm">
          <Stat label="Giri" value={`${s.laps} · best ${s.best_lap}`} />
          <Stat label="Consumo" value={`${s.fuel_avg_per_lap} L/giro · ${s.fuel_total} L`} />
        </div>
      </motion.div>

      {/* KPI: ingresso a cascata; ogni card apre il dettaglio in-page e si può trascinare */}
      <div className="mb-1 flex items-baseline justify-between">
        <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">Indicatori sessione</div>
        <div className="font-mono text-[0.56rem] uppercase tracking-widest text-muted">trascina per riordinare · click per dettaglio</div>
      </div>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        {ordered.map((k, i) => (
          <motion.div
            key={k.id}
            variants={fadeInUp}
            draggable
            onDragStart={() => (dragFrom.current = i)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => reorder(i)}
          >
            <KpiCard kpi={k} onOpen={() => setSelected(k.id)} />
          </motion.div>
        ))}
      </motion.div>

      {/* Prossime azioni: navigazione a pagina (invariata) */}
      <div className="mt-8">
        <div className="mb-3 font-mono text-[0.6rem] uppercase tracking-widest text-muted">Prossime azioni</div>
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-3 sm:grid-cols-3"
        >
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

// ─────────────────────────────────────────────
// KPI: modello dati (tutti derivati da /api/session, nessuna chiamata nuova)
// ─────────────────────────────────────────────
type Kpi = {
  id: string;
  label: string;
  valueNum: number;
  suffix: string;
  decimals: number;
  note: string;
  detail: string; // "come si calcola" mostrato nel modal
  color: string;
  series?: number[];
};

function buildKpis(d: SessionData): Kpi[] {
  const corners: Corner[] = ["fl", "fr", "rl", "rr"];
  const labelOf = (k: Corner) => TYRE_SERIES.find((t) => t.key === k)?.label ?? k;
  const [lo, hi] = d.pressure.hot_window;
  const winWidth = hi - lo;

  // Gomma più calda + sua serie.
  const hottest = corners.reduce((a, b) => (d.temp.max[b] > d.temp.max[a] ? b : a));
  const hotVal = d.temp.max[hottest];
  const overLimit = hotVal > d.temp.limit;
  const hotSeries = d.temp.series[hottest];
  const tempTrend = (hotSeries[hotSeries.length - 1] - hotSeries[0]) / Math.max(1, hotSeries.length - 1);

  // Pressioni: media, fuori-finestra, spread per-giro.
  const out = corners.filter((k) => d.pressure.hot[k] < lo || d.pressure.hot[k] > hi);
  const anyLow = corners.some((k) => d.pressure.hot[k] < lo);
  const pressSeries = d.pressure.hot_series.fl.map(
    (_, i) => (d.pressure.hot_series.fl[i] + d.pressure.hot_series.fr[i] + d.pressure.hot_series.rl[i] + d.pressure.hot_series.rr[i]) / 4,
  );
  const spreadSeries = d.pressure.hot_series.fl.map((_, i) => {
    const vals = corners.map((k) => d.pressure.hot_series[k][i]);
    return Math.max(...vals) - Math.min(...vals);
  });
  const lastSpread = Math.max(...corners.map((k) => d.pressure.hot[k])) - Math.min(...corners.map((k) => d.pressure.hot[k]));
  const outPerLap = d.pressure.hot_series.fl.map((_, i) => corners.filter((k) => d.pressure.hot_series[k][i] < lo || d.pressure.hot_series[k][i] > hi).length);

  // Consumo.
  const spread = Math.max(...d.fuel_per_lap) - Math.min(...d.fuel_per_lap);
  const stable = spread <= 0.4;
  const projFuel = d.session.fuel_avg_per_lap * PROJECTION_LAPS;

  return [
    {
      id: "temp",
      label: "Temperatura gomme",
      valueNum: hotVal,
      suffix: "°C",
      decimals: 0,
      note: overLimit ? `${labelOf(hottest)} oltre la finestra (${d.temp.limit}°C)` : `${labelOf(hottest)} entro la finestra`,
      detail: `Massimo di stint sulla gomma più calda (${labelOf(hottest)}), confrontato col limite finestra ${d.temp.limit}°C.`,
      color: overLimit ? COLORS.accent : COLORS.ok,
      series: hotSeries,
    },
    {
      id: "press",
      label: "Pressione media",
      valueNum: d.pressure.avg_hot,
      suffix: " psi",
      decimals: 1,
      note: out.length === 0 ? `Tutte in finestra (${lo}–${hi} psi)` : `${out.length} gomm${out.length === 1 ? "a" : "e"} fuori finestra${anyLow ? " · retrotreno basso" : ""}`,
      detail: `Media delle 4 pressioni a caldo dell'ultimo giro. Finestra ottimale ${lo}–${hi} psi.`,
      color: out.length === 0 ? COLORS.ok : COLORS.warn,
      series: pressSeries,
    },
    {
      id: "fuel",
      label: "Consumo medio",
      valueNum: d.session.fuel_avg_per_lap,
      suffix: " L/giro",
      decimals: 1,
      note: stable ? `Stabile (Δ ${spread.toFixed(1)} L) · ${d.session.fuel_total} L totali` : `Variabile (Δ ${spread.toFixed(1)} L) · ${d.session.fuel_total} L totali`,
      detail: `Consumo medio per giro sullo stint; Δ = escursione tra giro più e meno esoso (${spread.toFixed(1)} L).`,
      color: stable ? COLORS.ok : COLORS.warn,
      series: d.fuel_per_lap,
    },
    {
      id: "trend",
      label: "Trend temperatura",
      valueNum: tempTrend,
      suffix: "°C/giro",
      decimals: 1,
      note: tempTrend > 0 ? `In salita su ${labelOf(hottest)}` : tempTrend < 0 ? `In calo su ${labelOf(hottest)}` : "Stabile",
      detail: `Pendenza media della temperatura sulla gomma più calda (${labelOf(hottest)}): (ultimo − primo) / giri.`,
      color: tempTrend > 0 ? COLORS.warn : COLORS.ok,
      series: hotSeries,
    },
    {
      id: "spread",
      label: "Spread pressioni",
      valueNum: lastSpread,
      suffix: " psi",
      decimals: 1,
      note: lastSpread > winWidth ? "Sbilanciamento marcato" : "Bilanciamento regolare",
      detail: `Differenza tra la gomma più gonfia e la più sgonfia (a caldo, ultimo giro). Riferimento: ampiezza finestra ${winWidth.toFixed(1)} psi.`,
      color: lastSpread > winWidth ? COLORS.warn : COLORS.ok,
      series: spreadSeries,
    },
    {
      id: "outwin",
      label: "Gomme fuori finestra",
      valueNum: out.length,
      suffix: "/4",
      decimals: 0,
      note: out.length === 0 ? "Tutte in finestra" : `${out.map((k) => labelOf(k)).join(", ")}`,
      detail: `Quante delle 4 gomme sono fuori dalla finestra pressioni a caldo (${lo}–${hi} psi) nell'ultimo giro.`,
      color: out.length === 0 ? COLORS.ok : COLORS.warn,
      series: outPerLap,
    },
    {
      id: "proj",
      label: `Proiezione +${PROJECTION_LAPS} giri`,
      valueNum: projFuel,
      suffix: " L",
      decimals: 1,
      note: `~${d.session.fuel_avg_per_lap} L/giro a questo ritmo`,
      detail: `Estrapolazione lineare: consumo medio × ${PROJECTION_LAPS} giri. (Orizzonte ${PROJECTION_LAPS} giri: assunzione di comodo, non un dato ACC.)`,
      color: COLORS.ok,
      series: d.fuel_per_lap,
    },
  ];
}

// Shortcut di navigazione (icone coerenti con la Sidebar).
const ACTIONS = [
  { href: "/console", icon: "🎧", label: "Engineer Console", hint: "Chiedi a Gigi un'analisi" },
  { href: "/telemetry", icon: "📈", label: "Telemetria", hint: "Dati gomme e consumo per-giro" },
  { href: "/setup", icon: "🔧", label: "Setup", hint: "Regola i 49 parametri ACC" },
];

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-0.5 font-mono">{value}</div>
    </div>
  );
}

// Pallino di stato: pulse discreto quando lo stato richiede attenzione (accent/warn).
function StatusDot({ color, pulse }: { color: string; pulse: boolean }) {
  const reduce = useReducedMotion();
  if (!pulse || reduce) return <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />;
  return (
    <motion.span
      className="h-1.5 w-1.5 rounded-full"
      style={{ background: color }}
      animate={{ opacity: [1, 0.35, 1], scale: [1, 1.25, 1] }}
      transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

// Card KPI: count-up al mount, sparkline se c'è una serie, apre il dettaglio in-page.
function KpiCard({ kpi, onOpen }: { kpi: Kpi; onOpen: () => void }) {
  const { label, valueNum, suffix, decimals, note, color, series } = kpi;
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group block w-full cursor-pointer rounded-xl border border-line bg-surface p-4 text-left transition duration-200 hover:-translate-y-1 hover:border-accent/50 hover:shadow-[0_12px_30px_-14px_rgba(232,0,45,0.4)]"
    >
      <div className="flex items-start justify-between">
        <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
        <span aria-hidden="true" className="font-mono text-sm text-muted transition-colors duration-200 group-hover:text-accent">
          ⤢
        </span>
      </div>
      <div className="mt-2 block font-mono text-3xl" style={{ color }}>
        <CountUp value={valueNum} decimals={decimals} suffix={suffix} />
      </div>
      <div className="mt-2 flex items-center gap-1.5 text-xs" style={{ color }}>
        <StatusDot color={color} pulse={color !== COLORS.ok} />
        {note}
      </div>
      {series && series.length >= 2 && (
        <div className="mt-3">
          <Sparkline data={series} color={color} />
        </div>
      )}
    </button>
  );
}

// Modal dettaglio KPI (in-page, nessun cambio rotta).
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
        className="w-full max-w-md rounded-2xl border border-line bg-surface p-6"
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
        <div className="mt-2 font-mono text-4xl" style={{ color: kpi.color }}>
          <CountUp value={kpi.valueNum} decimals={kpi.decimals} suffix={kpi.suffix} />
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-sm" style={{ color: kpi.color }}>
          <StatusDot color={kpi.color} pulse={kpi.color !== COLORS.ok} />
          {kpi.note}
        </div>
        {kpi.series && kpi.series.length >= 2 && (
          <div className="mt-4 rounded-lg border border-line bg-inset p-3">
            <Sparkline data={kpi.series} color={kpi.color} />
          </div>
        )}
        <p className="mt-4 border-t border-line pt-3 text-[0.8rem] leading-relaxed text-subtle">{kpi.detail}</p>
      </motion.div>
    </motion.div>
  );
}

function ActionCard({ href, icon, label, hint }: (typeof ACTIONS)[number]) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 rounded-xl border border-line bg-surface p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent/50"
    >
      <span className="text-lg">{icon}</span>
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
