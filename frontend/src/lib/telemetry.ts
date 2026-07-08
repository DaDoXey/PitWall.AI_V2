import { COLORS } from "./theme";

export type Corner = "fl" | "fr" | "rl" | "rr";

// Interpolazione blu→rosso su scala [lo,hi] — portata da v1 (components.temp_to_color).
export function tempToColor(value: number, scale: [number, number] = [80, 105]): string {
  const [lo, hi] = scale;
  const t = hi > lo ? Math.max(0, Math.min(1, (value - lo) / (hi - lo))) : 0;
  const cold = [59, 130, 246];
  const hot = [232, 0, 45];
  const ch = (i: number) => Math.round(cold[i] + (hot[i] - cold[i]) * t);
  const hex = (n: number) => n.toString(16).padStart(2, "0");
  return `#${hex(ch(0))}${hex(ch(1))}${hex(ch(2))}`;
}

// Colori serie gomme (coerenti con la v1).
export const TYRE_SERIES: { key: Corner; label: string; color: string }[] = [
  { key: "fl", label: "Ant.SX", color: COLORS.blue },
  { key: "fr", label: "Ant.DX", color: COLORS.ok },
  { key: "rl", label: "Post.SX", color: COLORS.warn },
  { key: "rr", label: "Post.DX", color: COLORS.accent },
];

export interface SessionData {
  session: {
    track: string;
    track_nick: string;
    car: string;
    car_year: string;
    laps: number;
    best_lap: string;
    stint: string;
    fuel_avg_per_lap: number;
    fuel_total: number;
  };
  tyre_labels: Record<Corner, string>;
  temp: {
    series: Record<Corner, number[]>;
    max: Record<Corner, number>;
    limit: number;
    scale: [number, number];
  };
  pressure: {
    hot: Record<Corner, number>;
    hot_window: [number, number];
    hot_series: Record<Corner, number[]>;
    cold: Record<Corner, number>;
    cold_window: [number, number];
    cold_amber_margin: number;
    avg_hot: number;
  };
  fuel_per_lap: number[];
  laps: number[];
  suggested_params: string[];
}
