"use client";

// Confronto rapido con la sessione precedente (megaprompt #5, FASE 6).
// La demo ha UNA sola sessione: usiamo un riferimento statico "precedente (demo)"
// lato client — coerente con la natura demo-mode dell'app (numeri illustrativi),
// ESPLICITAMENTE etichettato come demo, NON telemetria reale. Quando ci sarà lo
// storico sessioni, il "precedente" verrà da lì.
import { STATE } from "@/lib/instrument";
import { COLORS } from "@/lib/theme";
import type { SessionData } from "@/lib/telemetry";

// Riferimento demo: uno stint Monza/BMW leggermente peggiore del corrente.
const PREV = { bestLap: "1:48.4", fuelAvg: 3.4, tempMax: 108, pressAvg: 28.3 };

function lapToSec(t: string): number {
  const [m, s] = t.split(":");
  return parseInt(m, 10) * 60 + parseFloat(s);
}

type Row = { label: string; cur: string; prev: string; delta: number; unit: string; lowerIsBetter: boolean };

export default function QuickCompare({ data }: { data: SessionData }) {
  const s = data.session;
  const curTempMax = Math.max(...Object.values(data.temp.max));

  const rows: Row[] = [
    { label: "Best lap", cur: s.best_lap, prev: PREV.bestLap, delta: lapToSec(s.best_lap) - lapToSec(PREV.bestLap), unit: "s", lowerIsBetter: true },
    { label: "Consumo", cur: s.fuel_avg_per_lap.toFixed(1), prev: PREV.fuelAvg.toFixed(1), delta: s.fuel_avg_per_lap - PREV.fuelAvg, unit: "L/g", lowerIsBetter: true },
    { label: "Temp max", cur: String(curTempMax), prev: String(PREV.tempMax), delta: curTempMax - PREV.tempMax, unit: "°C", lowerIsBetter: true },
    { label: "Press. media", cur: data.pressure.avg_hot.toFixed(1), prev: PREV.pressAvg.toFixed(1), delta: data.pressure.avg_hot - PREV.pressAvg, unit: "psi", lowerIsBetter: false },
  ];

  const deltaColor = (r: Row) => {
    if (!r.lowerIsBetter || Math.abs(r.delta) < 1e-9) return COLORS.subtle;
    return r.delta < 0 ? STATE.ok : STATE.alarm; // migliorato = verde, peggiorato = rosso
  };
  const fmtDelta = (r: Row) => `${r.delta > 0 ? "+" : ""}${r.delta.toFixed(r.unit === "s" ? 2 : 1)}`;

  return (
    <div className="rounded-lg border border-line bg-inset p-2">
      <div className="mb-1.5 flex items-center justify-between">
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">Corrente ↔ precedente</span>
        <span className="font-mono text-[0.48rem] uppercase tracking-widest text-muted">demo</span>
      </div>
      <div className="flex flex-col gap-1">
        {rows.map((r) => (
          <div key={r.label} className="flex items-center justify-between gap-2 font-mono text-[0.58rem]">
            <span className="text-subtle">{r.label}</span>
            <span className="flex items-center gap-2">
              <span className="text-white">{r.cur}</span>
              <span className="text-muted">vs {r.prev}</span>
              <span className="w-12 text-right" style={{ color: deltaColor(r) }}>
                {fmtDelta(r)} {r.unit}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
