// Logica pura della pagina Setup (Fase 5), portata dalla v1 (ui/setup_view.py):
// tipi della risposta /api/setup-params, layout dichiarativo dei gruppi per tab,
// formattazione valore e colore-stato delle pressioni vs finestra a freddo.
// I range/default/unit arrivano dal backend (modulo dati ACC): qui solo presentazione.

import { COLORS } from "@/lib/theme";

export type Param = {
  label: string;
  min: number;
  max: number;
  step: number;
  unit: string;
  default: number;
  tip?: string;
};
export type Section = { label: string; params: Record<string, Param> };
export type SetupParams = Record<string, Section>;

// Finestra pressioni a FREDDO (psi) per la colorazione — speculare a demo_data.py
// (COLD_PRESS_WINDOW / COLD_PRESS_AMBER_MARGIN). Base version: costante lato client;
// in futuro cablabile a un endpoint per single-source-of-truth.
export const COLD_PRESS_WINDOW: [number, number] = [24.5, 25.5];
export const COLD_PRESS_AMBER_MARGIN = 0.6;

/** Verde in finestra, ambra entro il margine, rosso oltre. Solo per le pressioni. */
export function pressureStatusColor(value: number): string {
  const [lo, hi] = COLD_PRESS_WINDOW;
  const m = COLD_PRESS_AMBER_MARGIN;
  if (value >= lo && value <= hi) return COLORS.ok;
  if (value >= lo - m && value <= hi + m) return COLORS.warn;
  return COLORS.accent;
}

export function isPressure(key: string): boolean {
  return key.startsWith("tire_press_");
}

/** Formatta il valore: interi senza decimali, altrimenti 1 decimale (step≥0.1) o 2. */
export function formatValue(p: Param, v: number): string {
  const decimals = Number.isInteger(p.step) ? 0 : p.step >= 0.1 ? 1 : 2;
  const num = v.toFixed(decimals);
  return p.unit ? `${num} ${p.unit}` : num;
}

// Layout dichiarativo dei gruppi per ogni sezione (titoli + colonne), come i
// _render_* della v1. `title: ""` = gruppo senza intestazione. `cols` = colonne desktop.
export type Group = { title: string; keys: string[]; cols: 1 | 2 | 4 };
export const SECTION_LAYOUT: Record<string, Group[]> = {
  tyres: [
    { title: "Pressioni", keys: ["tire_press_fl", "tire_press_fr", "tire_press_rl", "tire_press_rr"], cols: 2 },
    { title: "Camber", keys: ["camber_fl", "camber_fr", "camber_rl", "camber_rr"], cols: 2 },
    { title: "Toe", keys: ["toe_fl", "toe_fr", "toe_rl", "toe_rr"], cols: 2 },
    { title: "Caster", keys: ["caster"], cols: 1 },
  ],
  electronics: [{ title: "", keys: ["tc1", "tc2", "abs", "ecu_map", "brake_bias"], cols: 2 }],
  mechanical_grip: [
    { title: "Barre antirollio", keys: ["arb_front", "arb_rear"], cols: 2 },
    { title: "Wheel rate", keys: ["wheel_rate_front", "wheel_rate_rear"], cols: 2 },
    { title: "Bumpstop rate", keys: ["bumpstop_rate_front", "bumpstop_rate_rear"], cols: 2 },
    { title: "Bumpstop range", keys: ["bumpstop_range_front", "bumpstop_range_rear"], cols: 2 },
    { title: "Differenziale", keys: ["preload"], cols: 1 },
  ],
  dampers: [
    { title: "Anteriore Sinistra", keys: ["bump_fl", "fast_bump_fl", "rebound_fl", "fast_rebound_fl"], cols: 4 },
    { title: "Anteriore Destra", keys: ["bump_fr", "fast_bump_fr", "rebound_fr", "fast_rebound_fr"], cols: 4 },
    { title: "Posteriore Sinistra", keys: ["bump_rl", "fast_bump_rl", "rebound_rl", "fast_rebound_rl"], cols: 4 },
    { title: "Posteriore Destra", keys: ["bump_rr", "fast_bump_rr", "rebound_rr", "fast_rebound_rr"], cols: 4 },
  ],
  aero: [
    { title: "Ride height & deportanza", keys: ["ride_height_front", "ride_height_rear"], cols: 2 },
    { title: "Carico aerodinamico", keys: ["splitter", "wing"], cols: 2 },
    { title: "Brake ducts", keys: ["brake_duct_front", "brake_duct_rear"], cols: 2 },
  ],
};

// Fallback layout se una sezione non è mappata: un unico gruppo a 2 colonne.
export function groupsFor(sectionKey: string, section: Section): Group[] {
  return SECTION_LAYOUT[sectionKey] ?? [{ title: "", keys: Object.keys(section.params), cols: 2 }];
}
