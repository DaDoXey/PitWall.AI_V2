"use client";

// Indice degli asset scaricati (public/assets/manifest.json, generato da
// backend/scripts/fetch_assets.py) e ritagli scelti a mano (crops.json).
//
// Perché sta qui e non dentro un componente: dal 18/09 il manifest serve a due
// posti — le card di SessionBriefing e la sezione Tracciati — e due copie
// vorrebbero dire due fetch e due cache che possono divergere. La promessa del
// modulo è semplice: il file si scarica **una volta sola** per sessione di
// pagina e chi arriva dopo trova la stessa risposta.
//
// La copertura è parziale e l'estensione varia (jpg/png/svg): senza indice la
// UI dovrebbe tentare una URL e gestire il 404. Se il manifest manca, le
// immagini semplicemente non compaiono — nessuna pagina si rompe.
//
// Nota sulle mappe: nel manifest ci sono SOLO i layout verificati a occhio.
// Gli altri sono stati tolti dal repo apposta (regola «meglio nessuna mappa
// che una sbagliata»), quindi qui non può comparire un layout non approvato.
import { useEffect, useState } from "react";

export type Manifest = {
  cars: Record<string, Record<string, string>>;
  tracks: Record<string, Record<string, string>>;
};

let manifestPromise: Promise<Manifest | null> | null = null;

export function loadManifest(): Promise<Manifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch("/assets/manifest.json")
      .then((r) => (r.ok ? (r.json() as Promise<Manifest>) : null))
      .catch(() => null);
  }
  return manifestPromise;
}

/** Gli asset di una entità ({photo, map, ...}); {} finché il manifest non c'è. */
export function useAssets(kind: "cars" | "tracks", id: string | undefined) {
  const [assets, setAssets] = useState<Record<string, string>>({});
  useEffect(() => {
    if (!id) return;
    let alive = true;
    loadManifest().then((m) => {
      if (alive && m) setAssets(m[kind]?.[id] ?? {});
    });
    return () => {
      alive = false;
    };
  }, [kind, id]);
  return assets;
}

/** Gli asset di TUTTE le entità di un tipo: per le liste, che altrimenti
 *  monterebbero un hook per riga. */
export function useAssetsIndex(kind: "cars" | "tracks") {
  const [index, setIndex] = useState<Record<string, Record<string, string>>>({});
  useEffect(() => {
    let alive = true;
    loadManifest().then((m) => {
      if (alive && m) setIndex(m[kind] ?? {});
    });
    return () => {
      alive = false;
    };
  }, [kind]);
  return index;
}

// Ritagli scelti a mano (public/assets/crops.json, export del tool generato da
// backend/scripts/build_crop_tool.py). Ogni voce dice come piazzare l'immagine
// dentro la banda, in percentuali del riquadro; `band` ne fissa il rapporto.
// Se il file manca si va di ritaglio centrato: la UI non dipende dal tool.
export type Crop = { w: number; h: number; l: number; t: number };
export type Band = { w: number; h: number };
export type Crops = { band: Band; items: Record<string, Crop> };

export const BANDA_PREDEFINITA: Band = { w: 540, h: 128 };

let cropsPromise: Promise<Crops | null> | null = null;

export function loadCrops(): Promise<Crops | null> {
  if (!cropsPromise) {
    cropsPromise = fetch("/assets/crops.json")
      .then((r) => (r.ok ? (r.json() as Promise<Crops>) : null))
      .catch(() => null);
  }
  return cropsPromise;
}

export function useCrop(id: string | undefined) {
  const [crops, setCrops] = useState<Crops | null>(null);
  useEffect(() => {
    let alive = true;
    loadCrops().then((c) => alive && setCrops(c));
    return () => {
      alive = false;
    };
  }, []);
  return {
    crop: id && crops ? crops.items?.[id] : undefined,
    band: crops?.band ?? BANDA_PREDEFINITA,
  };
}
