// Consigli di Gigi per la Sidebar (megaprompt #5, FASE 4).
// Nota onesta: NON esiste uno storico temporale dei consigli lato server. La fonte
// reale sono i `suggested_params` della sessione (i parametri che l'analisi di Gigi
// ha evidenziato in rosso nel Setup). Qui li rendo leggibili e li ordino per lettura;
// sono la fotografia dell'ultima analisi, non una cronologia.
import type { SessionData } from "@/lib/telemetry";

export interface Advice {
  key: string;
  label: string;
  group: string;
}

// Posizioni gomma coerenti con TYRE_LABELS (Ant./Post. · SX/DX).
const TYRE_POS: Record<string, string> = {
  fl: "Ant.SX",
  fr: "Ant.DX",
  rl: "Post.SX",
  rr: "Post.DX",
};

// Etichette esplicite per le chiavi note; fallback che "prettifica" la chiave.
const KNOWN: Record<string, { label: string; group: string }> = {
  preload: { label: "Precarico differenziale", group: "Differenziale" },
};

function describe(key: string): { label: string; group: string } {
  if (key.startsWith("tire_press_")) {
    const pos = key.slice("tire_press_".length);
    return { label: `Pressione ${TYRE_POS[pos] ?? pos.toUpperCase()}`, group: "Pressioni" };
  }
  if (KNOWN[key]) return KNOWN[key];
  const pretty = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return { label: pretty, group: "Setup" };
}

// Ordine di PRESENTAZIONE (non una priorità di dominio inventata): le pressioni —
// causa tipica nella storia demo — prima del resto, per una lettura coerente.
const GROUP_RANK: Record<string, number> = { Pressioni: 0, Differenziale: 1, Setup: 2 };

export function buildAdvice(d: SessionData): Advice[] {
  const params = d.suggested_params ?? [];
  return params
    .map((k) => ({ key: k, ...describe(k) }))
    .sort((a, b) => (GROUP_RANK[a.group] ?? 9) - (GROUP_RANK[b.group] ?? 9));
}
