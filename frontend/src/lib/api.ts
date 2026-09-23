// Client API verso il backend FastAPI. La base URL viene dall'env pubblico
// (in dev: http://localhost:8000). La ANTHROPIC_API_KEY NON è mai qui: sta solo lato server.
//
// L4 del rework dati (16/09/2026): le schermate non leggono più numeri scritti a mano
// (`/api/session` è sparito). Leggono l'archivio delle sessioni e il REPORT del motore
// di analisi: ogni cifra a schermo è una cifra calcolata e dimostrata dal backend, e
// il frontend la mostra senza rifare conti.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Errore con lo status HTTP, così la UI può distinguere 400/404/409/503 e mostrare il
// messaggio giusto (il `detail` del backend è già scritto per il pilota).
export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

async function leggiErrore(res: Response): Promise<ApiError> {
  let detail: unknown = undefined;
  let messaggio = `${res.status}`;
  try {
    detail = (await res.json())?.detail;
    if (typeof detail === "string") messaggio = detail;
    else if (detail && typeof detail === "object" && "messaggio" in detail)
      messaggio = String((detail as { messaggio: string }).messaggio);
  } catch {
    /* corpo non-JSON: resta lo status */
  }
  return new ApiError(res.status, messaggio, detail);
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw await leggiErrore(res);
  return res.json() as Promise<T>;
}

async function sendJSON<T>(path: string, method: "POST" | "DELETE", body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw await leggiErrore(res);
  return res.json() as Promise<T>;
}

async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
  if (!res.ok) throw await leggiErrore(res);
  return res.json() as Promise<T>;
}

// ─────────────────────────────────────────────
// Salute del backend
// ─────────────────────────────────────────────
export type Health = {
  status: string;
  demo_mode: boolean;
  live_allowed: boolean;
  recorder_allowed: boolean;
};

export function getHealth() {
  return getJSON<Health>("/");
}

// ─────────────────────────────────────────────
// Archivio delle sessioni
// ─────────────────────────────────────────────
export type Fonte = "acc_results" | "acc_setup" | "acc_shm" | "motec" | "demo" | "manuale";
export type Piattaforma = "pc" | "playstation" | "xbox";
export type Mescola = "asciutto" | "bagnato";

export type Riassunto = {
  id: string;
  fonte: Fonte;
  car: string | null;
  car_model_id: number | null;
  track: string | null;
  tipo_sessione: string;
  pilota: string | null;
  giri: number;
  giri_validi: number;
  miglior_giro_ms: number | null;
  ha_setup: boolean;
  parametri_setup: number;
  assunzioni: number;
  importato_il: string | null;
  iniziata_il: string | null;
  mescola: Mescola | null;
  piattaforma: Piattaforma | null;
  ha_canali: boolean;
  ha_racconto: boolean;
  demo: boolean;
  // L5: sessione di un altro pilota (es. un giro MoTeC scaricato), e giro ritagliato a mano
  // in MoTeC i2 (inizio incerto: confronto curva per curva meno preciso).
  riferimento: boolean;
  ritaglio_i2: boolean;
};

export function getSessioni() {
  return getJSON<{ sessioni: Riassunto[]; demo_id: string }>("/api/sessions?limite=200");
}

/** Lo zip .ld + .ldx della sessione, per MoTeC i2 (L5): un link da scaricare, non un fetch. */
export function urlEsportaMotec(id: string) {
  return `${API_BASE}/api/sessions/${encodeURIComponent(id)}/export/motec`;
}

export function cancellaSessione(id: string) {
  return sendJSON<{ cancellata: string }>(`/api/sessions/${encodeURIComponent(id)}`, "DELETE");
}

// ─────────────────────────────────────────────
// Report del motore di analisi
// ─────────────────────────────────────────────
export type PerRuota = { FL: number | null; FR: number | null; RL: number | null; RR: number | null };
export type Ruota = keyof PerRuota;

