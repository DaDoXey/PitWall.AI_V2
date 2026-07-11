"use client";

// Sezione Lap Times (megaprompt #5, FASE 7): tabella di TUTTI i giri con tempo e
// gap sul giro più veloce. Sostituisce il singolo "best lap" isolato con l'elenco
// completo. Il giro più veloce è EVIDENZIATO (marker PB, per ora neutro): il colore
// semantico viola/fucsia arriva in FASE 8. Solo presentazione, nessuna logica di dominio.
import { formatLapTime, type SessionData } from "@/lib/telemetry";
import { COLORS } from "@/lib/theme";
import { STATE } from "@/lib/instrument";

export default function LapTimesTable({ data }: { data: SessionData }) {
  const times = data.lap_times ?? [];
  const best = times.length ? Math.min(...times) : 0;
  const bestIdx = times.indexOf(best);

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="font-mono text-[0.62rem] uppercase text-muted">
          <th className="px-3 py-2 text-left">Giro</th>
          <th className="px-3 text-right">Tempo</th>
          <th className="px-3 text-right">Δ best</th>
        </tr>
      </thead>
      <tbody>
        {times.map((t, i) => {
          const isBest = i === bestIdx;
          const gap = t - best;
          return (
            <tr key={i} className="border-t border-line">
              <td className="px-3 py-2 font-mono">
                {data.laps[i] ?? i + 1}
                {isBest && (
                  <span
                    className="ml-2 rounded px-1 py-0.5 font-mono text-[0.5rem] uppercase tracking-widest text-white"
                    style={{ background: STATE.best }}
                  >
                    PB
                  </span>
                )}
              </td>
              <td
                className="px-3 text-right font-mono"
                style={{ color: isBest ? STATE.best : COLORS.subtle, fontWeight: isBest ? 700 : 400 }}
              >
                {formatLapTime(t)}
              </td>
              <td className="px-3 text-right font-mono text-muted">{isBest ? "—" : `+${gap.toFixed(3)}`}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
