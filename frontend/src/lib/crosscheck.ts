// Cross-check dati sessione (megaprompt #5, FASE 5) — ESTRATTO da telemetry/page.tsx
// per riuso tra Telemetria (elenco completo) e Sidebar (feed avvisi). Logica di
// PRESENTAZIONE: riusa temp.limit, pressure.hot_window e la regola "consumo stabile
// ≤ 0.4 L" già esistenti; nessuna soglia nuova. Il colore comunica solo lo stato.
import { STATE } from "@/lib/instrument";
import type { Corner, SessionData } from "@/lib/telemetry";

export type CheckLevel = "ok" | "warn" | "alarm";
export interface Check {
  level: CheckLevel;
  color: string;
  msg: string;
}

const CORNERS: Corner[] = ["fl", "fr", "rl", "rr"];

/** Elenco completo (incongruenze + eventuale conferma "ok"), come nella Telemetria. */
export function buildCrossChecks(d: SessionData): Check[] {
  const out: Check[] = [];
  const labels = d.tyre_labels;

  CORNERS.forEach((k) => {
    const mx = d.temp.max[k];
    if (mx > d.temp.limit)
      out.push({ level: "alarm", color: STATE.alarm, msg: `${labels[k]}: ${mx}°C oltre il limite finestra (${d.temp.limit}°C)` });
  });

  const [lo, hi] = d.pressure.hot_window;
  CORNERS.forEach((k) => {
    const v = d.pressure.hot[k];
    if (v < lo) out.push({ level: "warn", color: STATE.warn, msg: `${labels[k]}: ${v} psi sotto la finestra a caldo (${lo}–${hi})` });
    else if (v > hi) out.push({ level: "warn", color: STATE.warn, msg: `${labels[k]}: ${v} psi oltre la finestra a caldo (${lo}–${hi})` });
  });

  const spread = Math.max(...d.fuel_per_lap) - Math.min(...d.fuel_per_lap);
  if (spread <= 0.4)
    out.push({ level: "ok", color: STATE.ok, msg: `Consumo stabile (variazione ${spread.toFixed(1)} L/giro su ${d.session.laps} giri)` });

  if (out.length === 0) out.push({ level: "ok", color: STATE.ok, msg: "Nessuna incongruenza rilevata" });
  return out;
}

/** Solo le anomalie (warn/alarm) — per il feed avvisi rapidi della Sidebar. */
export function buildAlerts(d: SessionData): Check[] {
  return buildCrossChecks(d).filter((c) => c.level !== "ok");
}
