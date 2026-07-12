"use client";

// Scatter/XY plot "Correlazione canali" stile i2 Pro (megaprompt #7, FASE 6):
// sostituisce l'istogramma distribuzione nella tab Analisi. Un punto = un giro;
// canali su X e Y selezionabili tra quelli GIÀ esposti da /api/session (tempo
// giro, consumo, temp/press per angolo) — nessun canale nuovo. Il giro Personal
// Best usa il token fucsia STATE.best (stessa convenzione della tabella Tempi).
// Resa strumento: hairline grid, assi su min/max reali (no padding arbitrario),
// numerici monospace, zero glow. I valori esatti vivono nel tooltip (giro + X/Y).
import { useState } from "react";
import { CartesianGrid, Cell, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { formatLapTime, TYRE_SERIES, type SessionData } from "@/lib/telemetry";

export type Chan = {
  key: string;
  label: string;
  unit: string;
  values: number[];
  decimals: number;
  fmt: (v: number) => string; // formato "esatto" per il tooltip (tempo giro → m:ss.mmm)
};

type Row = { lap: number; x: number; y: number; pb: boolean };

// Esportato (FASE 8 #7): StintCompare riusa gli stessi 10 canali senza duplicare.
export function buildChannels(data: SessionData): Chan[] {
  const num = (dec: number) => (v: number) => v.toFixed(dec);
  const chans: Chan[] = [
    { key: "lap_time", label: "Tempo giro", unit: "s", values: data.lap_times ?? [], decimals: 2, fmt: formatLapTime },
    { key: "fuel", label: "Consumo", unit: "L", values: data.fuel_per_lap ?? [], decimals: 1, fmt: num(1) },
  ];
  for (const s of TYRE_SERIES) {
    chans.push({ key: `temp_${s.key}`, label: `Temp ${s.label}`, unit: "°C", values: data.temp.series[s.key], decimals: 0, fmt: num(0) });
  }
  for (const s of TYRE_SERIES) {
    chans.push({ key: `press_${s.key}`, label: `Press ${s.label}`, unit: "psi", values: data.pressure.hot_series[s.key], decimals: 1, fmt: num(1) });
  }
  return chans;
}

// Riga di chip per scegliere il canale di un asse (stesso idioma dei selettori
// esistenti: chip mono, bordo accent sull'attivo, niente riempimenti).
function AxisSelector({ axis, chans, sel, onSel }: { axis: "X" | "Y"; chans: Chan[]; sel: string; onSel: (k: string) => void }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="w-3 font-mono text-[0.55rem] uppercase tracking-widest text-muted">{axis}</span>
      {chans.map((c) => (
        <button
          key={c.key}
          type="button"
          onClick={() => onSel(c.key)}
          aria-pressed={sel === c.key}
          className={`rounded border px-2 py-0.5 font-mono text-[0.58rem] transition ${
            sel === c.key ? "border-accent text-white" : "border-line text-subtle hover:text-white"
          }`}
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}

export default function ScatterPlot({ data }: { data: SessionData }) {
  const chans = buildChannels(data);
  // Default didattico: la storia demo (Post.DX surriscalda → il tempo degrada).
  const [xKey, setXKey] = useState("temp_rr");
  const [yKey, setYKey] = useState("lap_time");
  const cx = chans.find((c) => c.key === xKey) ?? chans[0];
  const cy = chans.find((c) => c.key === yKey) ?? chans[0];

  const times = data.lap_times ?? [];
  const bestIdx = times.length > 0 ? times.indexOf(Math.min(...times)) : -1;
  const rows: Row[] = (data.laps ?? []).map((lap, i) => ({
    lap,
    x: cx.values[i],
    y: cy.values[i],
    pb: i === bestIdx,
  }));

  // Tooltip: i numeri esatti vivono QUI (giro + valori X/Y), una volta sola.
  const TooltipBox = ({ active, payload }: { active?: boolean; payload?: { payload: Row }[] }) => {
    if (!active || !payload?.length) return null;
    const p = payload[0].payload;
    return (
      <div className="rounded-md border border-line bg-surface px-2.5 py-1.5 font-mono text-[0.62rem]">
        <div style={{ color: p.pb ? STATE.best : "#ffffff" }}>
          Giro {p.lap}
          {p.pb ? " · PB" : ""}
        </div>
        <div className="text-subtle">
          {cx.label}: <span className="text-white">{cx.fmt(p.x)} {cx.unit}</span>
        </div>
        <div className="text-subtle">
          {cy.label}: <span className="text-white">{cy.fmt(p.y)} {cy.unit}</span>
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* Selettori canale X / Y */}
      <div className="mb-3 flex flex-col gap-1.5">
        <AxisSelector axis="X" chans={chans} sel={xKey} onSel={setXKey} />
        <AxisSelector axis="Y" chans={chans} sel={yKey} onSel={setYKey} />
      </div>

      {/* Didascalia ordinata: unità Y orizzontale sopra la scala (lezione F10-fix
          del #5: niente testo ruotato), X etichettata sotto il grafico. */}
      <div className="mb-1 pl-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">
        {cy.label} · {cy.unit}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} />
          <XAxis
            type="number"
            dataKey="x"
            domain={["dataMin", "dataMax"]}
            stroke={INSTRUMENT.tick}
            tick={{ fill: COLORS.muted, fontSize: 10 }}
            tickFormatter={(v: number) => v.toFixed(cx.decimals)}
            tickCount={6}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={["dataMin", "dataMax"]}
            stroke={INSTRUMENT.tick}
            tick={{ fill: COLORS.muted, fontSize: 10 }}
            tickFormatter={(v: number) => v.toFixed(cy.decimals)}
            width={52}
          />
          <Tooltip content={<TooltipBox />} cursor={{ stroke: COLORS.lineStrong, strokeWidth: 1, strokeDasharray: "4 4" }} />
          <Scatter data={rows} isAnimationActive={false}>
            {rows.map((r, i) => (
              <Cell key={i} fill={r.pb ? STATE.best : COLORS.subtle} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">
        {cx.label} · {cx.unit}
      </div>

      {/* Legenda minima: solo la convenzione PB (il resto è neutro) */}
      <div className="mt-2 flex items-center gap-1.5 font-mono text-[0.55rem] text-muted">
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: STATE.best }} />
        giro personal best
      </div>
    </div>
  );
}
