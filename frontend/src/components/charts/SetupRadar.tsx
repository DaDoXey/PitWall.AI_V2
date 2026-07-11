"use client";

// Radar/spider bilanciamento (megaprompt #5, FASE 12): snapshot multi-canale su un
// giro selezionato. Layout a 2 colonne: RADAR (sinistra) + pannello SNAPSHOT/BILANCIAMENTO
// (destra) — così lo spazio è pieno di informazione pertinente invece che vuoto.
// Radar: 4 gomme come sull'auto (Ant.SX ↖, Ant.DX ↗, Post.DX ↘, Post.SX ↙), due poligoni
// Temperatura+Pressione normalizzati 0–100 nel giro (la forma = squilibrio). Valori reali
// nel tooltip e nel pannello. Solo presentazione.
import { useState } from "react";
import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT } from "@/lib/instrument";
import type { Corner, SessionData } from "@/lib/telemetry";

// Ordine radar (disposizione "auto" con startAngle=135): Ant.SX, Ant.DX, Post.DX, Post.SX.
const ORDER: { key: Corner; label: string }[] = [
  { key: "fl", label: "Ant.SX" },
  { key: "fr", label: "Ant.DX" },
  { key: "rr", label: "Post.DX" },
  { key: "rl", label: "Post.SX" },
];

type Datum = { corner: string; temp: number; press: number; tempRaw: number; pressRaw: number };

const norm = (v: number, mn: number, mx: number) => (mx > mn ? ((v - mn) / (mx - mn)) * 100 : 50);
const avg = (...xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;

function RadarTip({ active, payload }: { active?: boolean; payload?: Array<{ payload: Datum }> }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border px-2 py-1.5 font-mono text-[0.62rem]" style={{ background: COLORS.surface, borderColor: COLORS.line }}>
      <div className="mb-0.5 text-white">{p.corner}</div>
      <div style={{ color: COLORS.accent }}>Temp · {Math.round(p.tempRaw)} °C</div>
      <div style={{ color: COLORS.blue }}>Press · {p.pressRaw.toFixed(1)} psi</div>
    </div>
  );
}

export default function SetupRadar({ data }: { data: SessionData }) {
  const laps = data.laps ?? [];
  const [lapIdx, setLapIdx] = useState(Math.max(0, laps.length - 1)); // default: ultimo giro

  // Accessori valore per il giro selezionato (soglie/griglia 2×2 → TyreSnapshotGrid).
  const t = (c: Corner) => data.temp.series[c][lapIdx];
  const p = (c: Corner) => data.pressure.hot_series[c][lapIdx];

  // Radar normalizzato nel giro (la forma mostra lo squilibrio).
  const tempRaw = ORDER.map((o) => t(o.key));
  const pressRaw = ORDER.map((o) => p(o.key));
  const tMin = Math.min(...tempRaw), tMax = Math.max(...tempRaw);
  const pMin = Math.min(...pressRaw), pMax = Math.max(...pressRaw);
  const rows: Datum[] = ORDER.map((o, i) => ({
    corner: o.label,
    temp: norm(tempRaw[i], tMin, tMax),
    press: norm(pressRaw[i], pMin, pMax),
    tempRaw: tempRaw[i],
    pressRaw: pressRaw[i],
  }));

  // Bilanciamento (Δ = differenza medie): Ant↔Post e SX↔DX, per temp e pressione.
  const dAntPostT = avg(t("fl"), t("fr")) - avg(t("rl"), t("rr"));
  const dAntPostP = avg(p("fl"), p("fr")) - avg(p("rl"), p("rr"));
  const dSxDxT = avg(t("fl"), t("rl")) - avg(t("fr"), t("rr"));
  const dSxDxP = avg(p("fl"), p("rl")) - avg(p("fr"), p("rr"));

  const step = (d: number) => setLapIdx((i) => Math.min(laps.length - 1, Math.max(0, i + d)));
  const lapNum = laps[lapIdx] ?? lapIdx + 1;

  const sign = (v: number, dec: number) => `${v > 0 ? "+" : ""}${v.toFixed(dec)}`;

  return (
    <div>
      {/* Selettore giro (stepper) */}
      <div className="mb-3 flex items-center gap-2">
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Giro</span>
        <button
          type="button"
          onClick={() => step(-1)}
          disabled={lapIdx <= 0}
          className="rounded border border-line px-2 py-0.5 font-mono text-[0.7rem] text-subtle transition enabled:hover:border-accent enabled:hover:text-white disabled:opacity-30"
          aria-label="Giro precedente"
        >
          ◀
        </button>
        <span className="w-10 text-center font-mono text-sm text-white">{lapNum}</span>
        <button
          type="button"
          onClick={() => step(1)}
          disabled={lapIdx >= laps.length - 1}
          className="rounded border border-line px-2 py-0.5 font-mono text-[0.7rem] text-subtle transition enabled:hover:border-accent enabled:hover:text-white disabled:opacity-30"
          aria-label="Giro successivo"
        >
          ▶
        </button>
        <span className="ml-auto font-mono text-[0.5rem] uppercase tracking-widest text-muted">di {laps.length}</span>
      </div>

      {/* 2 colonne: radar (sx) + snapshot/bilanciamento (dx) */}
      <div className="grid gap-5 lg:grid-cols-2 lg:items-center">
        {/* Radar */}
        <div>
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={rows} startAngle={135} endAngle={-225} outerRadius="80%" margin={{ top: 16, right: 24, bottom: 8, left: 24 }}>
              <PolarGrid stroke={INSTRUMENT.grid} />
              <PolarAngleAxis dataKey="corner" tick={{ fill: COLORS.subtle, fontSize: 12 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar name="Temperatura" dataKey="temp" stroke={COLORS.accent} strokeWidth={2} fill={COLORS.accent} fillOpacity={0.2} isAnimationActive={false} />
              <Radar name="Pressione" dataKey="press" stroke={COLORS.blue} strokeWidth={2} fill={COLORS.blue} fillOpacity={0.16} isAnimationActive={false} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Tooltip content={<RadarTip />} />
            </RadarChart>
          </ResponsiveContainer>
          <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">
            Forma = squilibrio (valori normalizzati nel giro)
          </div>
        </div>

        {/* Bilanciamento (i valori esatti 2×2 vivono SOLO nel box "Valori" delle
            corsie — Snapshot rimosso in megaprompt #6 F7, decisione di Edoardo:
            stessa griglia dello stesso componente due volte nella stessa tab). */}
        <div className="flex flex-col gap-3">
          <div>
            <div className="mb-1.5 font-mono text-[0.55rem] uppercase tracking-widest text-muted">Bilanciamento</div>
            <div className="flex flex-col gap-1">
              {[
                { label: "Ant ↔ Post", dt: dAntPostT, dp: dAntPostP },
                { label: "SX ↔ DX", dt: dSxDxT, dp: dSxDxP },
              ].map((b) => (
                <div key={b.label} className="flex items-center justify-between rounded-md border border-line bg-inset px-2 py-1.5 font-mono text-[0.62rem]">
                  <span className="text-subtle">{b.label}</span>
                  <span className="flex gap-3">
                    <span className="text-muted">
                      Δt <span className="text-white">{sign(b.dt, 0)}°</span>
                    </span>
                    <span className="text-muted">
                      Δp <span className="text-white">{sign(b.dp, 1)}</span>
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
