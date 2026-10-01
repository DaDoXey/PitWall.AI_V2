// Logica pura della Engineer Console come radio del muretto (Entry #060): gli agganci
// alle altre sezioni, l'onda della radio, la «prima cosa da fare» detta in click, le
// risposte che il debrief sa dare da solo. Nessun calcolo di analisi: i numeri sono
// quelli del motore (analisi/debrief.py); qui solo come si dicono e dove portano.
import type { Debrief, FaseDebrief } from "@/lib/api";
import { clickDaVariazione, type SetupParams } from "@/lib/setup";

export type Collegamento = { etichetta: string; href: string };

const NOMI_RUOTE: Record<string, string> = {
  tire_press_fl: "Ant.SX",
  tire_press_fr: "Ant.DX",
  tire_press_rl: "Post.SX",
  tire_press_rr: "Post.DX",
};

/** Gli argomenti di una fase diventano link alle altre sezioni di PitWall. */
export function collegamenti(argomenti: string[]): Collegamento[] {
  const out: Collegamento[] = [];
  const aggiungi = (c: Collegamento) => {
    if (!out.some((x) => x.href === c.href)) out.push(c);
  };
  for (const a of argomenti) {
    if (a === "gomme") {
      aggiungi({ etichetta: "Gomme e freni", href: "/telemetry?tab=gomme" });
      aggiungi({ etichetta: "Lezione · finestra gomme", href: "/lezioni/gomme-finestra" });
    } else if (a.startsWith("curva:")) {
      aggiungi({ etichetta: "Le curve nei giri", href: "/telemetry?tab=curve" });
    } else if (a === "ritmo" || a.startsWith("settore:")) {
      aggiungi({ etichetta: "I giri", href: "/telemetry?tab=giri" });
    }
  }
  return out;
}

/** Altezze (0-1) delle barre di un'onda: sempre le stesse per lo stesso messaggio. */
export function barreOnda(seme: string, quante: number): number[] {
  let h = 2166136261;
  for (const c of seme) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  const barre: number[] = [];
  for (let i = 0; i < quante; i++) {
    h = Math.imul(h ^ (h >>> 15), 2246822507) >>> 0;
    const caso = (h % 1000) / 1000;
    const inviluppo = Math.pow(Math.sin((Math.PI * (i + 0.5)) / quante), 0.6);
    barre.push(Math.max(0.12, inviluppo * (0.35 + 0.65 * caso)));
  }
  return barre;
}

/**
 * La prima cosa da fare, detta come la direbbe Gigi. Con la tabella della vettura le
 * pressioni diventano click («Post.SX +6 · Post.DX +8 click»), altrimenti restano psi.
 */
export function titoloPrimaCosa(prima: NonNullable<Debrief["prima_cosa"]>, params: SetupParams | null): string {
  const voci = Object.entries(prima.parametri).filter(([, v]) => v !== null) as [string, number][];
  const pressioni = voci.filter(([k]) => k in NOMI_RUOTE);
  if (pressioni.length && pressioni.length === voci.length) {
    const verbo = pressioni.every(([, v]) => v > 0) ? "Alza" : pressioni.every(([, v]) => v < 0) ? "Abbassa" : "Correggi";
    const regola = (k: string) => {
      for (const sez of Object.values(params ?? {})) if (sez.params[k]) return sez.params[k].regola;
      return null;
    };
    const inClick = pressioni.map(([k, v]) => {
      const passi = clickDaVariazione(regola(k), 0, v);
      return passi === null ? null : `${NOMI_RUOTE[k]} ${passi > 0 ? "+" : ""}${passi}`;
    });
    if (inClick.every((x) => x !== null)) return `${verbo} le pressioni: ${inClick.join(" · ")} click`;
    return `${verbo} le pressioni a freddo: ${pressioni.map(([k, v]) => `${NOMI_RUOTE[k]} ${v > 0 ? "+" : ""}${v} psi`).join(" · ")}`;
  }
  // Senza parametri: la prima frase dell'azione, fino ai due punti o al punto.
  const frase = prima.azione.split(/[:.](\s|$)/)[0].trim();
  return frase || prima.titolo;
}

