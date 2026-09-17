// Formattazione dei numeri del report: SOLO presentazione.
// Regola di L4 (decisione 2 del 16/09/2026): i conti li fa il motore di analisi nel
// backend. Qui si cambia l'unità di visualizzazione (ms → m:ss.mmm) e si sceglie
// un'etichetta, mai si ricava una grandezza nuova.
import type { Fonte, Piattaforma, Riassunto, Ruota } from "@/lib/api";
import { COLORS } from "@/lib/theme";

/** 107820 → "1:47.820". */
export function tempoGiro(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  const minuti = Math.floor(ms / 60000);
  const resto = ms - minuti * 60000;
  return `${minuti}:${(resto / 1000).toFixed(3).padStart(6, "0")}`;
}

/** 33070 → "33.070 s". */
export function secondi(ms: number | null | undefined, cifre = 3): string {
  if (ms === null || ms === undefined) return "—";
  return `${(ms / 1000).toFixed(cifre)} s`;
}

/** 352 → "+0.352 s" (con segno, per i delta). */
export function delta(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  const segno = ms > 0 ? "+" : ms < 0 ? "−" : "±";
  return `${segno}${(Math.abs(ms) / 1000).toFixed(3)} s`;
}

export function numero(v: number | null | undefined, cifre = 1, unita = ""): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${v.toFixed(cifre)}${unita ? ` ${unita}` : ""}`;
}

export function data(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return "";
  }
}

export const RUOTE: { key: Ruota; label: string; colore: string }[] = [
  { key: "FL", label: "Ant.SX", colore: COLORS.blue },
  { key: "FR", label: "Ant.DX", colore: COLORS.ok },
  { key: "RL", label: "Post.SX", colore: COLORS.warn },
  { key: "RR", label: "Post.DX", colore: COLORS.accent },
];

export const ETICHETTA_TIPO: Record<string, string> = {
  FP: "Prove",
  Q: "Qualifica",
  R: "Gara",
  HL: "Hotlap",
  HS: "Hotstint",
  "?": "Sessione",
};

export const ETICHETTA_PIATTAFORMA: Record<Piattaforma, string> = {
  pc: "PC",
  playstation: "PlayStation",
  xbox: "Xbox",
};

/** Da dove arriva la sessione, in una parola. */
export function etichettaFonte(fonte: Fonte, piattaforma?: Piattaforma | null): string {
  switch (fonte) {
    case "demo":
      return "Demo";
    case "acc_shm":
      return "Telemetria";
    case "acc_results":
      return "Risultati ACC";
    case "acc_setup":
      return "Setup ACC";
    case "motec":
      return "MoTeC";
    case "manuale":
      return piattaforma && piattaforma !== "pc" ? ETICHETTA_PIATTAFORMA[piattaforma] : "Manuale";
  }
}

/** «1 giro», «3 giri»: con i riferimenti MoTeC a giro singolo «1 giri» si vedeva ovunque. */
export function giri(n: number | null | undefined, aggettivo = ""): string {
  const quanti = n ?? 0;
  const parola = quanti === 1 ? "giro" : "giri";
  return `${quanti} ${parola}${aggettivo ? ` ${quanti === 1 ? aggettivo.replace(/i$/, "e") : aggettivo}` : ""}`;
}

/** Da dove viene il consumo: accanto al numero, sempre (L5). */
export const ETICHETTA_FONTE_CARBURANTE: Record<"misurato" | "manuale" | "setup", string> = {
  misurato: "misurato",
  manuale: "inserito da te",
  setup: "dal setup",
};

/** Nome leggibile di uno slug quando il catalogo non lo conosce: «bmw_m4_gt3» → «bmw m4 gt3». */
export function slugLeggibile(slug: string | null | undefined): string {
  return slug ? slug.replace(/_/g, " ") : "—";
}

export function titoloSessione(s: Pick<Riassunto, "track" | "car">, nomi: NomiCatalogo): string {
  return `${nomi.pista(s.track)} · ${nomi.vettura(s.car)}`;
}

export type NomiCatalogo = {
  vettura: (slug: string | null | undefined) => string;
  pista: (slug: string | null | undefined) => string;
};
