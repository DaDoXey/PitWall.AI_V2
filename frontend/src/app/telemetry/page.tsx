"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import TempLineChart from "@/components/charts/TempLineChart";
import PressureGauge from "@/components/charts/PressureGauge";
import TyreHeatmap from "@/components/charts/TyreHeatmap";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { getSession } from "@/lib/api";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";
import { COLORS } from "@/lib/theme";

export default function TelemetryPage() {
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
        <PageHeader title="Telemetria" />
        <p className="text-sm text-warn">{err}</p>
      </div>
    );
  if (!data)
    return (
      <div>
        <PageHeader title="Telemetria" />
        <p className="text-sm text-subtle">Caricamento…</p>
      </div>
    );

  const s = data.session;
  const [lo, hi] = data.pressure.hot_window;
  const checks = buildCrossChecks(data);

  return (
    <div>
      <PageHeader
        title="Telemetria"
        subtitle={`${s.track} · ${s.car} · ${s.laps} giri · stint ${s.stint.toLowerCase()}`}
      />

      <motion.div variants={staggerContainer} initial="hidden" animate="visible">
      {/* Riga 1: line chart + heatmap */}
      <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-line bg-surface p-4 lg:col-span-2">
          <div className="mb-1 font-mono text-sm">Temperatura gomme · {s.laps} giri</div>
          <TempLineChart data={data} />
        </div>
        <TyreHeatmap data={data} />
      </motion.div>

      {/* Riga 2: gauge pressioni a caldo */}
      <motion.div variants={fadeInUp} className="mt-4">
        <div className="mb-1 font-mono text-xs uppercase tracking-wider text-subtle">
          Pressioni gomme · a caldo (display)
        </div>
        <div className="mb-3 text-xs text-muted">
          Finestra ottimale {lo}–{hi} psi · valori a freddo (garage) distinti
        </div>
        <motion.div variants={staggerContainer} className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {TYRE_SERIES.map((c) => (
            <motion.div key={c.key} variants={fadeInUp} className="rounded-xl border border-line bg-surface p-3">
              <PressureGauge label={c.label} value={data.pressure.hot[c.key]} window={data.pressure.hot_window} />
            </motion.div>
          ))}
        </motion.div>
      </motion.div>

      {/* Riga 3: tabella giro-per-giro */}
      <motion.div variants={fadeInUp} className="mt-6 overflow-x-auto rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Dati giro-per-giro</div>
        <table className="w-full text-sm">
          <thead>
            <tr className="font-mono text-[0.62rem] uppercase text-muted">
              <th className="py-1 text-left">Giro</th>
              <th className="text-right">Cons. (L)</th>
              {TYRE_SERIES.map((c) => (
                <th key={c.key} className="text-right">
                  T {c.label}
                </th>
              ))}
              {TYRE_SERIES.map((c) => (
                <th key={`p-${c.key}`} className="text-right">
                  P {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.laps.map((lap, i) => (
              <tr key={lap} className="border-t border-line">
                <td className="py-1 font-mono">{lap}</td>
                <td className="text-right font-mono">{data.fuel_per_lap[i].toFixed(1)}</td>
                {TYRE_SERIES.map((c) => (
                  <td key={c.key} className="text-right font-mono">
                    {data.temp.series[c.key][i]}
                  </td>
                ))}
                {TYRE_SERIES.map((c) => (
                  <td key={`p-${c.key}`} className="text-right font-mono">
                    {data.pressure.hot_series[c.key][i]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </motion.div>

      {/* Riga 4: cross-check */}
      <motion.div variants={fadeInUp} className="mt-6 rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Cross-check dati</div>
        <motion.div variants={staggerContainer} className="flex flex-col gap-2">
          {checks.map((cc, i) => (
            <motion.div key={i} variants={fadeInUp} className="flex items-center gap-2 text-sm text-[#cccccc]">
              <span className="h-2 w-2 rounded-full" style={{ background: cc.color }} />
              {cc.msg}
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
      </motion.div>
    </div>
  );
}

function buildCrossChecks(d: SessionData) {
  const out: { color: string; msg: string }[] = [];
  const labels = d.tyre_labels;
  const corners: Corner[] = ["fl", "fr", "rl", "rr"];

  corners.forEach((k) => {
    const mx = d.temp.max[k];
    if (mx > d.temp.limit)
      out.push({ color: COLORS.accent, msg: `${labels[k]}: ${mx}°C oltre il limite finestra (${d.temp.limit}°C)` });
  });

  const [lo, hi] = d.pressure.hot_window;
  corners.forEach((k) => {
    const v = d.pressure.hot[k];
    if (v < lo) out.push({ color: COLORS.warn, msg: `${labels[k]}: ${v} psi sotto la finestra a caldo (${lo}–${hi})` });
    else if (v > hi) out.push({ color: COLORS.warn, msg: `${labels[k]}: ${v} psi oltre la finestra a caldo (${lo}–${hi})` });
  });

  const spread = Math.max(...d.fuel_per_lap) - Math.min(...d.fuel_per_lap);
  if (spread <= 0.4)
    out.push({ color: COLORS.ok, msg: `Consumo stabile (variazione ${spread.toFixed(1)} L/giro su ${d.session.laps} giri)` });

  if (out.length === 0) out.push({ color: COLORS.ok, msg: "Nessuna incongruenza rilevata" });
  return out;
}
