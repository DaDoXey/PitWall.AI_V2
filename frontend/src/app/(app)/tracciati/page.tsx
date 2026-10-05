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
import ServizioFermo from "@/components/ui/ServizioFermo";
import { SERVIZIO_FERMO } from "@/lib/errori";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { getCatalog, type CatalogTrack } from "@/lib/api";
import { useAssetsIndex, useCrop } from "@/lib/assets";
import { useSessione } from "@/lib/sessione";

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
  const [tentativo, setTentativo] = useState(0);
  const [filtro, setFiltro] = useState<Filtro>("tutti");
  const foto = useAssetsIndex("tracks");
  const { elenco: sessioni, sessione } = useSessione();
  // Quante sessioni (tue o di riferimento, non la demo) ci sono in archivio per pista.
  const perPista = useMemo(() => {
    const conta = new Map<string, number>();
    for (const x of sessioni ?? []) if (!x.demo && x.track) conta.set(x.track, (conta.get(x.track) ?? 0) + 1);
    return conta;
  }, [sessioni]);

  useEffect(() => {
    let alive = true;
    setErrore(null);
    getCatalog()
      .then((c) => alive && setTracks(c.tracks))
      .catch(() => alive && setErrore(SERVIZIO_FERMO));
    return () => {
      alive = false;
    };
  }, [tentativo]);

  const conGuida = useMemo(() => (tracks ?? []).filter((t) => t.ha_guida).length, [tracks]);
  const essenziali = useMemo(() => (tracks ?? []).filter((t) => t.guida_essenziale).length, [tracks]);

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
            ? `${tracks.length} circuiti ACC · ${conGuida} con la guida curva per curva` +
              (essenziali ? ` (${essenziali} essenzial${essenziali === 1 ? "e" : "i"})` : "")
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

      {errore && <ServizioFermo onRiprova={() => setTentativo((t) => t + 1)} />}

      {!tracks && !errore && (
        <div className="font-mono text-xs uppercase tracking-widest text-muted">
          carico il catalogo…
        </div>
      )}

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      >
        {elenco.map((t) => (
          <motion.div key={t.id} variants={fadeInUp}>
            <Link
              href={`/tracciati/${t.id}`}
              className="group flex h-full flex-col overflow-hidden rounded-xl border border-line bg-surface transition duration-200 hover:-translate-y-1 hover:border-accent/50"
            >
              <Banda src={foto[t.id]?.photo} alt={`Il circuito di ${t.short_name}`} id={t.id} />
              <div className="flex flex-1 flex-col p-3">
                <div className="flex items-baseline justify-between gap-2">
                  <h2 className="font-display text-[0.95rem] font-bold tracking-wide transition-colors group-hover:text-accent">
                    {t.short_name}
                  </h2>
                  <span className="truncate font-mono text-[0.58rem] uppercase tracking-wider text-muted">
                    {t.country}
                  </span>
                </div>
                {/* il soprannome solo se dice qualcosa in più del nome («COTA» sotto COTA no) */}
                {t.nick && t.nick.toLowerCase() !== t.short_name.toLowerCase() && (
                  <div className="mt-0.5 text-xs italic text-subtle">«{t.nick}»</div>
                )}

                {/* numeri e bandierine in fondo: le card della stessa riga restano allineate */}
                <div className="mt-auto">
                  <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 border-t border-line pt-2.5 font-mono text-[0.68rem] text-subtle">
                    {t.length_km && <span>{t.length_km} km</span>}
                    {t.corners && <span>{t.corners} curve</span>}
                    {t.dlc && <span className="text-muted">DLC</span>}
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    <Bandierina acceso={t.ha_guida}>
                      {!t.ha_guida ? "guida in arrivo" : t.guida_essenziale ? "guida essenziale" : "guida"}
                    </Bandierina>
                    {t.mappa_verificata && <Bandierina acceso>layout</Bandierina>}
                    {sessione?.track === t.id && <Bandierina acceso>aperta ora</Bandierina>}
                    {perPista.get(t.id) && (
                      <Bandierina acceso={false}>
                        {perPista.get(t.id)} {perPista.get(t.id) === 1 ? "sessione" : "sessioni"}
                      </Bandierina>
                    )}
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
