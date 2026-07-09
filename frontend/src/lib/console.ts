// Logica pura della Engineer Console (Gigi), portata dalla v1 (ui/console.py):
// parsing robusto dell'output a 4 sezioni + chip scenari + etichette sorgente.
// Nessuna dipendenza da React: testabile e riusabile.

export type Section = { title: string; icon: string; body: string };

// (titolo canonico, regex header tollerante, icona). Ordine = ordine card.
// La 3ª (Correzione Setup) è resa come "SCHEDA SETUP" evidenziata.
const SECTIONS: { title: string; icon: string; pattern: RegExp }[] = [
  { title: "Diagnosi", icon: "🔍", pattern: /##\s*Diagnosi/i },
  { title: "Causa Meccanica Probabile", icon: "⚙", pattern: /##\s*Causa\s+Meccanica/i },
  { title: "Correzione Setup Consigliata", icon: "🔧", pattern: /##\s*Correzione\s+Setup/i },
  { title: "Note Aggiuntive", icon: "📋", pattern: /##\s*Note\s+Aggiuntive/i },
];

// Indice della card resa come "SCHEDA SETUP" (evidenziata).
export const SETUP_SECTION_INDEX = 2;

/**
 * Ritorna le 4 sezioni canoniche in ordine. Se una sezione manca, il suo
 * `body` è "" → la card degrada con grazia (mai errore), come nella v1.
 */
export function parseSections(text: string): Section[] {
  const src = text ?? "";
  // (posizione match, indice sezione) per le sezioni effettivamente presenti.
  const found: { start: number; i: number; headerEnd: number }[] = [];
  SECTIONS.forEach((s, i) => {
    const m = s.pattern.exec(src);
    if (m) {
      const nl = src.indexOf("\n", m.index);
      found.push({ start: m.index, i, headerEnd: nl === -1 ? src.length : nl + 1 });
    }
  });
  found.sort((a, b) => a.start - b.start);

  const bodies: Record<number, string> = {};
  found.forEach((f, idx) => {
    const nextStart = idx + 1 < found.length ? found[idx + 1].start : src.length;
    bodies[f.i] = src.slice(f.headerEnd, nextStart).trim();
  });

  return SECTIONS.map((s, i) => ({ title: s.title, icon: s.icon, body: bodies[i] ?? "" }));
}

// Chip scenari rapidi (prompt preset) — come da brief v1.
export const CHIPS = ["Sottosterzo", "Calcola carburante", "Analizza gomme", "Bilanciamento freni"];

// Etichetta leggibile della sorgente restituita dal backend.
export const SOURCE_LABELS: Record<string, string> = {
  demo: "demo-mode",
  cache: "cache",
  api: "live",
  fallback: "fallback offline",
};

// Prompt/risposta demo canonici: stato iniziale della console (mai vuota).
export const DEMO_QUESTION = "L'auto scivola dietro in accelerazione";
