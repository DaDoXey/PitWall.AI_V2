"use client";

// Schede di contesto per la sessione: "il tracciato" e "la vettura", con le
// didascalie del catalogo ACC (Lotto 1) scritte nella voce di Gigi.
// Alimentate da /api/catalog/{car,track}/{id}: accettano indifferentemente
// slug o nome di display, quindi si possono passare direttamente i valori che
// l'app già usa (demo_data.SESSION.car, selettori del Setup).
//
// Onestà sui dati: le specifiche del Lotto 1 sono in larga parte ricostruite
// da conoscenza di dominio, non da fonte primaria (campo `specs.confidence`).
// Dove non è "alta" lo diciamo, invece di presentarle come certe.
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getCatalogCar, getCatalogTrack, type CarSheet, type TrackSheet } from "@/lib/api";
import { fadeInUp } from "@/lib/motion";

// Indice degli asset scaricati (public/assets/manifest.json, generato da
// fetch_assets.py). La copertura è parziale e l'estensione varia: senza indice
// la UI dovrebbe tentare una URL e gestire il 404. Caricato una volta sola e
// condiviso tra le card; se manca, le schede restano senza immagini.
type Manifest = {
  cars: Record<string, Record<string, string>>;
  tracks: Record<string, Record<string, string>>;
};

let manifestPromise: Promise<Manifest | null> | null = null;

function loadManifest(): Promise<Manifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch("/assets/manifest.json")
      .then((r) => (r.ok ? (r.json() as Promise<Manifest>) : null))
      .catch(() => null);
  }
  return manifestPromise;
}

function useAssets(kind: "cars" | "tracks", id: string | undefined) {
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

// Ritagli scelti a mano (public/assets/crops.json, export del tool generato da
// backend/scripts/build_crop_tool.py). Ogni voce dice come piazzare l'immagine
// dentro la banda, in percentuali del riquadro; `band` ne fissa il rapporto.
// Se il file manca si va di ritaglio centrato: la UI non dipende dal tool.
type Crop = { w: number; h: number; l: number; t: number };
type Band = { w: number; h: number };
type Crops = { band: Band; items: Record<string, Crop> };

const BANDA_PREDEFINITA: Band = { w: 540, h: 128 };

let cropsPromise: Promise<Crops | null> | null = null;

function loadCrops(): Promise<Crops | null> {
  if (!cropsPromise) {
    cropsPromise = fetch("/assets/crops.json")
      .then((r) => (r.ok ? (r.json() as Promise<Crops>) : null))
      .catch(() => null);
  }
  return cropsPromise;
}

function useCrop(id: string | undefined) {
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

const DOWNFORCE_LABEL: Record<string, string> = {
  low: "bassa",
  "medium-low": "medio-bassa",
  medium: "media",
  "medium-high": "medio-alta",
  high: "alta",
};

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-mono text-[0.6rem] uppercase tracking-widest text-accent">{children}</div>
  );
}

/** Coppia etichetta/valore in idioma "strumento": label mono minuta, valore in evidenza. */
function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-0.5 font-mono text-sm text-white">{value}</div>
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={fadeInUp}
      className="flex flex-col rounded-xl border border-line bg-surface p-4"
    >
      {children}
    </motion.div>
  );
}

/** Foto di testa della card: banda panoramica, si nasconde se il file non c'è.
 *
 * L'inquadratura non è centrata d'ufficio: la banda è molto più larga che alta,
 * quindi il centro geometrico della foto quasi mai coincide con la vettura o
 * col punto interessante del circuito. Il ritaglio di ogni foto viene scelto a
 * mano nel tool (`backend/scripts/build_crop_tool.py`) e arriva qui da
 * `crops.json` come quattro percentuali già pronte — larghezza, altezza e
 * scostamento dell'immagine dentro la banda — che si applicano senza rifare
 * conti in pagina.
 *
 * La banda ha un RAPPORTO fisso (non un'altezza fissa): quelle percentuali sono
 * relative al riquadro, quindi se cambiasse la proporzione l'immagine verrebbe
 * stirata. A larghezza piena della card resta alta come prima.
 * Senza ritaglio salvato si ricade su `object-cover` centrato, cioè il
 * comportamento di sempre.
 */
