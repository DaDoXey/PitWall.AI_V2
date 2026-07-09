"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/ui/PageHeader";
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
      <div className="mb-4 rounded-xl border border-l-4 border-line border-l-accent bg-surface p-5">
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
      </div>

      {/* Metriche derivate dai dati di sessione */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {metrics.map((m) => (
          <MetricCard key={m.label} {...m} />
        ))}
      </div>
    </div>
  );
}

type Metric = { label: string; value: string; note: string; color: string };

// Metriche + note derivate dai dati (niente testo hardcoded): temperatura più
// critica vs limite, pressione media vs finestra a caldo, stabilità consumo.
function buildMetrics(d: SessionData): Metric[] {
  const corners: Corner[] = ["fl", "fr", "rl", "rr"];
  const labelOf = (k: Corner) => TYRE_SERIES.find((t) => t.key === k)?.label ?? k;

  // Gomma più calda.
  const hottest = corners.reduce((a, b) => (d.temp.max[b] > d.temp.max[a] ? b : a));
  const hotVal = d.temp.max[hottest];
  const overLimit = hotVal > d.temp.limit;

  // Pressioni a caldo fuori finestra.
  const [lo, hi] = d.pressure.hot_window;
  const out = corners.filter((k) => d.pressure.hot[k] < lo || d.pressure.hot[k] > hi);
  const anyLow = corners.some((k) => d.pressure.hot[k] < lo);

  // Stabilità consumo.
  const spread = Math.max(...d.fuel_per_lap) - Math.min(...d.fuel_per_lap);
  const stable = spread <= 0.4;

  return [
    {
      label: "Temperatura gomme",
      value: `${hotVal}°C`,
      note: overLimit
        ? `${labelOf(hottest)} oltre la finestra (${d.temp.limit}°C)`
        : `${labelOf(hottest)} entro la finestra`,
      color: overLimit ? COLORS.accent : COLORS.ok,
    },
    {
      label: "Pressione media",
      value: `${d.pressure.avg_hot} psi`,
      note:
        out.length === 0
          ? `Tutte in finestra (${lo}–${hi} psi)`
          : `${out.length} gomm${out.length === 1 ? "a" : "e"} fuori finestra${anyLow ? " · retrotreno basso" : ""}`,
      color: out.length === 0 ? COLORS.ok : COLORS.warn,
    },
    {
      label: "Consumo medio",
      value: `${d.session.fuel_avg_per_lap} L/giro`,
      note: stable
        ? `Stabile (Δ ${spread.toFixed(1)} L) · ${d.session.fuel_total} L totali`
        : `Variabile (Δ ${spread.toFixed(1)} L) · ${d.session.fuel_total} L totali`,
      color: stable ? COLORS.ok : COLORS.warn,
    },
  ];
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-0.5 font-mono">{value}</div>
    </div>
  );
}

function MetricCard({ label, value, note, color }: Metric) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-2 font-mono text-3xl">{value}</div>
      <div className="mt-2 flex items-center gap-1.5 text-xs" style={{ color }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
        {note}
      </div>
    </div>
  );
}
