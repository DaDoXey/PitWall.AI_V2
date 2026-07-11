"use client";

// Griglia 2×2 dei valori reali temp/pressione per gomma su un giro selezionato
// (megaprompt #6, FASE 5): ESTRATTA dal pannello "Snapshot giro" di SetupRadar
// per essere condivisa col box "Valori" delle corsie (TelemetryLanes) — un solo
// componente invece di due copie. Soglie riusate: temp.limit (alarm) e finestra
// pressioni a caldo (warn). Colore = solo stato, nessuna logica nuova.
import { STATE } from "@/lib/instrument";
import type { Corner, SessionData } from "@/lib/telemetry";

// Ordine griglia 2×2 (come l'auto vista dall'alto).
const GRID: { key: Corner; label: string }[] = [
  { key: "fl", label: "Ant.SX" },
  { key: "fr", label: "Ant.DX" },
  { key: "rl", label: "Post.SX" },
  { key: "rr", label: "Post.DX" },
];

export default function TyreSnapshotGrid({ data, lapIdx }: { data: SessionData; lapIdx: number }) {
  const t = (c: Corner) => data.temp.series[c][lapIdx];
  const p = (c: Corner) => data.pressure.hot_series[c][lapIdx];
  const limit = data.temp.limit;
  const [plo, phi] = data.pressure.hot_window;
  const tc = (v: number) => (v > limit ? STATE.alarm : STATE.ok);
  const pc = (v: number) => (v < plo || v > phi ? STATE.warn : STATE.ok);

  return (
    <div className="grid grid-cols-2 gap-2">
      {GRID.map((c) => (
        <div key={c.key} className="rounded-lg border border-line bg-inset p-2 text-center">
          <div className="font-mono text-[0.55rem] uppercase tracking-wider text-subtle">{c.label}</div>
          <div className="font-mono text-sm" style={{ color: tc(t(c.key)) }}>{Math.round(t(c.key))} °C</div>
          <div className="font-mono text-[0.7rem]" style={{ color: pc(p(c.key)) }}>{p(c.key).toFixed(1)} psi</div>
        </div>
      ))}
    </div>
  );
}
