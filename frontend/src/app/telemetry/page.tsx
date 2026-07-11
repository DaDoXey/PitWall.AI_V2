"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import TempLineChart from "@/components/charts/TempLineChart";
import PressureGauge from "@/components/charts/PressureGauge";
import TyreHeatmap from "@/components/charts/TyreHeatmap";
import LapTable from "@/components/charts/LapTable";
import LapChannelBars from "@/components/charts/LapChannelBars";
import LapTimesTable from "@/components/charts/LapTimesTable";
import LapDeltaChart from "@/components/charts/LapDeltaChart";
import TyreOverlay from "@/components/charts/TyreOverlay";
import ChannelHistogram from "@/components/charts/ChannelHistogram";
import SetupRadar from "@/components/charts/SetupRadar";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { getSession } from "@/lib/api";
import { TYRE_SERIES, type SessionData } from "@/lib/telemetry";
import { buildCrossChecks } from "@/lib/crosscheck";

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

      {/* Riga 2b: tempi sul giro (sezione Lap Times, FASE 7) */}
      <motion.div variants={fadeInUp} className="pw-scroll mt-6 overflow-x-auto rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Tempi sul giro</div>
        <LapTimesTable data={data} />
      </motion.div>

      {/* Riga 2c: delta giro-su-giro (FASE 9) */}
      <motion.div variants={fadeInUp} className="mt-6 rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Delta giro-su-giro</div>
        <LapDeltaChart data={data} />
      </motion.div>

      {/* Riga 2d: overlay confronto FL/FR/RL/RR (FASE 10) */}
      <motion.div variants={fadeInUp} className="mt-6 rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Overlay gomme · FL/FR/RL/RR</div>
        <TyreOverlay data={data} />
      </motion.div>

      {/* Riga 2e: Analisi — distribuzione canale (istogramma) (FASE 11) */}
      <motion.div variants={fadeInUp} className="mt-6 rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Analisi · Distribuzione (istogramma)</div>
        <ChannelHistogram data={data} />
      </motion.div>

      {/* Riga 2f: Analisi — radar bilanciamento setup (FASE 12) */}
      <motion.div variants={fadeInUp} className="mt-6 rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Analisi · Bilanciamento (radar)</div>
        <SetupRadar data={data} />
      </motion.div>

      {/* Riga 3: tabella giro-per-giro */}
      <motion.div variants={fadeInUp} className="pw-scroll mt-6 overflow-x-auto rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Dati giro-per-giro</div>
        <LapTable data={data} />
      </motion.div>

      {/* Riga 3b: channel report grafico — barre per canale (pannello separato) */}
      <motion.div variants={fadeInUp} className="mt-6 rounded-xl border border-line bg-surface p-4">
        <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Andamento per giro · barre per canale</div>
        <LapChannelBars data={data} />
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
