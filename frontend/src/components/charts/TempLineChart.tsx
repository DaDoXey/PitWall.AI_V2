"use client";

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
import { TYRE_SERIES, type SessionData } from "@/lib/telemetry";

export default function TempLineChart({ data }: { data: SessionData }) {
  const rows = data.laps.map((lap, i) => ({
    lap,
    fl: data.temp.series.fl[i],
    fr: data.temp.series.fr[i],
    rl: data.temp.series.rl[i],
    rr: data.temp.series.rr[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: -8 }}>
        <CartesianGrid stroke={COLORS.line} vertical={false} />
        <XAxis
          dataKey="lap"
          stroke={COLORS.muted}
          tick={{ fill: COLORS.muted, fontSize: 11 }}
          label={{ value: "Giro", position: "insideBottom", offset: -4, fill: COLORS.muted, fontSize: 11 }}
        />
        <YAxis
          domain={[74, 110]}
          stroke={COLORS.muted}
          tick={{ fill: COLORS.muted, fontSize: 11 }}
          tickFormatter={(v) => `${v}°`}
        />
        <Tooltip
          contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: COLORS.subtle }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <ReferenceLine
          y={data.temp.limit}
          stroke={COLORS.subtle}
          strokeDasharray="5 4"
          label={{ value: `${data.temp.limit}°C`, fill: COLORS.subtle, fontSize: 10, position: "insideTopRight" }}
        />
        {TYRE_SERIES.map((s) => (
          <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color} strokeWidth={2.2} dot={{ r: 2.5 }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
