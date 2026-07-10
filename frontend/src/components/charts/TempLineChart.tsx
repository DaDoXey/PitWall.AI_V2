"use client";

// Grafico temperature gomme (megaprompt #2, FASE 4): resa "analogica" — linee
// sottili senza glow, dot minimi, griglia/assi hairline (token instrument.ts),
// soglia 95°C come tratteggio hairline. Legenda con più aria (spaziatura voci +
// distanza dal grafico) per evitare le sovrapposizioni. I 4 colori-serie
// (blu/verde/ambra/rosso) restano per distinguere le gomme.
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STROKE } from "@/lib/instrument";
import { useReducedMotion } from "@/lib/motion";
import { TYRE_SERIES, type SessionData } from "@/lib/telemetry";

export default function TempLineChart({ data }: { data: SessionData }) {
  const reduce = useReducedMotion();
  const rows = data.laps.map((lap, i) => ({
    lap,
    fl: data.temp.series.fl[i],
    fr: data.temp.series.fr[i],
    rl: data.temp.series.rl[i],
    rr: data.temp.series.rr[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 24, left: -8 }}>
        <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
        <XAxis
          dataKey="lap"
          stroke={INSTRUMENT.tick}
          tick={{ fill: COLORS.muted, fontSize: 11 }}
          label={{ value: "Giro", position: "insideBottom", offset: -6, fill: COLORS.muted, fontSize: 11 }}
        />
        <YAxis
          domain={[74, 110]}
          stroke={INSTRUMENT.tick}
          tick={{ fill: COLORS.muted, fontSize: 11 }}
          tickFormatter={(v) => `${v}°`}
        />
        <Tooltip
          contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
          labelStyle={{ color: COLORS.subtle }}
          cursor={{ stroke: COLORS.lineStrong, strokeWidth: 1 }}
        />
        {/* Legenda: più spazio tra voci (formatter) e dal grafico (paddingTop) */}
        <Legend
          iconSize={10}
          wrapperStyle={{ fontSize: 11, paddingTop: 14 }}
          formatter={(value) => <span style={{ marginRight: 16, color: COLORS.subtle }}>{value}</span>}
        />
        {/* Soglia limite: tratteggio hairline, non un elemento "acceso" */}
        <ReferenceLine
          y={data.temp.limit}
          stroke={COLORS.muted}
          strokeDasharray="4 4"
          strokeWidth={1}
          label={{ value: `${data.temp.limit}°C`, fill: COLORS.muted, fontSize: 10, position: "insideTopRight" }}
        />
        {TYRE_SERIES.map((s) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={s.color}
            strokeWidth={STROKE.needle}
            strokeOpacity={0.9}
            dot={{ r: 1.8, strokeWidth: 0 }}
            activeDot={{ r: 3 }}
            isAnimationActive={!reduce}
            animationDuration={900}
            animationEasing="ease-out"
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
