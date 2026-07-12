"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import Tabs from "@/components/ui/Tabs";
import TelemetryLanes from "@/components/charts/TelemetryLanes";
import PressureGauge from "@/components/charts/PressureGauge";
import TyreHeatmap from "@/components/charts/TyreHeatmap";
import ChannelReport from "@/components/charts/ChannelReport";
import LapTimesTable from "@/components/charts/LapTimesTable";
import LapDeltaChart from "@/components/charts/LapDeltaChart";
import ScatterPlot from "@/components/charts/ScatterPlot";
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
      {/* ===== HEADER FISSO (megaprompt #6, FASE 3): cross-check → heatmap + gauge.
          L'informazione più actionable (coerenza dati) è la PRIMA cosa visibile;
          heatmap e pressioni rispondono a "come stanno le 4 gomme adesso" e restano
          sempre visibili, fuori dalle tab. Nessuna KPI duplicata dal Dashboard. ===== */}

      {/* Cross-check in cima: da lista in fondo pagina a riga compatta in testa */}
      <motion.div variants={fadeInUp} className="rounded-xl border border-line bg-surface p-4">
        <div className="mb-2 font-mono text-xs uppercase tracking-wider text-subtle">Cross-check dati</div>
        <div className="flex flex-wrap gap-x-6 gap-y-1.5">
          {checks.map((cc, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-[#cccccc]">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: cc.color }} />
              {cc.msg}
            </div>
          ))}
        </div>
      </motion.div>

      {/* Heatmap + gauge pressioni affiancati: lo stato attuale delle 4 gomme */}
      <motion.div variants={fadeInUp} className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <TyreHeatmap data={data} />
        <div className="lg:col-span-2">
          <div className="mb-1 font-mono text-xs uppercase tracking-wider text-subtle">
            Pressioni gomme · a caldo (display)
          </div>
          <div className="mb-3 text-xs text-muted">
            Finestra ottimale {lo}–{hi} psi · valori a freddo (garage) distinti
          </div>
          <div className="grid grid-cols-2 gap-3">
            {TYRE_SERIES.map((c) => (
              <div key={c.key} className="rounded-xl border border-line bg-surface p-3">
                <PressureGauge label={c.label} value={data.pressure.hot[c.key]} window={data.pressure.hot_window} />
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* ===== TAB Tempi | Analisi (megaprompt #6, FASE 4): il dettaglio si apre
          su richiesta invece di impilare tutto. Dentro le tab niente motion wrapper:
          il cambio tab non deve ri-animare i contenuti. ===== */}
      <motion.div variants={fadeInUp} className="mt-6">
        <Tabs
          tabs={[
            {
              id: "tempi",
              label: "Tempi",
              content: (
                <div className="flex flex-col gap-4">
                  <div className="pw-scroll overflow-x-auto rounded-xl border border-line bg-surface p-4">
                    <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Tempi sul giro</div>
                    <LapTimesTable data={data} />
                  </div>
                  <div className="rounded-xl border border-line bg-surface p-4">
                    <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Delta giro-su-giro</div>
                    <LapDeltaChart data={data} />
                  </div>
                </div>
              ),
            },
            {
              id: "analisi",
              label: "Analisi",
              content: (
                <div className="flex flex-col gap-4">
                  {/* Corsie i2 Pro (F5): UNICA vista andamento gomme — sostituisce la
                      line chart temperatura standalone e TyreOverlay. */}
                  <div className="rounded-xl border border-line bg-surface p-4">
                    <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Andamento gomme · {s.laps} giri</div>
                    <TelemetryLanes data={data} />
                  </div>
                  {/* Scatter XY (FASE 6 #7): sostituisce l'istogramma distribuzione */}
                  <div className="rounded-xl border border-line bg-surface p-4">
                    <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Correlazione canali</div>
                    <ScatterPlot data={data} />
                  </div>
                  <div className="rounded-xl border border-line bg-surface p-4">
                    <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Bilanciamento (radar)</div>
                    <SetupRadar data={data} />
                  </div>
                  {/* Channel Report (F6): tabella giro-per-giro + barre per canale
                      fusi in un'unica vista con switch Tabella ↔ Grafico. */}
                  <div className="rounded-xl border border-line bg-surface p-4">
                    <div className="mb-3 font-mono text-xs uppercase tracking-wider text-subtle">Channel report · giro per giro</div>
                    <ChannelReport data={data} />
                  </div>
                </div>
              ),
            },
          ]}
        />
      </motion.div>

      </motion.div>
    </div>
  );
}
