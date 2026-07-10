"use client";

// Tabella giro-per-giro con codifica visiva (FASE 5): numeri colorati per soglia
// (riusa le stesse soglie del cross-check — temp.limit e hot_window, nessuna nuova)
// + mini data-bar per cella proporzionale al range della colonna. Estratta da
// telemetry/page.tsx per pulizia; nessuna logica di dominio, solo presentazione.
import { COLORS } from "@/lib/theme";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";

const CORNERS: Corner[] = ["fl", "fr", "rl", "rr"];
const frac = (v: number, lo: number, hi: number) => (hi > lo ? (v - lo) / (hi - lo) : 0.5);

// Cella numerica: colore-testo per soglia + barra di fondo proporzionale al range colonna.
function Cell({ value, color, f }: { value: string; color: string; f: number }) {
  return (
    <td className="relative py-1 pr-1 text-right font-mono">
      <span style={{ color }}>{value}</span>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute bottom-0 right-0 h-[2px] rounded-full"
        style={{ width: `${Math.max(0, Math.min(1, f)) * 100}%`, background: color, opacity: 0.5 }}
      />
    </td>
  );
}

export default function LapTable({ data }: { data: SessionData }) {
  const limit = data.temp.limit;
  const [plo, phi] = data.pressure.hot_window;

  // Range colonna per le mini-bar (scala condivisa così le barre sono confrontabili).
  const allTemp = CORNERS.flatMap((k) => data.temp.series[k]);
  const [tMin, tMax] = [Math.min(...allTemp), Math.max(...allTemp)];
  const allPress = CORNERS.flatMap((k) => data.pressure.hot_series[k]);
  const [pMin, pMax] = [Math.min(...allPress), Math.max(...allPress)];
  const [fMin, fMax] = [Math.min(...data.fuel_per_lap), Math.max(...data.fuel_per_lap)];

  // Soglie riusate dal cross-check: temp oltre limite = rosso; pressione fuori finestra = ambra.
  const tempColor = (v: number) => (v > limit ? COLORS.accent : COLORS.ok);
  const pressColor = (v: number) => (v < plo || v > phi ? COLORS.warn : COLORS.ok);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="font-mono text-[0.62rem] uppercase text-muted">
          <th className="py-1 text-left">Giro</th>
          <th className="text-right">Cons. (L)</th>
          {TYRE_SERIES.map((c) => (
            <th key={c.key} className="text-right">
              T {c.label}
            </th>
          ))}
          {TYRE_SERIES.map((c) => (
            <th key={`p-${c.key}`} className="text-right">
              P {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.laps.map((lap, i) => (
          <tr key={lap} className="border-t border-line">
            <td className="py-1 font-mono">{lap}</td>
            <Cell
              value={data.fuel_per_lap[i].toFixed(1)}
              color={COLORS.subtle}
              f={frac(data.fuel_per_lap[i], fMin, fMax)}
            />
            {TYRE_SERIES.map((c) => {
              const v = data.temp.series[c.key][i];
              return <Cell key={c.key} value={String(v)} color={tempColor(v)} f={frac(v, tMin, tMax)} />;
            })}
            {TYRE_SERIES.map((c) => {
              const v = data.pressure.hot_series[c.key][i];
              return <Cell key={`p-${c.key}`} value={String(v)} color={pressColor(v)} f={frac(v, pMin, pMax)} />;
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
