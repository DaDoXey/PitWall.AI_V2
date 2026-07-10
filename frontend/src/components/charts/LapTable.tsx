"use client";

// Tabella giro-per-giro (megaprompt #2, FASE 3): numeri colorati per soglia
// (riusa le soglie del cross-check — temp.limit e hot_window, nessuna nuova),
// spaziatura ampia e resa "strumento" — niente decori (le mini data-bar sono
// state rimosse: causavano sovrapposizione visiva tra colonne ed erano decorative,
// contro la direttiva analogica). Solo presentazione, nessuna logica di dominio.
import { COLORS } from "@/lib/theme";
import { STATE } from "@/lib/instrument";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";

const CORNERS: Corner[] = ["fl", "fr", "rl", "rr"];

// Cella numerica: solo numero colorato per stato, ampio respiro orizzontale/verticale.
function Cell({ value, color }: { value: string; color: string }) {
  return (
    <td className="py-2 px-3 text-right font-mono" style={{ color }}>
      {value}
    </td>
  );
}

export default function LapTable({ data }: { data: SessionData }) {
  const limit = data.temp.limit;
  const [plo, phi] = data.pressure.hot_window;

  // Soglie riusate dal cross-check: temp oltre limite = allarme; pressione fuori finestra = warn.
  const tempColor = (v: number) => (v > limit ? STATE.alarm : STATE.ok);
  const pressColor = (v: number) => (v < plo || v > phi ? STATE.warn : STATE.ok);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="font-mono text-[0.62rem] uppercase text-muted">
          <th className="py-2 px-3 text-left">Giro</th>
          <th className="px-3 text-right">Cons. (L)</th>
          {TYRE_SERIES.map((c) => (
            <th key={c.key} className="px-3 text-right">
              T {c.label}
            </th>
          ))}
          {TYRE_SERIES.map((c) => (
            <th key={`p-${c.key}`} className="px-3 text-right">
              P {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.laps.map((lap, i) => (
          <tr key={lap} className="border-t border-line">
            <td className="py-2 px-3 font-mono">{lap}</td>
            <Cell value={data.fuel_per_lap[i].toFixed(1)} color={COLORS.subtle} />
            {TYRE_SERIES.map((c) => {
              const v = data.temp.series[c.key][i];
              return <Cell key={c.key} value={String(v)} color={tempColor(v)} />;
            })}
            {TYRE_SERIES.map((c) => {
              const v = data.pressure.hot_series[c.key][i];
              return <Cell key={`p-${c.key}`} value={String(v)} color={pressColor(v)} />;
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