export type Perdita = {
  titolo: string;
  decimi: number | null;
  prova: string;
  azione: string;
  gravita: number;
  categoria: "tempo" | "gomme";
  fonte: "misura" | "kunos";
  parametri: Record<string, number | null>;
};

export type PuntoFermo = { titolo: string; prova: string };

export type GiroReport = {
  numero: number;
  tempo_ms: number | null;
  splits_ms: number[];
  valido: boolean;
  di_ritmo: boolean;
  migliore: boolean;
  delta_migliore_ms: number | null;
  carburante_usato_l: number | null;
  in_pit: boolean;
};

export type Ritmo = {
  giri_validi: number;
  miglior_giro_ms: number | null;
  miglior_giro_numero: number | null;
  giro_teorico_ms: number | null;
  lasciato_sul_tavolo_ms: number | null;
  giri_per_teorico: number;
  motivo_teorico: string | null;
  media_ms: number | null;
  mediana_ms: number | null;
  media_migliori_3_ms: number | null;
};

export type Settore = {
  numero: number;
  migliore_ms: number;
  media_ms: number;
  deviazione_ms: number;
  perdita_media_ms: number;
  perdita_sul_giro_migliore_ms: number | null;
};

export type Costanza = {
  deviazione_ms: number | null;
  coefficiente_variazione: number | null;
  scarto_max_ms: number | null;
  giri_entro_mezzo_secondo: number;
  percentuale_entro_mezzo_secondo: number | null;
  giudizio: string | null;
};

export type Degrado = {
  calcolabile: boolean;
  pendenza_ms_giro: number | null;
  r_quadro: number | null;
  giri_considerati: number;
  dal_giro: number | null;
  perdita_su_10_giri_ms: number | null;
  motivo: string | null;
  significativo: boolean;
};

export type Carburante = {
  calcolabile: boolean;
  consumo_medio_l_giro: number | null;
  giri_misurati: number;
  motivo: string | null;
  // Da dove viene il consumo (L5): il numero non si mostra mai senza.
  fonte: "misurato" | "manuale" | "setup" | null;
};

export type Curva = {
  numero: number;
  ingresso: number;
  apice: number;
  uscita: number;
  velocita_minima_riferimento: number;
  ingresso_m: number | null;
  apice_m: number | null;
  uscita_m: number | null;
};

export type RiepilogoCurva = {
  curva: number;
  tempo_migliore_ms: number;
  tempo_medio_ms: number;
  perdita_media_ms: number;
  perdita_totale_ms: number;
  dispersione_frenata: number | null;
  dispersione_vmin: number;
  velocita_minima_migliore: number;
  velocita_minima_media: number;
  giri_considerati: number;
};

export type ReportCurve = {
  curve: Curva[];
  riepilogo: RiepilogoCurva[];
  giro_di_riferimento: number | null;
  perdita_totale_ms: number;
  lunghezza_stimata_m: number | null;
  dati_mancanti: string[];
};

export type Finestra = {
  grandezza: "pressione" | "temperatura_core";
  min: number;
  max: number;
  unita: string;
  fonte: string;
  sotto_pct: PerRuota;
  dentro_pct: PerRuota;
  sopra_pct: PerRuota;
  ruote_fuori: Ruota[];
};

export type Gomme = {
  pressione_media: PerRuota;
  pressione_minima: PerRuota;
  pressione_massima: PerRuota;
  temperatura_media: PerRuota;
  temperatura_massima: PerRuota;
  // Solo file MoTeC: TYRE_TAIR, non dichiarata come temperatura al core → mai giudicata.
  temperatura_motec_media?: PerRuota | null;
  temperatura_motec_massima?: PerRuota | null;
  nota_temperatura_motec?: string | null;
  mescola: Mescola | null;
  squilibrio_ant_post_psi: number | null;
  squilibrio_sx_dx_psi: number | null;
  squilibrio_temp_ant_post_c: number | null;
  squilibrio_temp_sx_dx_c: number | null;
  pendenza_pressione_psi_giro: number | null;
  misurato_su_giri: number;
  finestra_pressione: Finestra | null;
  finestra_temperatura: Finestra | null;
  nota_assi: string;
  nota_finestra: string;
};

