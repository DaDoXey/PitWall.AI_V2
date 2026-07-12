"use client";

// Confronto metà stint (megaprompt #7, FASE 8): modal aperto dal bottone
// "⇄ Confronto" della Sidebar. SCELTA DI SCOPE dichiarata (F7, decisa con
// Edoardo): la demo ha UNA sessione → si confrontano prima metà (giri 1–4) e
// seconda metà (giri 5–8) dello stint corrente — zero dati nuovi, zero numeri
// inventati (sostituisce QuickCompare, che usava una "precedente" statica finta).
// Idioma corsie (TelemetryLanes): hairline grid, tick monospace, tooltip muto,
// zero glow; un canale alla volta (stessi 10 canali dello Scatter, riusati).
// I numeri esatti vivono nella riga di sintesi (medie + Δ); i valori per giro
// restano nel Channel report della Telemetria (una rappresentazione per dato).
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE, STROKE } from "@/lib/instrument";
import { buildChannels } from "@/components/charts/ScatterPlot";
import type { SessionData } from "@/lib/telemetry";

// Identità serie (come TYRE_SERIES: colore = identità, non stato):
// metà 1 = blu (gomme/stint "freschi"), metà 2 = ambra (stint avanzato).
const HALF1_COLOR = COLORS.blue;
const HALF2_COLOR = COLORS.warn;

export default function StintCompareModal({ data, onClose }: { data: SessionData; onClose: () => void }) {
  const chans = buildChannels(data);
  const [selKey, setSelKey] = useState("lap_time");
  const ch = chans.find((c) => c.key === selKey) ?? chans[0];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Split a metà: 8 giri → 1–4 vs 5–8 (con N dispari il giro centrale va alla seconda metà).
  const n = ch.values.length;
  const mid = Math.floor(n / 2);
  const half1 = ch.values.slice(0, mid);
  const half2 = ch.values.slice(mid);
  const len = Math.min(half1.length, half2.length);
  const rows = Array.from({ length: len }, (_, i) => ({ rel: i + 1, h1: half1[i], h2: half2[i] }));

  const avg = (v: number[]) => v.reduce((s, x) => s + x, 0) / Math.max(1, v.length);
  const avg1 = avg(half1);
  const avg2 = avg(half2);
  const delta = avg2 - avg1;
  // Meno è meglio per tempo/consumo/temperatura; per la pressione il Δ è neutro
  // (dipende dalla finestra, non da "più alto/più basso") — idioma QuickCompare.
  const lowerIsBetter = !ch.key.startsWith("press");
  const deltaColor = !lowerIsBetter || Math.abs(delta) < 1e-9 ? COLORS.subtle : delta < 0 ? STATE.ok : STATE.alarm;
  const deltaDecimals = ch.key === "lap_time" ? 3 : Math.max(1, ch.decimals);

  const label1 = `Giri 1–${mid}`;
  const label2 = `Giri ${mid + 1}–${n}`;

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Confronto metà stint"
    >
      <motion.div
        className="pw-scroll max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-line border-t-2 border-t-accent bg-surface p-6"
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 16, scale: 0.98 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">Confronto metà stint</div>
            <div className="mt-0.5 text-sm text-subtle">
              {data.session.track} · {data.session.car} · {label1.toLowerCase()} vs {label2.toLowerCase()}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">stessa sessione · demo</span>
            <button onClick={onClose} className="font-mono text-sm text-muted transition hover:text-accent" aria-label="Chiudi">
              ✕
            </button>
          </div>
        </div>

        {/* Selettore canale (un canale alla volta, come da F7) */}
        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Canale</span>
          {chans.map((c) => (
            <button
              key={c.key}
              type="button"
              onClick={() => setSelKey(c.key)}
              aria-pressed={selKey === c.key}
              className={`rounded border px-2 py-0.5 font-mono text-[0.58rem] transition ${
                selKey === c.key ? "border-accent text-white" : "border-line text-subtle hover:text-white"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Legenda: identità delle due metà */}
        <div className="mt-3 flex gap-4">
          {[{ c: HALF1_COLOR, l: label1 }, { c: HALF2_COLOR, l: label2 }].map(({ c, l }) => (
            <span key={l} className="flex items-center gap-1.5 font-mono text-[0.6rem] text-subtle">
              <span className="h-0.5 w-3.5" style={{ background: c }} />
              {l}
            </span>
          ))}
        </div>

        {/* Corsia unica, 2 serie sovrapposte su giro relativo (idioma TelemetryLanes) */}
        <div className="mt-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">
          {ch.label} · {ch.unit}
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: 4 }}>
            <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
            <XAxis dataKey="rel" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} />
            <YAxis
              domain={["auto", "auto"]}
              stroke={INSTRUMENT.tick}
              tick={{ fill: COLORS.muted, fontSize: 10 }}
              tickFormatter={(v: number) => v.toFixed(ch.decimals)}
              width={52}
            />
            {/* Tooltip muto: solo cursore — i numeri vivono nella sintesi sotto */}
            <Tooltip content={() => null} cursor={{ stroke: COLORS.lineStrong, strokeWidth: 1 }} />
            <Line type="monotone" dataKey="h1" stroke={HALF1_COLOR} strokeWidth={STROKE.needle} strokeOpacity={0.9} dot={{ r: 1.6, strokeWidth: 0 }} activeDot={{ r: 3 }} isAnimationActive={false} />
            <Line type="monotone" dataKey="h2" stroke={HALF2_COLOR} strokeWidth={STROKE.needle} strokeOpacity={0.9} dot={{ r: 1.6, strokeWidth: 0 }} activeDot={{ r: 3 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
        <div className="mt-1 text-center font-mono text-[0.5rem] uppercase tracking-widest text-muted">Giro della metà (1–{len})</div>

        {/* Sintesi: le medie delle due metà + Δ (i numeri esatti vivono qui) */}
        <div className="mt-4 grid grid-cols-3 gap-2">
          <div className="rounded-lg border border-line bg-inset px-3 py-2 text-center">
            <div className="font-mono text-[0.5rem] uppercase tracking-widest" style={{ color: HALF1_COLOR }}>{label1} · media</div>
            <div className="mt-0.5 font-mono text-sm text-white">{ch.fmt(avg1)} {ch.unit}</div>
          </div>
          <div className="rounded-lg border border-line bg-inset px-3 py-2 text-center">
            <div className="font-mono text-[0.5rem] uppercase tracking-widest" style={{ color: HALF2_COLOR }}>{label2} · media</div>
            <div className="mt-0.5 font-mono text-sm text-white">{ch.fmt(avg2)} {ch.unit}</div>
          </div>
          <div className="rounded-lg border border-line bg-inset px-3 py-2 text-center">
            <div className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">Δ metà 2 − metà 1</div>
            <div className="mt-0.5 font-mono text-sm" style={{ color: deltaColor }}>
              {delta > 0 ? "+" : ""}{delta.toFixed(deltaDecimals)} {ch.unit}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
