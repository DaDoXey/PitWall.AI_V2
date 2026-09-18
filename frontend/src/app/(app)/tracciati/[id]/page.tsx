"use client";

// Scheda del circuito: i dati del catalogo + la guida, dove la guida c'è.
//
// Il patto con il pilota, in tre righe:
//   * la **mappa** si vede solo se il layout è stato verificato a occhio; gli
//     altri venti file non stanno nemmeno più nel repo, così nessuno può
//     mostrarli per sbaglio;
//   * la **guida** è il testo delle nozioni, parola per parola, con le fonti
//     in fondo: se il circuito non ce l'ha ancora la scheda lo dice e basta,
//     senza riempitivi;
//   * la **placca chiara** della mappa è voluta: una mappa stampata appoggiata
//     sul cruscotto, non un disegno reinventato col filtro invert.
import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import CurvaGuida, { TitoloCurva } from "@/components/ui/CurvaGuida";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import {
  getCatalogTrack,
  getGuidaTracciato,
  type GuidaTracciato,
  type TrackSheet,
} from "@/lib/api";
import { useAssets, useCrop, type Crop } from "@/lib/assets";

const DOWNFORCE_LABEL: Record<string, string> = {
  low: "bassa",
  "medium-low": "medio-bassa",
  medium: "media",
  "medium-high": "medio-alta",
  high: "alta",
};

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="mt-0.5 font-mono text-sm text-white">{value}</div>
    </div>
  );
}

function Sezione({
  titolo,
  children,
}: {
  titolo: string;
  children: React.ReactNode;
}) {
  return (
    <motion.section variants={fadeInUp} className="rounded-xl border border-line bg-surface p-5">
      <h2 className="font-mono text-[0.6rem] uppercase tracking-widest text-accent">{titolo}</h2>
      <div className="mt-3">{children}</div>
    </motion.section>
  );
}

function Prosa({ children }: { children: React.ReactNode }) {
  return <p className="text-sm leading-relaxed text-subtle">{children}</p>;
}

/** Il centro del ritaglio scelto a mano, in coordinate `object-position`.
 *
 * `crops.json` descrive il ritaglio come «immagine larga w% e alta h% del
 * riquadro, spostata di l% e t%»: funziona solo se il riquadro ha le
 * proporzioni della banda su cui il ritaglio è stato scelto. Qui il riquadro è
 * più alto (lo stira il testo accanto), quindi di quelle percentuali si tiene
 * solo l'informazione che conta davvero — dove guardava Edoardo quando ha
 * scelto — e il resto lo fa `object-cover`, che ritaglia invece di stirare.
 * Senza ritaglio salvato si sta al centro, come prima.
 */
function puntoDiInteresse(crop?: Crop): string {
  if (!crop || !crop.w || !crop.h) return "50% 50%";
  const x = ((50 - crop.l) / crop.w) * 100;
  const y = ((50 - crop.t) / crop.h) * 100;
  const dentro = (v: number) => Math.min(100, Math.max(0, v));
  return `${dentro(x).toFixed(1)}% ${dentro(y).toFixed(1)}%`;
}

