// Logica pura della pagina Setup (Fase 5), portata dalla v1 (ui/setup_view.py):
// tipi della risposta /api/setup-params, layout dichiarativo dei gruppi per tab.
//
// L4 (16/09/2026): via la finestra delle pressioni «a freddo» (24.5–25.5, non
// pubblicata da Kunos) e i valori obiettivo fissi dello scenario demo. I parametri da
// toccare arrivano dal verdetto del motore (`Perdita.parametri`), con la variazione.
//
// #058 (30/09/2026): la pagina lavora in CLICK, come il file di ACC. Il valore che il
// gioco mostra (psi, °, N/m…) si calcola solo con la `regola` della vettura, che arriva
// dal backend (car_setup_ranges.json); senza regola resta il click. I min/max/default
// generici della risposta non si usano più: non erano della vettura.
import type { Perdita } from "@/lib/api";

type RegolaBase = {
  unita: string; // "" = il gioco mostra il numero senza unità
  fonti: string[];
  stato: "gioco" | "fonti";
  nota?: string;
};
export type Regola =
  | (RegolaBase & { tipo: "lineare"; base: number; passo: number; click_max: number | null })
  | (RegolaBase & { tipo: "elenco"; valori: number[] });

export type Param = {
  label: string;
  unit: string;
  tip?: string;
  regola: Regola | null; // null = vettura senza tabella o parametro da verificare
};
export type Section = { label: string; params: Record<string, Param> };
export type SetupParams = Record<string, Section>;

const decimali = (n: number) => (Number.isInteger(n) ? 0 : String(n).split(".")[1]?.length ?? 0);

/** Il click più alto che la regola conosce; null = nessun limite noto. */
export function clickMax(r: Regola | null): number | null {
  if (!r) return null;
  return r.tipo === "elenco" ? r.valori.length - 1 : r.click_max;
}

/** Il valore che il gioco mostra per quel click (come click_in_reale del backend), o null. */
export function reale(r: Regola | null, click: number): number | null {
  if (!r || !Number.isInteger(click) || click < 0) return null;
  if (r.tipo === "elenco") return click < r.valori.length ? r.valori[click] : null;
  if (r.click_max !== null && click > r.click_max) return null;
  const d = Math.max(decimali(r.base), decimali(r.passo));
  return Number((r.base + r.passo * click).toFixed(d));
}

/** Il valore del gioco formattato con i decimali della regola, es. «25.7 psi», «120000 N/m», «4». */
export function formatReale(r: Regola, v: number): string {
  const d = r.tipo === "lineare" ? Math.max(decimali(r.base), decimali(r.passo)) : 0;
  const num = v.toFixed(d);
  if (!r.unita) return num;
  return r.unita === "°" ? `${num}°` : `${num} ${r.unita}`;
}

/** Di quanti click spostarsi per una variazione nell'unità del gioco (es. +0.6 psi → +6). */
export function clickDaVariazione(r: Regola | null, click: number, variazione: number): number | null {
  if (!r) return null;
  if (r.tipo === "lineare") return Math.round(variazione / r.passo);
  const attuale = reale(r, click);
  if (attuale === null) return null;
  const obiettivo = attuale + variazione;
  let migliore = click;
  r.valori.forEach((v, i) => {
    if (Math.abs(v - obiettivo) < Math.abs(r.valori[migliore] - obiettivo)) migliore = i;
  });
  return migliore - click;
}

/** Un parametro che il verdetto chiede di toccare. */
export type Suggerimento = {
  key: string;
  variazione: number | null; // nell'unità del parametro; null = solo la direzione
  motivi: string[]; // titoli delle voci del verdetto che lo chiedono
};

/** I parametri citati dal verdetto, una voce per parametro (lo stesso può tornare in più voci). */
export function suggerimentiDalVerdetto(verdetto: Perdita[]): Suggerimento[] {
  const perChiave = new Map<string, Suggerimento>();
  for (const voce of verdetto) {
    for (const [key, variazione] of Object.entries(voce.parametri ?? {})) {
      const esistente = perChiave.get(key);
      if (esistente) {
        esistente.motivi.push(voce.titolo);
        // Il primo numero che arriva è quello della voce più grave: non si sommano.
        if (esistente.variazione === null) esistente.variazione = variazione;
      } else {
        perChiave.set(key, { key, variazione, motivi: [voce.titolo] });
      }
    }
  }
  return [...perChiave.values()];
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
