// Salute sessione — derivazione di PRESENTAZIONE dello stato aggregato (megaprompt #5, FASE 3).
// Non introduce soglie nuove: riusa temp.limit, pressure.hot_window e la regola
// "consumo stabile ≤ 0.4 L" già usate altrove (cross-check Telemetria, KPI Dashboard).
// Il colore comunica SOLO lo stato: ok (verde) / warn (ambra) / alarm (rosso).
import { STATE } from "@/lib/instrument";
import type { Corner, SessionData } from "@/lib/telemetry";

export type HealthState = "ok" | "warn" | "alarm";

export const HEALTH_COLOR: Record<HealthState, string> = {
  ok: STATE.ok,
  warn: STATE.warn,
  alarm: STATE.alarm,
};

export const HEALTH_LABEL: Record<HealthState, string> = {
  ok: "Nominale",
  warn: "Attenzione",
  alarm: "Critico",
};

export interface HealthItem {
  key: string;
  label: string;
  state: HealthState;
  detail: string;
}

export interface Health {
  overall: HealthState;
  items: HealthItem[];
}

const CORNERS: Corner[] = ["fl", "fr", "rl", "rr"];
const RANK: Record<HealthState, number> = { ok: 0, warn: 1, alarm: 2 };
const worst = (a: HealthState, b: HealthState): HealthState => (RANK[b] > RANK[a] ? b : a);

// Banda "al limite" per le pressioni: rispecchia PressureGauge (scelta di
// PRESENTAZIONE, non una soglia dati) così il semaforo racconta la stessa
// storia dei gauge a caldo.
const PRESS_NEAR = 0.5;

export function buildHealth(d: SessionData): Health {
  // ── Temperature: oltre il limite finestra = critico (regola del cross-check). ──
  const hottest = CORNERS.reduce((a, b) => (d.temp.max[b] > d.temp.max[a] ? b : a));
  const tMax = d.temp.max[hottest];
  const tempState: HealthState = tMax > d.temp.limit ? "alarm" : "ok";
  const tempDetail =
    tempState === "alarm"
      ? `${d.tyre_labels[hottest]} ${tMax}°C oltre ${d.temp.limit}°C`
      : `max ${tMax}°C entro ${d.temp.limit}°C`;

  // ── Pressioni: gomma peggiore rispetto alla finestra a caldo (regola dei gauge). ──
  const [lo, hi] = d.pressure.hot_window;
  const dist = (v: number) => (v < lo ? lo - v : v > hi ? v - hi : 0);
  const pWorst = CORNERS.reduce((a, b) => (dist(d.pressure.hot[b]) > dist(d.pressure.hot[a]) ? b : a));
  const pd = dist(d.pressure.hot[pWorst]);
  const pressState: HealthState = pd === 0 ? "ok" : pd <= PRESS_NEAR ? "warn" : "alarm";
  const pressDetail =
    pressState === "ok"
      ? `tutte in finestra ${lo}–${hi} psi`
      : `${d.tyre_labels[pWorst]} ${d.pressure.hot[pWorst].toFixed(1)} psi fuori finestra`;

  // ── Carburante: consumo stabile se escursione ≤ 0.4 L (stessa regola del cross-check). ──
  const spread = Math.max(...d.fuel_per_lap) - Math.min(...d.fuel_per_lap);
  const fuelState: HealthState = spread <= 0.4 ? "ok" : "warn";
  const fuelDetail = `${fuelState === "ok" ? "stabile" : "variabile"} · Δ ${spread.toFixed(1)} L/giro`;

  const items: HealthItem[] = [
    { key: "temp", label: "Gomme", state: tempState, detail: tempDetail },
    { key: "press", label: "Pressioni", state: pressState, detail: pressDetail },
    { key: "fuel", label: "Carburante", state: fuelState, detail: fuelDetail },
  ];

  const overall = items.reduce<HealthState>((acc, it) => worst(acc, it.state), "ok");
  return { overall, items };
}