export type RiferimentoCommunityFreni = {
  stato: string;
  etichetta: string;
  anteriori_max_c: number;
  anteriori_picco_c: number;
  posteriori_max_c: number;
  posteriori_picco_c: number;
  fonte: string;
  limiti: string;
};

export type Freni = {
  temperatura_media: PerRuota;
  temperatura_massima: PerRuota;
  squilibrio_ant_post_c: number | null;
  pastiglie_consumate_mm: PerRuota | null;
  dischi_consumati_mm: PerRuota | null;
  riferimento_community: RiferimentoCommunityFreni | null;
};

export type GiroGomme = { giro: number; pressione: PerRuota; temperatura: PerRuota; freni_max: PerRuota };

export type GommeEFreni = {
  gomme: Gomme | null;
  freni: Freni | null;
  per_giro: GiroGomme[];
  dati_mancanti: string[];
};

export type Report = {
  car: string | null;
  car_model_id: number | null;
  track: string | null;
  tipo_sessione: string;
  fonte: Fonte;
  mescola: Mescola | null;
  giri_totali: number;
  giri_buttati: number;
  giri_di_ritmo: number;
  giri_esclusi_dal_ritmo: number;
  giri: GiroReport[];
  ritmo: Ritmo;
  settori: Settore[];
  costanza: Costanza;
  degrado: Degrado;
  carburante: Carburante;
  verdetto: Perdita[];
  cosa_regge: PuntoFermo[];
  dati_mancanti: string[];
  ha_setup: boolean;
  ha_racconto: boolean;
  curve: ReportCurve | null;
  gomme_e_freni: GommeEFreni | null;
  ha_canali: boolean;
};

export function getAnalisi(id: string) {
  return getJSON<Report>(`/api/sessions/${encodeURIComponent(id)}/analisi`);
}

// Il bundle intero: serve solo dove si mostra ciò che il report non porta (il setup
// grezzo della sessione, le condizioni, il racconto).
export type ValoreSetup = { raw: number | number[]; reale: number | null; unita: string; verificato: boolean };
export type Racconto = {
  andamento?: string | null;
  frenata?: string | null;
  ingresso?: string | null;
  centro?: string | null;
  uscita?: string | null;
  gomme?: string | null;
  curve_critiche?: string[];
  note?: string | null;
};
export type Bundle = {
  schema_version: string;
  meta: {
    fonte: Fonte;
    car: string | null;
    track: string | null;
    pilota: string | null;
    tipo_sessione: string;
    iniziata_il: string | null;
    importato_il: string | null;
    durata_s: number | null;
    mescola: Mescola | null;
    piattaforma: Piattaforma | null;
    riferimento?: boolean;
    ritaglio_i2?: boolean;
    condizioni: {
      temp_aria_c: number | null;
      temp_pista_c: number | null;
      grip_linea_ideale: number | null;
      pioggia: number | null;
      pista_bagnata: boolean | null;
    };
  };
  setup: { nome: string | null; valori: Record<string, ValoreSetup>; assunzioni: string[] } | null;
  racconto: Racconto | null;
  giri: { numero: number; tempo_ms: number | null; valido: boolean; in_pit: boolean }[];
  assunzioni: string[];
};

export function getBundle(id: string) {
  return getJSON<Bundle>(`/api/sessions/${encodeURIComponent(id)}`);
}

export type Tracce = {
  id: string;
  punti: number;
  posizione: number[];
  metri: number[] | null;
  lunghezza_stimata_m: number | null;
  giri: { giro: number; tempo_ms: number | null; canali: Record<string, number[]> }[];
};

export function getTracce(id: string, giri: number[], canali: string[], punti = 800) {
  const q = new URLSearchParams({ giri: giri.join(","), canali: canali.join(","), punti: String(punti) });
  return getJSON<Tracce>(`/api/sessions/${encodeURIComponent(id)}/tracce?${q.toString()}`);
}

