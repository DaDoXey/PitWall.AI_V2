// Client API verso il backend FastAPI. La base URL viene dall'env pubblico
// (in dev: http://localhost:8000). La ANTHROPIC_API_KEY NON è mai qui: sta solo lato server.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJSON(path: string) {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

export function getSession() {
  return getJSON("/api/session");
}

// ── Catalogo ACC (Lotto 1): anagrafica vetture e circuiti servita dal backend
// (core/catalog.py). Sostituisce le liste hardcoded di lib/catalog.ts, che
// restano come fallback se il backend non risponde.
export type CatalogCar = {
  id: string;
  display_name: string;
  brand: string;
  model: string;
  year: number;
  category: string;
  dlc: boolean;
  dlc_pack: string | null;
};

export type CatalogTrack = {
  id: string;
  name: string;
  /** Etichetta breve per la UI ("Monza"), il nome ufficiale è in `name`. */
  short_name: string;
  nick: string | null;
  country: string;
  length_km: number | null;
  corners: number | null;
  downforce_level: string | null;
  dlc: boolean;
  dlc_pack: string | null;
};

export type Catalog = {
  cars: CatalogCar[];
  tracks: CatalogTrack[];
  counts: { cars: number; tracks: number; by_category: Record<string, number> };
};

export function getCatalog() {
  return getJSON("/api/catalog") as Promise<Catalog>;
}

export function getSetupParams(car?: string, track?: string) {
  const q = new URLSearchParams();
  if (car) q.set("car", car);
  if (track) q.set("track", track);
  return getJSON(`/api/setup-params?${q.toString()}`);
}

// `profile` (opzionale): riga "Profilo pilota: …" dal wizard (megaprompt #9,
// FASE 5). Viaggia in un campo separato dal prompt: il routing keyword della
// demo-cache lato server deve vedere solo le parole dell'utente.
export async function postAnalysis(prompt: string, profile?: string) {
  const res = await fetch(`${API_BASE}/api/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile ? { prompt, profile } : { prompt }),
  });
  if (!res.ok) throw new Error(`POST /api/analysis → ${res.status}`);
  return res.json() as Promise<{ question: string; text: string; source: string }>;
}

// Errore con lo status HTTP, così la UI può distinguere 400 (CSV non valido)
// da 503 (screenshot senza chiave server) e mostrare il messaggio giusto.
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function postFile(path: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      detail = (await res.json())?.detail ?? detail;
    } catch {
      /* corpo non-JSON: tieni lo status */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json();
}

export type CsvResult = {
  laps_count: number;
  fuel_cons_avg: number;
  has_pressure_data: boolean;
  has_temp_data: boolean;
  warnings: string[];
  validation_errors: string[];
};

export function postCsvParse(file: File) {
  return postFile("/api/csv/parse", file) as Promise<CsvResult>;
}

export type VisionResult = { params: Record<string, number>; summary: string };

export function postSetupFromImage(file: File) {
  return postFile("/api/setup/from-image", file) as Promise<VisionResult>;
}