export type Messaggio = {
  id: string;
  da: "gigi" | "tu";
  testo: string;
  prova?: string;
  fase?: number; // indice della fase di cui parla (per «in onda»)
  collegamenti?: Collegamento[];
  dalVivo?: boolean; // scambio con il modello (#061): gli altri vengono dal debrief
  errore?: boolean; // la chat non ha risposto: non conta e non torna al modello
};

/** Le domande che il pilota può scrivere a Gigi dal vivo in una conversazione (come il backend). */
export const MAX_DOMANDE_DAL_VIVO = 12;

/** La radio all'apertura: un messaggio di Gigi per ogni fase. */
export function messaggiIniziali(d: Debrief): Messaggio[] {
  return d.fasi.map((f, i) => ({
    id: `fase-${i}-${f.giri.join("-")}`,
    da: "gigi",
    testo: f.messaggio,
    prova: f.prova,
    fase: i,
    collegamenti: collegamenti(f.argomenti),
  }));
}

export type Domanda = "perche" | "dove" | "gomme" | "giro";

export const DOMANDE: { id: Domanda; testo: string }[] = [
  { id: "perche", testo: "Perché?" },
  { id: "dove", testo: "Dove perdo?" },
  { id: "gomme", testo: "E le gomme?" },
  { id: "giro", testo: "Il giro migliore?" },
];

const s = (ms: number) => `${(Math.floor(ms / 10 + 0.5) / 100).toFixed(2)} s`;

/**
 * Le risposte che il debrief sa dare senza modello: dai dati delle fasi, mai inventate.
 * Restituisce anche la fase di cui parla, così la striscia e la mappa la seguono.
 */
export function rispondi(d: Debrief, domanda: Domanda, faseAttiva: number): { testo: string; prova?: string; fase?: number } {
  const fase: FaseDebrief | undefined = d.fasi[faseAttiva];
  if (domanda === "perche") {
    if (!fase) return { testo: "Non ho una fase da spiegarti: questa sessione non ha giri di ritmo." };
    return { testo: `I numeri di questa fase, uno per uno:`, prova: fase.prova, fase: faseAttiva };
  }
  if (domanda === "giro") {
    const i = d.fasi.findIndex((f) => f.tipo === "giro");
    if (i < 0) return { testo: "Non c'è un giro migliore da raccontare in questa sessione." };
    return { testo: d.fasi[i].messaggio, prova: d.fasi[i].prova, fase: i };
  }
  if (domanda === "dove") {
    let migliore: { fase: number; nome: string; ms: number } | null = null;
    d.fasi.forEach((f, i) =>
      f.punti.forEach((p) => {
        if (!migliore || p.perdita_ms > migliore.ms) migliore = { fase: i, nome: p.nome ?? `curva ${p.curva}`, ms: p.perdita_ms };
      }),
    );
    if (!migliore) {
      return { testo: "Senza la telemetria non vedo le curve: ti so dire solo i tempi, e sono nelle fasi qui sopra." };
    }
    const m = migliore as { fase: number; nome: string; ms: number };
    return { testo: `In ${m.nome}: ${s(m.ms)} a giro, nella fase «${d.fasi[m.fase].nome}».`, fase: m.fase };
  }
  // gomme
  const conGomme = d.fasi.map((f, i) => ({ f, i })).filter(({ f }) => f.argomenti.includes("gomme"));
  if (conGomme.length) {
    const { f, i } = conGomme[0];
    const frase = f.messaggio.split(". ").find((x) => /finestra|°C/.test(x));
    return { testo: frase ? frase.replace(/\.$/, "") + "." : f.messaggio, fase: i };
  }
  if (d.fasi.some((f) => f.stato_gomme)) return { testo: "Le gomme stanno nella finestra per tutta la sessione: da lì non arriva niente." };
  return { testo: "Senza la telemetria non vedo le gomme: pressioni e temperature arrivano con i canali." };
}

/** Il taglio fra due giri: c'è → si toglie, non c'è → si mette. */
export function alternaTaglio(tagli: number[], giro: number): number[] {
  return tagli.includes(giro) ? tagli.filter((t) => t !== giro) : [...tagli, giro].sort((a, b) => a - b);
}