// ─────────────────────────────────────────────
// Soglie di riferimento (Kunos e community, separate)
// ─────────────────────────────────────────────
export type VoceRiferimento = {
  min?: number;
  max?: number;
  unita?: string | null;
  citazione?: string;
  si_applica_a?: string;
  nota?: string;
  stato?: string;
};

export type Riferimenti = {
  ufficiali: {
    fonte: { titolo: string; editore: string; pubblicato_il: string; versione_acc: string; url_thread_ufficiale: string };
    voci: Record<string, VoceRiferimento>;
  };
  community: { regola: string; voci: Record<string, VoceRiferimento & { fonti?: { nome: string; url: string }[] }> };
};

export function getRiferimenti() {
  return getJSON<Riferimenti>("/api/riferimenti/fisica");
}

// ─────────────────────────────────────────────
// Import (PC) e sessione manuale (console)
// ─────────────────────────────────────────────
export type Partecipante = {
  car_id: number;
  numero: number | null;
  car_model: number | null;
  pilota: string | null;
  player_id: string | null;
  giri: number;
};

export function importaSetup(file: File, track?: string) {
  const form = new FormData();
  form.append("file", file);
  if (track) form.append("track", track);
  return postForm<{ id: string; assunzioni: string[] }>("/api/sessions/import/setup", form);
}

export function importaRisultati(file: File, carId?: number) {
  const form = new FormData();
  form.append("file", file);
  if (carId !== undefined) form.append("car_id", String(carId));
  return postForm<{ id: string; assunzioni: string[] }>("/api/sessions/import/results", form);
}

// Export MoTeC di ACC (L5): .ld obbligatorio, .ldx per i giri, setup e litri facoltativi.
export type ImportMotec = {
  ld: File;
  ldx?: File | null;
  setup?: File | null;
  carburanteInizioL?: number | null;
  carburanteFineL?: number | null;
  mescola?: Mescola | null;
  riferimento: boolean;
};

export function importaMotec(dati: ImportMotec) {
  const form = new FormData();
  form.append("ld", dati.ld);
  if (dati.ldx) form.append("ldx", dati.ldx);
  if (dati.setup) form.append("setup", dati.setup);
  if (dati.carburanteInizioL != null && dati.carburanteFineL != null) {
    form.append("carburante_inizio_l", String(dati.carburanteInizioL));
    form.append("carburante_fine_l", String(dati.carburanteFineL));
  }
  if (dati.mescola) form.append("mescola", dati.mescola);
  form.append("riferimento", dati.riferimento ? "true" : "false");
  return postForm<{ id: string; giri: number; giri_con_tempo: number; assunzioni: string[] }>(
    "/api/sessions/import/motec",
    form,
  );
}

export type SessioneManuale = {
  piattaforma: Piattaforma;
  car?: string | null;
  track?: string | null;
  tipo_sessione?: string;
  mescola?: Mescola | null;
  temp_aria_c?: number | null;
  temp_pista_c?: number | null;
  giri?: { numero: number; tempo_ms: number | null; valido?: boolean }[];
  setup?: Record<string, number>;
  racconto?: Racconto | null;
};

export function creaSessioneManuale(body: SessioneManuale) {
  return sendJSON<{ id: string }>("/api/sessions/manuale", "POST", body);
}

// Registratore della shared memory (solo PC, backend locale).
export type StatoRegistratore = {
  abilitato: boolean;
  agganciato: boolean;
  in_registrazione: boolean;
  frequenza_hz: number;
  colonne: number;
  sessione: { id: string; vettura: string | null; pista: string | null; campioni: number } | null;
};

export type Registrazione = {
  id: string;
  inizio: string | null;
  fine: string | null;
  vettura: string | null;
  pista: string | null;
  tipo_sessione: string | null;
  campioni: number;
  ha_canali: boolean;
  canali_rimossi: boolean;
};

export function getStatoRegistratore() {
  return getJSON<StatoRegistratore>("/api/telemetria/stato");
}

