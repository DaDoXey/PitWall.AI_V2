"use client";

// Grafico unificato "a corsie" stile MoTeC i2 Pro (megaprompt #6, FASE 5):
// SOSTITUISCE la line chart temperatura standalone e TyreOverlay. Due corsie
// sottili impilate — Temperatura sopra, Pressione sotto — con lo stesso asse X
// (giro) e UN SOLO cursore sincronizzato (syncId Recharts). La soglia temp resta
// solo sulla corsia Temperatura (tratteggio hairline); il tratto che sfora è
// ridisegnato in rosso (colore = solo stato). I valori esatti NON sono duplicati
// in tooltip per corsia: compaiono una volta sola nel box "Valori" a lato
// (riusa TyreSnapshotGrid, lo stesso dello Snapshot del radar).
import { useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE, STROKE } from "@/lib/instrument";
import TyreSnapshotGrid from "@/components/charts/TyreSnapshotGrid";
import { formatLapTime, TYRE_SERIES, type SessionData } from "@/lib/telemetry";
import { DEMO_TANK_CAPACITY_L } from "@/lib/catalog";

const SYNC_ID = "pw-lanes";

// Stato del mouse Recharts (tipizzazione minima di ciò che usiamo).
type ChartMouseState = { activeTooltipIndex?: number } | null;

