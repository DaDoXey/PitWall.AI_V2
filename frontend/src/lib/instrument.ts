// Token "strumento analogico da pit wall" (megaprompt #2, FASE 1).
// Riferimento di design/data-viz del progetto: vedi ../../docs/DESIGN_REFERENCE.md (MoTeC i2 Pro).
// Fonte UNICA da cui le viste dati (gauge, grafici, sparkline, heatmap, KPI)
// derivano la resa "strumento reale": niente glow di default, colore solo per
// STATO, grigi per griglia/assi/tacche, lancette/linee sottili, numeri monospace.
// Nessun colore nuovo: tutto viene dal design system (theme.ts).
import { COLORS } from "@/lib/theme";

// ── Colori di STATO (gli unici "vivi" ammessi sugli elementi dato) ──
// Il colore comunica uno stato, mai decorazione. `cold` per gomme/valori freddi.
export const STATE = {
  ok: COLORS.ok, // #00C853 — in finestra / nominale
  warn: COLORS.warn, // #FFB300 — al limite
  alarm: COLORS.accent, // #E8002D — fuori finestra / critico
  cold: COLORS.blue, // #3B82F6 — sotto temperatura/pressione di esercizio
  best: COLORS.best, // #C026D3 — giro più veloce / personal best (semantico, convenzione F1). USO ESCLUSIVO: mai decorativo.
} as const;

// ── Grigi strumento (griglia, assi, tacche, tracce) — riferimento di scala, non decoro ──
export const INSTRUMENT = {
  grid: COLORS.line, // #222 — hairline griglia di sfondo
  track: COLORS.lineStrong, // #333 — traccia/arco di fondo, assi
  tick: COLORS.muted, // #666 — tacche ed etichette attenuate
  ink: COLORS.subtle, // #999 — valori/testo secondari
} as const;

// ── Spessori (unità viewBox): hairline per i riferimenti, needle per l'elemento attivo ──
export const STROKE = {
  hairline: 1, // griglia, assi, tacche minori, soglie
  tick: 1.5, // tacche maggiori
  needle: 2, // lancetta / linea-dato attiva / marker
} as const;

// ── Glow / ombre: SPENTI di default sugli elementi dato ──
// Regola: nessun drop-shadow/glow di default. Il glow discreto è riservato al
// SOLO stato di allarme attivo (opzionale), mai come abbellimento permanente.
export const NO_GLOW = "none";
export const alarmGlow = `drop-shadow(0 0 2px ${COLORS.accent})`;

// ── Tipografia numerica: JetBrains Mono (classe Tailwind `font-mono`), nessun effetto testo ──
// Promemoria d'uso, non un valore: i numeri-strumento restano mono e piatti.
export const MONO_CLASS = "font-mono";