export default function TracciatoPage() {
  // `useParams` e non la prop `params`: in Next 15 quella è una Promise, e il
  // resto dell'app (lezioni/[slug]) fa già così.
  const { id } = useParams<{ id: string }>();
  const [track, setTrack] = useState<TrackSheet | null>(null);
  const [guida, setGuida] = useState<GuidaTracciato | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [aperta, setAperta] = useState<number | null>(null);
  const [fontiAperte, setFontiAperte] = useState(false);

  const assets = useAssets("tracks", track?.id);
  const { crop, band } = useCrop(track?.id);
  const [fotoRotta, setFotoRotta] = useState(false);

  useEffect(() => {
    let alive = true;
    getCatalogTrack(id)
      .then((t) => {
        if (!alive) return;
        setTrack(t);
        // La guida si chiede solo se il catalogo dice che c'è: il 404 sarebbe
        // una risposta corretta, ma non c'è motivo di andarlo a cercare.
        if (t.ha_guida) {
          getGuidaTracciato(t.id)
            .then((g) => alive && setGuida(g))
            .catch(() => alive && setGuida(null));
        }
      })
      .catch((e) => alive && setErrore(e instanceof Error ? e.message : "circuito non trovato"));
    return () => {
      alive = false;
    };
  }, [id]);

  if (errore) {
    return (
      <div>
        <PageHeader title="Tracciato" subtitle="non trovato" />
        <div className="rounded-xl border border-line bg-surface p-5 text-sm text-subtle">
          {errore}.{" "}
          <Link href="/tracciati" className="text-accent hover:underline">
            Torna all&apos;elenco
          </Link>
          .
        </div>
      </div>
    );
  }

  if (!track) {
    return (
      <div className="font-mono text-xs uppercase tracking-widest text-muted">carico il circuito…</div>
    );
  }

  const df = track.downforce_level
    ? DOWNFORCE_LABEL[track.downforce_level] ?? track.downforce_level
    : null;
  const meteo = guida?.meteo_e_luce ?? null;
  const righeMeteo = meteo
    ? ([
        ["Condizioni tipiche", meteo.condizioni_tipiche],
        ["Sul bagnato", meteo.sul_bagnato],
        ["Punti d'acqua", meteo.punti_acqua],
        ["Di notte", meteo.di_notte],
        ["Al tramonto", meteo.al_tramonto],
      ] as const).filter(([, v]) => !!v)
    : [];

  return (
    <div>
      <Link
        href="/tracciati"
        className="mb-3 inline-block font-mono text-[0.65rem] uppercase tracking-widest text-muted transition hover:text-accent"
      >
        ← Tracciati
      </Link>

      <PageHeader
        title={track.short_name || track.name}
        subtitle={[track.country, track.dlc ? `DLC ${track.dlc_pack ?? ""}`.trim() : "base"]
          .filter(Boolean)
          .join(" · ")}
      />

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="flex flex-col gap-4"
      >
        {/* Foto + identità + numeri del catalogo.
            La foto sta in colonna, e la colonna è PIÙ ALTA della banda per cui
            i ritagli sono stati scelti: in un flex il riquadro viene stirato
            all'altezza del testo, e le percentuali di crops.json — larghezza e
            altezza indipendenti — ci si adeguano deformando l'immagine (Imola:
            rapporto naturale 1,50 renderizzato 0,85).
            Qui quindi NON si usano le percentuali: si usa `object-cover`, che
            non stira mai, e il ritaglio scelto a mano si conserva come punto
            d'interesse tramite `object-position`. La lista dei tracciati e le
            card di sessione continuano a usare il crop esatto, perché lì il
            riquadro ha davvero le proporzioni della banda. */}
        <motion.section
          variants={fadeInUp}
          className="overflow-hidden rounded-xl border border-line bg-surface lg:flex"
        >
          {assets.photo && !fotoRotta && (
            <div
              className="relative shrink-0 overflow-hidden border-b border-line bg-black lg:w-[380px] lg:border-b-0 lg:border-r"
              style={{ aspectRatio: `${band.w} / ${band.h}` }}
            >
              {/* eslint-disable-next-line @next/next/no-img-element -- asset statico locale */}
              <img
                src={assets.photo}
                alt={`Il circuito di ${track.short_name || track.name}`}
                onError={() => setFotoRotta(true)}
                className="absolute inset-0 h-full w-full object-cover opacity-90"
                style={{ objectPosition: puntoDiInteresse(crop) }}
              />
            </div>
          )}
          <div className="flex-1 p-5">
            <div className="font-display text-lg font-bold">{track.name}</div>
            {track.nick && <div className="text-xs italic text-subtle">«{track.nick}»</div>}

            <div className="mt-4 flex flex-wrap gap-x-8 gap-y-3 border-t border-line pt-4">
              {track.length_km && <Fact label="Lunghezza" value={`${track.length_km} km`} />}
              {track.corners && (
                <Fact
                  label="Curve"
                  value={
                    track.corners_confidence && track.corners_confidence !== "alta"
                      ? `${track.corners} (da verificare)`
                      : String(track.corners)
                  }
                />
              )}
              {df && <Fact label="Deportanza" value={df} />}
              {track.grid_size && <Fact label="Griglia" value={`${track.grid_size} vetture`} />}
              {track.lap_record_real && (
                <Fact label="Record reale" value={track.lap_record_real} />
              )}
            </div>

            <p className="mt-4 text-sm leading-relaxed text-subtle">{track.description_it}</p>

            {track.setup_focus_it && (
              <div className="mt-4 rounded-lg border border-line bg-inset p-3">
                <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                  Focus setup
                </div>
                <p className="mt-1 text-sm leading-relaxed text-subtle">{track.setup_focus_it}</p>
              </div>
            )}
          </div>
        </motion.section>

        {/* Il layout, solo se verificato. Placca chiara dentro la scheda scura:
            una mappa stampata appoggiata sul cruscotto. */}
        {track.mappa_verificata && assets.map && (
          <Sezione titolo="Il layout">
            {/* La placca si adatta al disegno, non il contrario: `w-fit` +
                `w-auto` sull'immagine. Con una placca a larghezza piena il
                layout galleggiava in mezzo a due bande avorio vuote.
                I file hanno proporzioni molto diverse (Zandvoort è quasi
                quadrata a 1920×1753, Spa panoramica, Zolder un SVG che
                dichiara solo il viewBox e nessuna dimensione): l'altezza
                massima e la larghezza automatica reggono tutti i casi, e
                `overflow-hidden` è la cintura di sicurezza se un domani
                arriva un file con proporzioni fuori scala. */}
            <div className="mx-auto w-fit max-w-full overflow-hidden rounded-lg bg-[#f4f1ea] p-4">
              {/* eslint-disable-next-line @next/next/no-img-element -- asset statico locale */}
              {/* ALTEZZA fissa e larghezza automatica, non il contrario.
                  `zolder_map.svg` dichiara solo il viewBox, senza width né
                  height: con la larghezza in automatico il browser non sa
                  quanto è grande e lo riduce a un quadratino. Dando l'altezza
                  ricava la larghezza dal rapporto del viewBox, e i PNG si
                  comportano allo stesso modo. */}
              <img
                src={assets.map}
                alt={`Mappa del circuito di ${track.short_name || track.name}`}
                className="block h-[min(420px,52vw)] w-auto max-w-full object-contain"
              />
            </div>
            <p className="mt-2 font-mono text-[0.55rem] uppercase tracking-widest text-muted">
              layout verificato · attribuzioni in /crediti
            </p>
          </Sezione>
        )}

        {/* La guida. Quando non c'è, si dice e basta. */}
        {!track.ha_guida && (
          <motion.section
            variants={fadeInUp}
            className="rounded-xl border border-dashed border-line bg-surface p-5"
          >
            <div className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">
              La guida
            </div>
            <p className="mt-2 text-sm leading-relaxed text-subtle">
              Le nozioni curva per curva di questo circuito non ci sono ancora. Arrivano a blocchi,
              e finché non sono verificate qui non compare niente: meglio nessuna nozione che una
              sbagliata.
            </p>
          </motion.section>
        )}

        {guida && (
          <>
            {guida.settori && guida.settori.length > 0 && (
              <Sezione titolo="I settori">
                <div className="flex flex-col gap-3">
                  {guida.settori.map((s) => (
                    <div key={s.n} className="rounded-lg border border-line bg-inset p-3">
                      <div className="font-mono text-[0.6rem] uppercase tracking-widest text-subtle">
                        Settore {s.n}
                      </div>
                      {s.carattere && (
                        <p className="mt-1 text-sm leading-relaxed text-subtle">{s.carattere}</p>
                      )}
                      {s.cosa_decide && (
                        <p className="mt-2 text-sm leading-relaxed text-subtle">
                          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                            cosa decide ·{" "}
                          </span>
                          {s.cosa_decide}
                        </p>
                      )}
                      {s.errore_costoso && (
                        <p className="mt-2 text-sm leading-relaxed text-subtle">
                          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                            errore costoso ·{" "}
                          </span>
                          {s.errore_costoso}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </Sezione>
            )}

            {guida.curve && guida.curve.length > 0 && (
              <Sezione titolo={`Curva per curva · ${guida.curve.length}`}>
                <div className="flex flex-col divide-y divide-line overflow-hidden rounded-lg border border-line">
                  {guida.curve.map((c) => {
                    const apertaQui = aperta === c.n;
                    return (
                      <div key={c.n} className="bg-inset">
                        <button
                          onClick={() => setAperta(apertaQui ? null : c.n)}
                          aria-expanded={apertaQui}
                          className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-raised"
                        >
                          <TitoloCurva curva={c} />
                          <span
                            className={`font-mono text-xs text-muted transition-transform ${
                              apertaQui ? "rotate-90" : ""
                            }`}
                          >
                            ›
                          </span>
                        </button>
                        {apertaQui && (
                          <div className="border-t border-line px-4 pb-3 pt-1">
                            <CurvaGuida curva={c} />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Sezione>
            )}

            {guida.errore_del_principiante && (
              <Sezione titolo="L'errore che fanno tutti">
                <Prosa>{guida.errore_del_principiante}</Prosa>
              </Sezione>
            )}

            {guida.gomme_e_freni_pista && (
              <Sezione titolo="Gomme e freni su questa pista">
                <Prosa>{guida.gomme_e_freni_pista}</Prosa>
              </Sezione>
            )}

            {guida.track_limits_generale && (
              <Sezione titolo="Track limits">
                <Prosa>{guida.track_limits_generale}</Prosa>
              </Sezione>
            )}

            {guida.pit && (guida.pit.note || guida.pit.limite_kmh || guida.pit.tempo_perso_s) && (
              <Sezione titolo="Ai box">
                <div className="flex flex-wrap gap-x-8 gap-y-3">
                  {guida.pit.limite_kmh && (
                    <Fact label="Limite" value={`${guida.pit.limite_kmh} km/h`} />
                  )}
                  {guida.pit.tempo_perso_s && (
                    <Fact label="Tempo perso" value={`${guida.pit.tempo_perso_s} s`} />
                  )}
                  {guida.pit.lato_box && <Fact label="Lato box" value={guida.pit.lato_box} />}
                </div>
                {guida.pit.note && <p className="mt-3 text-sm leading-relaxed text-subtle">{guida.pit.note}</p>}
              </Sezione>
            )}

            {righeMeteo.length > 0 && (
              <Sezione titolo="Meteo e luce">
                <div className="flex flex-col gap-3">
                  {righeMeteo.map(([label, testo]) => (
                    <div key={label}>
                      <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                        {label}
                      </div>
                      <p className="mt-0.5 text-sm leading-relaxed text-subtle">{testo}</p>
                    </div>
                  ))}
                </div>
              </Sezione>
            )}

            {guida.traffico_multiclass && (
              <Sezione titolo="Traffico">
                <Prosa>{guida.traffico_multiclass}</Prosa>
              </Sezione>
            )}

            {guida.chicche && guida.chicche.length > 0 && (
              <Sezione titolo="Chicche">
                <div className="flex flex-col gap-3">
                  {guida.chicche.map((c, i) => (
                    <div key={i} className="rounded-lg border border-line bg-inset p-3">
                      <p className="text-sm leading-relaxed text-subtle">{c.testo}</p>
                      {c.perche_interessa_al_pilota && (
                        <p className="mt-1 text-sm leading-relaxed text-subtle/80">
                          {c.perche_interessa_al_pilota}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </Sezione>
            )}

            {/* Le fonti sono la nostra credibilità, ma non devono ingombrare:
                stanno in coda e si aprono se uno vuole controllare. */}
            {guida.fonti && guida.fonti.length > 0 && (
              <motion.section
                variants={fadeInUp}
                className="rounded-xl border border-line bg-surface p-5"
              >
                <button
                  onClick={() => setFontiAperte((v) => !v)}
                  aria-expanded={fontiAperte}
                  className="font-mono text-[0.6rem] uppercase tracking-widest text-muted transition hover:text-accent"
                >
                  {fontiAperte ? "− " : "+ "}
                  Fonti della guida · {guida.fonti.length}
                </button>
                {fontiAperte && (
                  <ul className="mt-3 flex flex-col gap-1">
                    {guida.fonti.map((f, i) => {
                      const url = typeof f === "string" ? f : f.url;
                      const titolo = typeof f === "string" ? f : f.titolo ?? f.url ?? "";
                      return (
                        <li key={i} className="break-all text-xs text-subtle">
                          {url ? (
                            <a
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="transition hover:text-accent"
                            >
                              {titolo}
                            </a>
                          ) : (
                            titolo
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </motion.section>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
}
