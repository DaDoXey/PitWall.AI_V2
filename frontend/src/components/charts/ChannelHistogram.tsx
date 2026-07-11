"use client";

// Histogram distribuzione canale (megaprompt #5, FASE 11): distribuzione di un canale
// selezionabile (tempo giro / consumo / temp / pressione) sui giri della sessione.
// Barre = n. giri per fascia; dove esiste una soglia, la fascia fuori-spec usa il
// colore di stato (temp oltre limite = alarm, pressione fuori finestra = warn).
// Niente label X interne (lezione F10-fix): didascalie in HTML. Solo presentazione.
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import type { SessionData } from "@/lib/telemetry";

type Chan = { key: string; label: string; unit: string; values: number[]; decimals: number; classify?: (mid: number) => string };

const NBINS = 5;

export default function ChannelHistogram({ data }: { data: SessionData }) {
  const [lo, hi] = data.pressure.hot_window;
  const limit = data.temp.limit;

  const channels: Chan[] = [
    { key: "lap", label: "Tempo giro", unit: "s", values: data.lap_times ?? [], decimals: 2 },
    { key: "fuel", label: "Consumo", unit: "L", values: data.fuel_per_lap, decimals: 1 },
    { key: "temp", label: "Temp Post.DX", unit: "°C", values: data.temp.series.rr, decimals: 0, classify: (m) => (m > limit ? STATE.alarm : STATE.ok) },
    { key: "press", label: "Press Post.DX", unit: "psi", values: data.pressure.hot_series.rr, decimals: 1, classify: (m) => (m < lo || m > hi ? STATE.warn : STATE.ok) },
  ];

  const [sel, setSel] = useState("temp");
  const ch = channels.find((c) => c.key === sel) ?? channels[0];

  const vals = ch.values;
  const min = vals.length ? Math.min(...vals) : 0;
  const max = vals.length ? Math.max(...vals) : 1;
  const w = (max - min) || 1;
  const step = w / NBINS;
  const bins = Array.from({ length: NBINS }, (_, i) => {
    const mid = min + (i + 0.5) * step;
    return { label: mid.toFixed(ch.decimals), count: 0, mid };
  });
  vals.forEach((v) => {
    const idx = Math.min(NBINS - 1, Math.max(0, Math.floor((v - min) / step)));
    bins[idx].count++;
  });
  const fillFor = (mid: number) => (ch.classify ? ch.classify(mid) : COLORS.subtle);

  return (
    <div>
      {/* Selettore canale */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Canale</span>
        {channels.map((c) => (
          <button
            key={c.key}
            type="button"
            onClick={() => setSel(c.key)}
            aria-pressed={sel === c.key}
            className={`rounded border px-2 py-0.5 font-mono text-[0.58rem] transition ${
              sel === c.key ? "border-accent text-white" : "border-line text-subtle hover:text-white"
            }`}
          >
            {c.label}
          </button>
        ))}
        <span className="ml-auto font-mono text-[0.5rem] uppercase tracking-widest text-muted">{ch.unit}</span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={bins} margin={{ top: 8, right: 12, bottom: 8, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
          <XAxis dataKey="label" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 9 }} interval={0} />
          <YAxis allowDecimals={false} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={28} />
          <Tooltip
            cursor={{ fill: COLORS.text, fillOpacity: 0.06 }}
            contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
            labelStyle={{ color: COLORS.text }}
            itemStyle={{ color: COLORS.subtle }}
            labelFormatter={(l) => `≈ ${l} ${ch.unit}`}
          />
          <Bar dataKey="count" name="Giri" isAnimationActive={false}>
            {bins.map((b, i) => (
              <Cell key={i} fill={fillFor(b.mid)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">
        Distribuzione · {ch.label} ({ch.unit}) — n. giri per fascia
      </div>
    </div>
  );
}
