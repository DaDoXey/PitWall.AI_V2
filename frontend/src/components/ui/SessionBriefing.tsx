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

  if (!data) return null;

  const df = data.downforce_level ? DOWNFORCE_LABEL[data.downforce_level] ?? data.downforce_level : null;

  return (
    <Card>
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
