"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import CountUp from "@/components/ui/CountUp";
import Sparkline from "@/components/charts/Sparkline";
import { fadeInUp, staggerContainer, useReducedMotion } from "@/lib/motion";
import { getSession } from "@/lib/api";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";
import { COLORS } from "@/lib/theme";

export default function Dashboard() {
  const [data, setData] = useState<SessionData | null>(null);
  const [err, setErr] = useState<string | null>(null);

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
  const metrics = buildMetrics(data);

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
        <div className="font-mono text-[0.6rem] uppercase tracking-widest text-accent">
          Ultima sessione
        </div>
        <div className="mt-1 font-display text-2xl font-bold">{s.track}</div>
        <div className="text-sm text-subtle">
          {s.car} · {s.car_year} · stint {s.stint.toLowerCase()}
        </div>
        <div className="mt-4 flex flex-wrap gap-8 border-t border-line pt-3 text-sm">
          <Stat label="Giri" value={`${s.laps} · best ${s.best_lap}`} />
          <Stat label="Consumo" value={`${s.fuel_avg_per_lap} L/giro · ${s.fuel_total} L`} />
        </div>
      </motion.div>

      {/* Metriche: ingresso a cascata; ogni card è una CTA */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-3"
      >
        {metrics.map((m) => (
          <motion.div key={m.label} variants={fadeInUp}>
            <MetricCard {...m} />
          </motion.div>
        ))}
      </motion.div>

      {/* Prossime azioni: naviga da qui, la Dashboard non è più un vicolo cieco */}
      <div className="mt-8">
        <div className="mb-3 font-mono text-[0.6rem] uppercase tracking-widest text-muted">
          Prossime azioni
        </div>
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
    </div>
  );
}

type Metric = {
  label: string;
  valueNum: number;
  suffix: string;
  decimals: number;
  note: string;
  color: string;
  href: string;
  series: number[];
};

// Metriche + note + serie per-giro derivate dai dati (niente numeri inventati):
// temperatura gomma più calda, media pressioni a caldo, consumo per giro.
function buildMetrics(d: SessionData): Metric[] {
  const corners: Corner[] = ["fl", "fr", "rl", "rr"];
  const labelOf = (k: Corner) => TYRE_SERIES.find((t) => t.key === k)?.label ?? k;

  // Gomma più calda + sua serie termica per-giro.
  const hottest = corners.reduce((a, b) => (d.temp.max[b] > d.temp.max[a] ? b : a));
  const hotVal = d.temp.max[hottest];
  const overLimit = hotVal > d.temp.limit;
  const tempSeries = d.temp.series[hottest];

  // Pressioni a caldo fuori finestra + serie media a caldo per-giro (dai 4 corner).
  const [lo, hi] = d.pressure.hot_window;
  const out = corners.filter((k) => d.pressure.hot[k] < lo || d.pressure.hot[k] > hi);
  const anyLow = corners.some((k) => d.pressure.hot[k] < lo);
  const pressSeries = d.pressure.hot_series.fl.map(
    (_, i) =>
      (d.pressure.hot_series.fl[i] +
        d.pressure.hot_series.fr[i] +
        d.pressure.hot_series.rl[i] +
        d.pressure.hot_series.rr[i]) /
      4,
  );

  // Stabilità consumo + serie consumo per-giro.
  const spread = Math.max(...d.fuel_per_lap) - Math.min(...d.fuel_per_lap);
  const stable = spread <= 0.4;

  return [
    {
      label: "Temperatura gomme",
      valueNum: hotVal,
      suffix: "°C",
      decimals: 0,
      note: overLimit
        ? `${labelOf(hottest)} oltre la finestra (${d.temp.limit}°C)`
        : `${labelOf(hottest)} entro la finestra`,
      color: overLimit ? COLORS.accent : COLORS.ok,
      href: "/telemetry",
      series: tempSeries,
    },
    {
      label: "Pressione media",
      valueNum: d.pressure.avg_hot,
      suffix: " psi",
      decimals: 1,
      note:
        out.length === 0
          ? `Tutte in finestra (${lo}–${hi} psi)`
          : `${out.length} gomm${out.length === 1 ? "a" : "e"} fuori finestra${anyLow ? " · retrotreno basso" : ""}`,
      color: out.length === 0 ? COLORS.ok : COLORS.warn,
      href: "/telemetry",
      series: pressSeries,
    },
    {
      label: "Consumo medio",
      valueNum: d.session.fuel_avg_per_lap,
      suffix: " L/giro",
      decimals: 1,
      note: stable
        ? `Stabile (Δ ${spread.toFixed(1)} L) · ${d.session.fuel_total} L totali`
        : `Variabile (Δ ${spread.toFixed(1)} L) · ${d.session.fuel_total} L totali`,
      color: stable ? COLORS.ok : COLORS.warn,
      href: "/console",
      series: d.fuel_per_lap,
    },
  ];
}

// Shortcut di navigazione sotto le metriche (icone coerenti con la Sidebar).
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

// Pallino di stato: pulse discreto quando lo stato richiede attenzione
// (accent/warn); verde "ok" resta fisso. Reduced-motion → statico.
function StatusDot({ color, pulse }: { color: string; pulse: boolean }) {
  const reduce = useReducedMotion();
  if (!pulse || reduce)
    return <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />;
  return (
    <motion.span
      className="h-1.5 w-1.5 rounded-full"
      style={{ background: color }}
      animate={{ opacity: [1, 0.35, 1], scale: [1, 1.25, 1] }}
      transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

// Card metrica cliccabile: count-up al mount, sparkline reale, hover premium.
function MetricCard({ label, valueNum, suffix, decimals, note, color, href, series }: Metric) {
  return (
    <Link
      href={href}
      className="group block rounded-xl border border-line bg-surface p-4 transition duration-200 hover:-translate-y-1 hover:border-accent/50 hover:shadow-[0_12px_30px_-14px_rgba(232,0,45,0.4)]"
    >
      <div className="flex items-start justify-between">
        <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
        <span
          aria-hidden="true"
          className="font-mono text-sm text-muted transition-all duration-200 group-hover:translate-x-0.5 group-hover:text-accent"
        >
          →
        </span>
      </div>
      <CountUp
        value={valueNum}
        decimals={decimals}
        suffix={suffix}
        className="mt-2 block font-mono text-3xl"
      />
      <div className="mt-2 flex items-center gap-1.5 text-xs" style={{ color }}>
        <StatusDot color={color} pulse={color !== COLORS.ok} />
        {note}
      </div>
      <div className="mt-3">
        <Sparkline data={series} color={color} />
      </div>
    </Link>
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
      <span
        aria-hidden="true"
        className="font-mono text-sm text-muted transition-colors duration-200 group-hover:text-accent"
      >
        →
      </span>
    </Link>
  );
}