export function getRegistrazioni() {
  return getJSON<{ sessioni: Registrazione[] }>("/api/telemetria/sessioni");
}

export function importaRegistrazione(id: string) {
  return sendJSON<{ id_sessione: string }>(`/api/telemetria/sessioni/${encodeURIComponent(id)}/importa`, "POST");
}

// ─────────────────────────────────────────────
// Catalogo ACC (Lotto 1): anagrafica vetture e circuiti servita dal backend
// (core/catalog.py). Sostituisce le liste hardcoded di lib/catalog.ts, che
// restano come fallback se il backend non risponde.
// ─────────────────────────────────────────────
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
  /** C'è una guida (nozioni curva per curva) per questo circuito. */
  ha_guida: boolean;
  /** Il layout a disco è stato guardato e approvato: si può mostrare. */
  mappa_verificata: boolean;
};

export type Catalog = {
  cars: CatalogCar[];
  tracks: CatalogTrack[];
  counts: { cars: number; tracks: number; by_category: Record<string, number> };
};

export function getCatalog() {
  return getJSON<Catalog>("/api/catalog");
}

// Schede complete (didascalie, specifiche, contesto di setup). `id` accetta
// slug o nome di display: il backend risolve entrambi.
export type CarSpecs = {
  engine?: string | null;
  power_hp?: number | null;
  weight_kg?: number | null;
  drivetrain?: string | null;
  gearbox?: string | null;
  bop_variable?: boolean;
  /** "alta" | "media" | "da_verificare" — quanto è affidabile la specifica. */
  confidence?: string;
};

export type CarSheet = CatalogCar & {
  specs: CarSpecs;
  caption_it: string;
  has_tc?: boolean;
  has_abs?: boolean;
  specs_note?: string | null;
};

export type TrackSheet = CatalogTrack & {
  description_it: string;
  setup_focus_it?: string | null;
  lap_record_real?: string | null;
  grid_size?: number | null;
  corners_confidence?: string;
};

// ─────────────────────────────────────────────
// Guida del tracciato — le nozioni curva per curva
// (backend: data/tracks_knowledge/<id>.json, servite da
// /api/catalog/track/{id}/guida). Sono contenuto da MOSTRARE al pilota, non
// contesto per l'LLM: quello che si legge qui è il testo della guida parola
// per parola, non una riscrittura.
//
// Quasi tutti i campi sono opzionali per scelta: una nozione che nessuna fonte
// documenta resta `null` invece di essere inventata, e la UI semplicemente non
// disegna la riga.
// ─────────────────────────────────────────────
export type GuidaSettore = {
  n: number;
  carattere?: string | null;
  cosa_decide?: string | null;
  errore_costoso?: string | null;
};

export type GuidaCurva = {
  n: number;
  /** null quando il nome non è documentato: non si inventa. */
  nome?: string | null;
  tipo?: string | null;
  marcia_indicativa?: string | null;
  riferimento_frenata?: string | null;
  insidia?: string | null;
  costo_errore?: string | null;
  /** Senso della curva; manca nelle guide del blocco 1. */
  direzione?: string | null;
  sorpasso?: {
    possibile?: boolean | null;
    come?: string | null;
    come_ci_si_difende?: string | null;
  } | null;
  gomme?: { stress?: string | null; note?: string | null } | null;
  freni?: { stress?: string | null; note?: string | null } | null;
  track_limits?: { rischio?: string | null; note?: string | null } | null;
  differenza_gara_qualifica?: string | null;
  /** Come si cresce su quella curva: dal giro pulito al limite. Chiesta dal
   *  blocco 2 in poi; le quattro guide del blocco 1 non ce l'hanno. */
  progressione?: {
    prendi_il_giro?: string | null;
    guadagni?: string | null;
    al_limite?: string | null;
  } | null;
  /** "fonte" | "mestiere": i consigli senza fonte sono marcati. */
  origine?: string | null;
  confidence?: string | null;
};