export default function TelemetryLanes({ data }: { data: SessionData }) {
  const laps = data.laps ?? [];
  // Giro attivo per il box "Valori": default ultimo giro, aggiornato da hover/tap.
  const [lapIdx, setLapIdx] = useState(Math.max(0, laps.length - 1));

  const limit = data.temp.limit;
  const [plo, phi] = data.pressure.hot_window;

  // Righe condivise: temp + press per gomma, più le serie "over" (solo i valori
  // oltre soglia, null altrove) per ridisegnare in rosso il tratto che sfora.
  const rows = laps.map((lap, i) => {
    const r: Record<string, number | null> = { lap };
    for (const s of TYRE_SERIES) {
      const tv = data.temp.series[s.key][i];
      r[s.key] = tv;
      r[`${s.key}Over`] = tv > limit ? tv : null;
      r[`${s.key}P`] = data.pressure.hot_series[s.key][i];
    }
    return r;
  });

  const onMove = (st: ChartMouseState) => {
    if (st && typeof st.activeTooltipIndex === "number" && st.activeTooltipIndex >= 0) {
      setLapIdx(st.activeTooltipIndex);
    }
  };

  // Cursore sincronizzato senza box flottante: i numeri esatti vivono SOLO nel
  // box "Valori" (niente doppia rappresentazione, principio sezione 0).
  const silentTooltip = (
    <Tooltip content={() => null} cursor={{ stroke: COLORS.lineStrong, strokeWidth: 1 }} />
  );

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {/* Corsie (2/3): stesso asse X, un cursore */}
      <div className="lg:col-span-2">
        {/* Legenda unica per entrambe le corsie */}
        <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1">
          {TYRE_SERIES.map((s) => (
            <span key={s.key} className="flex items-center gap-1.5 font-mono text-[0.6rem] text-subtle">
              <span className="h-0.5 w-3.5" style={{ background: s.color }} />
              {s.label}
            </span>
          ))}
        </div>

        {/* Corsia 1 · Temperatura (con soglia) */}
        <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Temperatura · °C</div>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={rows} syncId={SYNC_ID} margin={{ top: 6, right: 12, bottom: 0, left: 4 }} onMouseMove={onMove} onClick={onMove}>
            <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
            <XAxis dataKey="lap" hide />
            <YAxis domain={[74, 110]} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} tickFormatter={(v) => `${v}°`} width={40} />
            {silentTooltip}
            <ReferenceLine
              y={limit}
              stroke={COLORS.muted}
              strokeDasharray="4 4"
              strokeWidth={1}
              label={{ value: `${limit}°C`, fill: COLORS.muted, fontSize: 9, position: "insideTopRight" }}
            />
            {TYRE_SERIES.map((s) => (
              <Line key={s.key} type="monotone" dataKey={s.key} stroke={s.color} strokeWidth={STROKE.needle} strokeOpacity={0.9} dot={{ r: 1.6, strokeWidth: 0 }} activeDot={{ r: 3 }} isAnimationActive={false} />
            ))}
            {/* Tratto oltre soglia ridisegnato in rosso stato (sopra la serie base).
                DEVE ridisegnare anche i marker standard (pallini bianchi + activeDot):
                essendo più spessa e disegnata sopra, altrimenti COPRE i pallini della
                serie base e il tratto oltre soglia resta senza punti in evidenza,
                diverso dalle altre gomme (F5-fix3, diagnosi da screenshot). */}
            {TYRE_SERIES.map((s) => (
              <Line key={`${s.key}Over`} type="monotone" dataKey={`${s.key}Over`} stroke={STATE.alarm} strokeWidth={STROKE.needle + 0.5} dot={{ r: 1.6, strokeWidth: 0 }} activeDot={{ r: 3 }} connectNulls={false} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* Corsia 2 · Pressione (finestra ottimale) */}
        <div className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-muted">Pressione · psi</div>
        <ResponsiveContainer width="100%" height={130}>
          <LineChart data={rows} syncId={SYNC_ID} margin={{ top: 6, right: 12, bottom: 0, left: 4 }} onMouseMove={onMove} onClick={onMove}>
            <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
            <XAxis dataKey="lap" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} />
            <YAxis domain={["auto", "auto"]} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={40} />
            {silentTooltip}
            {[plo, phi].map((y) => (
              <ReferenceLine key={y} y={y} stroke={COLORS.muted} strokeDasharray="4 4" strokeWidth={1} />
            ))}
            {TYRE_SERIES.map((s) => (
              <Line key={`${s.key}P`} type="monotone" dataKey={`${s.key}P`} stroke={s.color} strokeWidth={STROKE.needle} strokeOpacity={0.9} dot={{ r: 1.6, strokeWidth: 0 }} activeDot={{ r: 3 }} isAnimationActive={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
        <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">Giro</div>
      </div>

      {/* Box "Valori" (1/3): i numeri esatti del giro attivo, una volta sola */}
      <div className="rounded-lg border border-line bg-inset p-3">
        <div className="mb-2 flex items-baseline justify-between">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Valori · giro</span>
          <span className="font-mono text-sm text-white">{laps[lapIdx] ?? "—"}</span>
        </div>
        <TyreSnapshotGrid data={data} lapIdx={lapIdx} />

        {/* Contesto del giro attivo (F5-fix, riempimento richiesto da Edoardo):
            tempo (PB fucsia se migliore, altrimenti Δ dal best) + consumo.
            Seguono il cursore come la griglia — stessi dati di lap_times/fuel_per_lap. */}
        {(() => {
          const times = data.lap_times ?? [];
          const tSel = times[lapIdx];
          const best = times.length > 0 ? Math.min(...times) : null;
          const isPB = tSel != null && best != null && tSel === best;
          const fuel = data.fuel_per_lap?.[lapIdx];
          // Residuo stimato al giro attivo (FASE 9 #7): capacità − consumo
          // cumulato fino al giro. Assunzione DEMO dichiarata: pieno al via.
          const used = (data.fuel_per_lap ?? []).slice(0, lapIdx + 1).reduce((s, v) => s + v, 0);
          const remaining = fuel != null ? DEMO_TANK_CAPACITY_L - used : null;
          if (tSel == null && fuel == null) return null;
          return (
            <div className="mt-2 flex flex-col gap-1">
              {tSel != null && (
                <div className="flex items-center justify-between rounded-md border border-line px-2 py-1.5 font-mono text-[0.62rem]">
                  <span className="text-subtle">Tempo giro</span>
                  <span className="flex items-center gap-2">
                    <span style={{ color: isPB ? STATE.best : "#ffffff" }}>{formatLapTime(tSel)}</span>
                    {isPB ? (
                      <span className="rounded px-1 font-mono text-[0.5rem] uppercase" style={{ color: STATE.best, border: `1px solid ${STATE.best}` }}>
                        PB
                      </span>
                    ) : (
                      best != null && <span className="text-muted">+{(tSel - best).toFixed(3)}</span>
                    )}
                  </span>
                </div>
              )}
              {fuel != null && (
                <div className="flex items-center justify-between rounded-md border border-line px-2 py-1.5 font-mono text-[0.62rem]">
                  <span className="text-subtle">Consumo</span>
                  <span className="text-white">{fuel.toFixed(1)} L</span>
                </div>
              )}
              {remaining != null && (
                <div className="rounded-md border border-line px-2 py-1.5 font-mono text-[0.62rem]">
                  <div className="flex items-center justify-between">
                    <span className="text-subtle">Residuo stimato</span>
                    <span className="text-white">~{remaining.toFixed(1)} L</span>
                  </div>
                  <div className="mt-0.5 text-[0.5rem] uppercase tracking-widest text-muted">
                    serbatoio {DEMO_TANK_CAPACITY_L} L · pieno al via (demo)
                  </div>
                </div>
              )}
            </div>
          );
        })()}

        <div className="mt-2 font-mono text-[0.5rem] uppercase tracking-widest text-muted">
          Passa il cursore (o tocca) sulle corsie per cambiare giro
        </div>
      </div>
    </div>
  );
}
