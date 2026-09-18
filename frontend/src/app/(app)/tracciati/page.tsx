"use client";

// Tracciati — indice dei 25 circuiti ACC (filone «guide dei tracciati», 18/09/2026).
//
// È la prima pagina che mostra il lavoro del catalogo: fino a oggi le guide
// stavano a disco e non le leggeva nessuno, e i layout stavano in public/ senza
// che una riga di UI li citasse.
//
// Due regole visibili qui, tutte e due già decise:
//   1. **Meglio niente che sbagliato.** La card dice «guida» o «layout» solo
//      quando ci sono davvero: le bandierine arrivano dal backend
//      (`ha_guida`, `mappa_verificata`), non da un tentativo di caricare il file.
//   2. **Niente placeholder finti.** Un circuito senza guida resta una scheda
//      onesta con i dati del catalogo: si apre lo stesso, e dice come stanno le cose.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { getCatalog, type CatalogTrack } from "@/lib/api";
import { useAssetsIndex, useCrop } from "@/lib/assets";

type Filtro = "tutti" | "guida" | "senza";

const FILTRI: { id: Filtro; label: string }[] = [
  { id: "tutti", label: "Tutti" },
  { id: "guida", label: "Con guida" },
  { id: "senza", label: "Ancora senza" },
];

/** Banda panoramica con la foto del circuito, ritagliata come nelle card di
 *  sessione. Si nasconde da sola se il file non c'è (Valencia, oggi). */
function Banda({ src, alt, id }: { src?: string; alt: string; id: string }) {
  const { crop, band } = useCrop(id);
  const [rotta, setRotta] = useState(false);
  if (!src || rotta) return null;
  return (
    <div
      className="relative overflow-hidden rounded-t-xl border-b border-line bg-black"
      style={{ aspectRatio: `${band.w} / ${band.h}` }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- asset statico locale */}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onError={() => setRotta(true)}
        className="absolute max-w-none opacity-90 transition duration-300 group-hover:opacity-100"
        style={
          crop
            ? { width: `${crop.w}%`, height: `${crop.h}%`, left: `${crop.l}%`, top: `${crop.t}%` }
            : { inset: 0, width: "100%", height: "100%", objectFit: "cover" }
        }
      />
    </div>
  );
}

function Bandierina({ children, acceso }: { children: React.ReactNode; acceso: boolean }) {
  return (
    <span
      className={`rounded border px-2 py-0.5 font-mono text-[0.6rem] uppercase tracking-wider ${
        acceso ? "border-accent/40 bg-accent/10 text-accent" : "border-line bg-inset text-muted"
      }`}
    >
      {children}
    </span>
  );
}

export default function TracciatiPage() {
  const [tracks, setTracks] = useState<CatalogTrack[] | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("tutti");
  const foto = useAssetsIndex("tracks");

  useEffect(() => {
    let alive = true;
    getCatalog()
      .then((c) => alive && setTracks(c.tracks))
      .catch((e) => alive && setErrore(e instanceof Error ? e.message : "catalogo non raggiungibile"));
    return () => {
      alive = false;
    };
  }, []);

  const conGuida = useMemo(() => (tracks ?? []).filter((t) => t.ha_guida).length, [tracks]);

  const elenco = useMemo(() => {
    const t = tracks ?? [];
    const filtrati =
      filtro === "guida" ? t.filter((x) => x.ha_guida)
      : filtro === "senza" ? t.filter((x) => !x.ha_guida)
      : t;
    // Alfabetico sul nome breve: è quello che il pilota legge.
    return [...filtrati].sort((a, b) => a.short_name.localeCompare(b.short_name, "it"));
  }, [tracks, filtro]);

  return (
    <div>
      <PageHeader
        title="Tracciati"
        subtitle={
          tracks
            ? `${tracks.length} circuiti ACC · ${conGuida} con la guida curva per curva`
            : "catalogo ACC"
        }
      />

      <div className="mb-5 flex flex-wrap items-center gap-2">
        {FILTRI.map((f) => (
          <button
            key={f.id}
            onClick={() => setFiltro(f.id)}
            className={`rounded-full border px-3 py-1 font-mono text-[0.65rem] uppercase tracking-wider transition ${
              filtro === f.id
                ? "border-accent bg-accent/10 text-accent"
                : "border-line text-muted hover:border-line-strong hover:text-subtle"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {errore && (
        <div className="rounded-xl border border-line bg-surface p-5 text-sm text-subtle">
          Il catalogo non risponde ({errore}). La pagina non inventa nulla: riprova quando il
          backend è su.
        </div>
      )}

      {!tracks && !errore && (
        <div className="font-mono text-xs uppercase tracking-widest text-muted">
          carico il catalogo…
        </div>
      )}

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
      >
        {elenco.map((t) => (
          <motion.div key={t.id} variants={fadeInUp}>
            <Link
              href={`/tracciati/${t.id}`}
              className="group flex h-full flex-col overflow-hidden rounded-xl border border-line bg-surface transition duration-200 hover:-translate-y-1 hover:border-accent/50"
            >
              <Banda src={foto[t.id]?.photo} alt={`Il circuito di ${t.short_name}`} id={t.id} />
              <div className="flex flex-1 flex-col p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <h2 className="font-display text-base font-bold tracking-wide transition-colors group-hover:text-accent">
                    {t.short_name}
                  </h2>
                  <span className="font-mono text-[0.6rem] uppercase tracking-wider text-muted">
                    {t.country}
                  </span>
                </div>
                {t.nick && <div className="mt-0.5 text-xs italic text-subtle">«{t.nick}»</div>}

                <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-line pt-3 font-mono text-[0.7rem] text-subtle">
                  {t.length_km && <span>{t.length_km} km</span>}
                  {t.corners && <span>{t.corners} curve</span>}
                  {t.dlc && <span className="text-muted">DLC</span>}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <Bandierina acceso={t.ha_guida}>
                    {t.ha_guida ? "guida" : "guida in arrivo"}
                  </Bandierina>
                  {t.mappa_verificata && <Bandierina acceso>layout</Bandierina>}
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