export type GuidaValoreConFonte = {
  valore?: number | string | null;
  contesto?: string | null;
  fonte?: string | null;
};

/** Da dove viene un campo di pista: il link, oppure una nota che dice perché
 *  il link non c'è. `fonte_singola` = un solo riscontro, da confermare. */
export type GuidaFonteCampo = {
  fonte?: string | null;
  fonte_singola?: boolean | null;
  nota?: string | null;
};

export type GuidaTracciato = {
  id: string;
  verifica_catalogo?: {
    lunghezza_confermata?: boolean | null;
    curve_confermate?: boolean | null;
    note?: string | null;
  } | null;
  /** I quattro campi di pista (dal blocco 2; retrofit sulle guide vecchie il 23/09). */
  senso_marcia?: string | null;
  dislivello_m?: number | null;
  rettilineo_piu_lungo_m?: number | null;
  variante_acc?: string | null;
  fonti_campi_pista?: {
    senso_marcia?: GuidaFonteCampo | null;
    dislivello_m?: GuidaFonteCampo | null;
    rettilineo_piu_lungo_m?: GuidaFonteCampo | null;
    variante_acc?: GuidaFonteCampo | null;
  } | null;
  settori?: GuidaSettore[];
  curve?: GuidaCurva[];
  track_limits_generale?: string | null;
  pit?: {
    tempo_perso_s?: number | null;
    limite_kmh?: number | null;
    lato_box?: string | null;
    note?: string | null;
    fonte?: string | null;
  } | null;
  traffico_multiclass?: string | null;
  meteo_e_luce?: {
    condizioni_tipiche?: string | null;
    sul_bagnato?: string | null;
    punti_acqua?: string | null;
    di_notte?: string | null;
    al_tramonto?: string | null;
  } | null;
  gomme_e_freni_pista?: string | null;
  errore_del_principiante?: string | null;
  gt3_ref_lap_time?: GuidaValoreConFonte | null;
  gt3_fuel_per_lap_l?: GuidaValoreConFonte | null;
  chicche?: { testo: string; perche_interessa_al_pilota?: string | null; fonte?: string | null }[];
  fonti?: (string | { url?: string; titolo?: string })[];
};

export function getCatalogCar(id: string) {
  return getJSON<CarSheet>(`/api/catalog/car/${encodeURIComponent(id)}`);
}

export function getCatalogTrack(id: string) {
  return getJSON<TrackSheet>(`/api/catalog/track/${encodeURIComponent(id)}`);
}

/** La guida del circuito. Va a 404 (e quindi in errore) per i circuiti che non
 *  ce l'hanno ancora: chi chiama tratta l'errore come «guida non disponibile»,
 *  che è un'informazione vera, non un guasto. */
export function getGuidaTracciato(id: string) {
  return getJSON<GuidaTracciato>(`/api/catalog/track/${encodeURIComponent(id)}/guida`);
}

export function getSetupParams(car?: string, track?: string) {
  const q = new URLSearchParams();
  if (car) q.set("car", car);
  if (track) q.set("track", track);
  return getJSON(`/api/setup-params?${q.toString()}`);
}

// ─────────────────────────────────────────────
// Gigi
// ─────────────────────────────────────────────
// `profile` (opzionale): riga "Profilo pilota: …" dal wizard. Viaggia in un campo
// separato dal prompt: il routing keyword della demo-cache lato server deve vedere
// solo le parole dell'utente. `sessionId`: la sessione di cui si parla (senza, la demo).
export function postAnalysis(prompt: string, profile?: string, sessionId?: string) {
  return sendJSON<{ question: string; text: string; source: string }>("/api/analysis", "POST", {
    prompt,
    ...(profile ? { profile } : {}),
    ...(sessionId ? { session_id: sessionId } : {}),
  });
}

export type VisionResult = { params: Record<string, number>; summary: string };

export function postSetupFromImage(file: File) {
  const form = new FormData();
  form.append("file", file);
  return postForm<VisionResult>("/api/setup/from-image", form);
}
