"use client";

// Delta giro-su-giro (megaprompt #5, FASE 9): variazione di ciascun giro rispetto al
// giro precedente o alla media dello stint. Grafico a barre sul Δ TEMPO (toggle di
// riferimento) + tabella dei delta sugli altri canali (consumo, temp max, pressione).
// Colore = stato (più veloce=verde / più lento=ambra); il giro più veloce usa il
// token best-time FUCSIA di FASE 8. Solo presentazione, nessuna logica di dominio.
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import type { Corner, SessionData } from "@/lib/telemetry";

type Mode = "prev" | "avg";
const CORNERS: Corner[] = ["fl", "fr", "rl", "rr"];

export default function LapDeltaChart({ data }: { data: SessionData }) {
  const [mode, setMode] = useState<Mode>("prev");

  const times = data.lap_times ?? [];
  const laps = data.laps ?? times.map((_, i) => i + 1);
  const best = times.length ? Math.min(...times) : 0;
  const bestIdx = times.indexOf(best);
  const avg = times.length ? times.reduce((a, b) => a + b, 0) / times.length : 0;

  // Δ tempo per il grafico a barre (riferimento selezionabile).
  const rows = times.map((t, i) => {
    const ref = mode === "avg" ? avg : i === 0 ? t : times[i - 1];
    return { lap: laps[i] ?? i + 1, delta: +(t - ref).toFixed(3), i };
  });
  const barColor = (i: number, delta: number) => {
    if (i === bestIdx) return STATE.best; // giro più veloce (fucsia)
    if (delta < 0) return STATE.ok; // più veloce del riferimento
    if (delta > 0) return STATE.warn; // più lento
    return INSTRUMENT.tick;
  };

  // Canali per giro per la tabella dei delta (vs giro precedente).
  const tempMax = times.map((_, i) => Math.max(...CORNERS.map((c) => data.temp.series[c][i])));
  const pressAvg = times.map((_, i) => CORNERS.reduce((a, c) => a + data.pressure.hot_series[c][i], 0) / 4);
  const chan = [
    { key: "time", label: "Tempo", arr: times, lowerBetter: true, fmt: (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(3)} s` },
    { key: "fuel", label: "Consumo", arr: data.fuel_per_lap, lowerBetter: true, fmt: (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(1)} L` },
    { key: "temp", label: "Temp max", arr: tempMax, lowerBetter: true, fmt: (v: number) => `${v > 0 ? "+" : ""}${Math.round(v)}°` },
    { key: "press", label: "Press", arr: pressAvg, lowerBetter: false, fmt: (v: number) => `${v > 0 ? "+" : ""}${v.toFixed(1)}` },
  ];
  const deltaColor = (v: number, lowerBetter: boolean) => {
    if (Math.abs(v) < 1e-9) return COLORS.muted;
    if (!lowerBetter) return COLORS.subtle;
    return v < 0 ? STATE.ok : STATE.alarm;
  };

  return (
    <div>
      {/* Toggle riferimento (giro precedente / media stint) */}
      <div className="mb-3 flex items-center gap-2">
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Riferimento</span>
        {(["prev", "avg"] as Mode[]).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            aria-pressed={mode === m}
            className={`rounded border px-2 py-0.5 font-mono text-[0.58rem] transition ${
              mode === m ? "border-accent text-white" : "border-line text-subtle hover:text-white"
            }`}
          >
            {m === "prev" ? "giro precedente" : "media stint"}
          </button>
        ))}
      </div>

      {/* Grafico Δ tempo per giro */}
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={rows} margin={{ top: 8, right: 12, bottom: 20, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
          <XAxis dataKey="lap" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} />
          <YAxis
            stroke={INSTRUMENT.tick}
            tick={{ fill: COLORS.muted, fontSize: 10 }}
            width={48}
            tickFormatter={(v: number) => `${v > 0 ? "+" : ""}${v.toFixed(1)}s`}
          />
          <ReferenceLine y={0} stroke={INSTRUMENT.track} strokeWidth={1} />
          <Tooltip
            cursor={{ fill: COLORS.text, fillOpacity: 0.06 }}
            contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
            labelStyle={{ color: COLORS.text }}
            itemStyle={{ color: COLORS.subtle }}
            labelFormatter={(l) => `Giro ${l}`}
          />
          <Bar dataKey="delta" name="Δ tempo (s)" isAnimationActive={false}>
            {rows.map((r) => (
              <Cell key={r.i} fill={barColor(r.i, r.delta)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">Giro</div>

      {/* Tabella delta multi-canale (vs giro precedente) */}
      <div className="pw-scroll mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="font-mono text-[0.6rem] uppercase text-muted">
              <th className="px-3 py-2 text-left">Giro</th>
              {chan.map((c) => (
                <th key={c.key} className="px-3 text-right">
                  Δ {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {laps.map((lap, i) => (
              <tr key={i} className="border-t border-line">
                <td className="px-3 py-2 font-mono">
                  {lap}
                  {i === bestIdx && (
                    <span className="ml-2 rounded px-1 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest text-white" style={{ background: STATE.best }}>
                      PB
                    </span>
                  )}
                </td>
                {chan.map((c) => {
                  const v = i === 0 ? null : c.arr[i] - c.arr[i - 1];
                  return (
                    <td key={c.key} className="px-3 text-right font-mono" style={{ color: v === null ? COLORS.muted : deltaColor(v, c.lowerBetter) }}>
                      {v === null ? "—" : c.fmt(v)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