function Hero({ src, alt, crop, band }: { src?: string; alt: string; crop?: Crop; band: Band }) {
  const [broken, setBroken] = useState(false);
  if (!src || broken) return null;
  return (
    <div
      className="relative -mx-4 -mt-4 mb-3 w-[calc(100%+2rem)] overflow-hidden rounded-t-xl border-b border-line bg-black"
      style={{ aspectRatio: `${band.w} / ${band.h}` }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- asset statico
          locale, non serve l'ottimizzatore di next/image */}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onError={() => setBroken(true)}
        className="absolute max-w-none opacity-90"
        style={
          crop
            ? { width: `${crop.w}%`, height: `${crop.h}%`, left: `${crop.l}%`, top: `${crop.t}%` }
            : { inset: 0, width: "100%", height: "100%", objectFit: "cover" }
        }
      />
    </div>
  );
}

export function TrackCard({ track }: { track: string }) {
  const [data, setData] = useState<TrackSheet | null>(null);

  useEffect(() => {
    let alive = true;
    getCatalogTrack(track)
      .then((t) => alive && setData(t))
      .catch(() => alive && setData(null)); // pista fuori catalogo: la card non compare
    return () => {
      alive = false;
    };
  }, [track]);

  const assets = useAssets("tracks", data?.id);
  const { crop, band } = useCrop(data?.id);

  if (!data) return null;

  const df = data.downforce_level ? DOWNFORCE_LABEL[data.downforce_level] ?? data.downforce_level : null;

  return (
    <Card>
      <Hero
        src={assets.photo}
        alt={`Il circuito di ${data.short_name || data.name}`}
        crop={crop}
        band={band}
      />
      <Label>Il tracciato</Label>
      {/* Nome UFFICIALE, non lo short: l'intestazione della pagina dice già
          "Monza", qui la scheda aggiunge informazione invece di ripeterla. */}
      <div className="mt-1 font-display text-lg font-bold">{data.name}</div>
      {data.nick && <div className="text-xs italic text-subtle">«{data.nick}»</div>}

      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 border-t border-line pt-3">
        {data.length_km && <Fact label="Lunghezza" value={`${data.length_km} km`} />}
        {data.corners && <Fact label="Curve" value={String(data.corners)} />}
        {df && <Fact label="Deportanza" value={df} />}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-subtle">{data.description_it}</p>

      {data.setup_focus_it && (
        <div className="mt-3 rounded-lg border border-line bg-inset p-3">
          <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
            Focus setup
          </div>
          <p className="mt-1 text-sm leading-relaxed text-subtle">{data.setup_focus_it}</p>
        </div>
      )}
    </Card>
  );
}

// NIENTE loghi dei costruttori: Wikimedia Commons non è una fonte affidabile
// per i marchi. Nella passata del 30/08 la ricerca ha restituito "3-BMW.svg"
// (un disegno di vettura, non lo stemma), il logo Aston Martin del 1920 e —
// peggio — "9ff_logo.svg" per le Porsche, che è un'AZIENDA DIVERSA: un errore
// fattuale mostrato all'utente. Altri 13 marchi non hanno alcun candidato
// perché protetti da trademark. Le foto danno già riconoscibilità; per i loghi
// servirebbe una fonte curata (press kit ufficiali), non una ricerca automatica.

export function CarCard({ car }: { car: string }) {
  const [data, setData] = useState<CarSheet | null>(null);

  useEffect(() => {
    let alive = true;
    getCatalogCar(car)
      .then((c) => alive && setData(c))
      .catch(() => alive && setData(null));
    return () => {
      alive = false;
    };
  }, [car]);

  const assets = useAssets("cars", data?.id);
  const { crop, band } = useCrop(data?.id);

  if (!data) return null;

  const s = data.specs ?? {};
  // Aiuti alla guida: si segnala l'ASSENZA, non la presenza — è l'informazione
  // che cambia i consigli (una vettura senza TC non si regola come le altre).
  const missing = [
    data.has_tc === false ? "TC" : null,
    data.has_abs === false ? "ABS" : null,
  ].filter(Boolean);

  return (
    <Card>
      <Hero src={assets.photo} alt={data.display_name} crop={crop} band={band} />
      <Label>La vettura</Label>
      <div className="mt-1 font-display text-lg font-bold">{data.display_name}</div>
      <div className="text-xs text-subtle">
        {data.year}
        {data.dlc && data.dlc_pack ? ` · ${data.dlc_pack}` : ""}
      </div>

      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 border-t border-line pt-3">
        {s.engine && <Fact label="Motore" value={s.engine} />}
        {s.power_hp && <Fact label="Potenza" value={`${s.power_hp} CV`} />}
        {s.weight_kg && <Fact label="Peso" value={`${s.weight_kg} kg`} />}
      </div>

      <p className="mt-3 text-sm leading-relaxed text-subtle">{data.caption_it}</p>

      {missing.length > 0 && (
        <div className="mt-3 rounded-lg border border-warn/40 bg-inset p-2.5">
          <p className="text-xs text-subtle">
            Questa vettura non ha <span className="text-white">{missing.join(" né ")}</span>: i
            consigli che li riguardano non si applicano.
          </p>
        </div>
      )}

      {/* Provenienza: il Lotto 1 marca le specifiche non confermate su fonte
          primaria. Meglio dirlo che spacciarle per verificate. */}
      {s.confidence && s.confidence !== "alta" && (
        <p className="mt-2 font-mono text-[0.55rem] uppercase tracking-wider text-muted">
          {s.confidence === "da_verificare"
            ? "· specifiche da verificare"
            : "· specifiche indicative"}
        </p>
      )}
    </Card>
  );
}
