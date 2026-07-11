"use client";

// Overlay confronto FL/FR/RL/RR (megaprompt #5, FASE 10): sovrappone l'andamento
// delle 4 posizioni gomma sugli stessi assi, per confronto diretto. Toggle canale
// Temperatura/Pressione. Riusa i colori TYRE_SERIES e i token strumento (griglia
// hairline, no glow); linee-soglia dai riferimenti esistenti (limite temp / finestra
// pressioni). Solo presentazione, nessuna logica di dominio.
import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT } from "@/lib/instrument";
import { TYRE_SERIES, type SessionData } from "@/lib/telemetry";

type Ch = "temp" | "press";

export default function TyreOverlay({ data }: { data: SessionData }) {
  const [ch, setCh] = useState<Ch>("temp");

  const laps = data.laps ?? [];
  const series = ch === "temp" ? data.temp.series : data.pressure.hot_series;
  const rows = laps.map((lap, i) => ({
    giro: lap,
    fl: series.fl[i],
    fr: series.fr[i],
    rl: series.rl[i],
    rr: series.rr[i],
  }));
  const unit = ch === "temp" ? "°C" : "psi";
  const refs = ch === "temp" ? [data.temp.limit] : data.pressure.hot_window;

  return (
    <div>
      {/* Toggle canale (temperatura / pressione) */}
      <div className="mb-3 flex items-center gap-2">
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Canale</span>
        {(["temp", "press"] as Ch[]).map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setCh(c)}
            aria-pressed={ch === c}
            className={`rounded border px-2 py-0.5 font-mono text-[0.58rem] transition ${
              ch === c ? "border-accent text-white" : "border-line text-subtle hover:text-white"
            }`}
          >
            {c === "temp" ? "Temperatura" : "Pressione"}
          </button>
        ))}
        <span className="ml-auto font-mono text-[0.5rem] uppercase tracking-widest text-muted">{unit}</span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 20, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
          <XAxis dataKey="giro" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} />
          <YAxis stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={40} domain={["auto", "auto"]} />
          {refs.map((y, idx) => (
            <ReferenceLine key={idx} y={y} stroke={COLORS.muted} strokeDasharray="4 4" strokeWidth={1} />
          ))}
          <Tooltip
            contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
            labelFormatter={(l) => `Giro ${l}`}
          />
          <Legend verticalAlign="top" align="center" wrapperStyle={{ fontSize: 11, paddingBottom: 6 }} />
          {TYRE_SERIES.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={s.color}
              strokeWidth={1.5}
              dot={{ r: 2, fill: s.color, strokeWidth: 0 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">Giro</div>
    </div>
  );
}
