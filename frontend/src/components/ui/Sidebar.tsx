"use client";

// La colonna di sinistra. Riordino del 29/09/2026 (Entry #048), con le regole del #6 e
// del #7 (niente duplicati, navigazione sempre visibile, pochi blocchi):
//   * in cima la SESSIONE APERTA, compatta: è il contesto delle quattro pagine sotto;
//   * la navigazione in due gruppi — «La sessione» (Dashboard, Telemetria, Setup,
//     Engineer Console) e, in una riga sola, «Archivio e studio» (Sessioni, Tracciati, Lezioni);
//   * via il riquadro Verdetto: era la copia della prima voce della Dashboard;
//   * nello spazio libero «La pista»: la mappa della sessione aperta e la curva dove
//     perdi di più (PannelloPista), che si adatta all'altezza dello schermo;
//   * note e utente sono due icone accanto al marchio (il menu dell'utente ha tutorial,
//     crediti, versione, esci): niente piede, lo spazio va alla mappa della pista.
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import UserChip from "@/components/ui/UserChip";
import {
  IconConsole,
  IconDashboard,
  IconLessons,
  IconSessions,
  IconSetup,
  IconTelemetry,
  IconTracks,
} from "@/components/ui/NavIcons";
import PannelloPista from "@/components/ui/PannelloPista";
import QuickNotes from "@/components/ui/QuickNotes";
import type { Riassunto } from "@/lib/api";
import { GRUPPI_SESSIONI, useSessione } from "@/lib/sessione";
import { data, ETICHETTA_TIPO, etichettaFonte, giri, tempoGiro } from "@/lib/formato";

// Icone: set line-style coerente (NavIcons, FASE 4 #7) al posto delle emoji miste.
const NAV_SESSIONE = [
  { href: "/", label: "Dashboard", icon: IconDashboard },
  { href: "/telemetry", label: "Telemetria", icon: IconTelemetry },
  { href: "/setup", label: "Setup", icon: IconSetup },
  { href: "/console", label: "Engineer Console", icon: IconConsole },
];
const NAV_ARCHIVIO = [
  { href: "/sessioni", label: "Sessioni", icon: IconSessions },
  { href: "/tracciati", label: "Tracciati", icon: IconTracks },
  { href: "/lezioni", label: "Lezioni", icon: IconLessons },
];

// Quante sessioni per gruppo nell'elenco rapido: le altre stanno nella pagina Sessioni.
const PER_GRUPPO = 5;

function attiva(path: string, href: string) {
  // Match anche le sotto-rotte (es. /lezioni/[slug]); "/" resta esatto.
  return href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`);
}

function Gruppo({ titolo }: { titolo: string }) {
  return <div className="mb-1.5 px-3 font-mono text-[0.58rem] uppercase tracking-[0.18em] text-muted">{titolo}</div>;
}

/** Le note rapide: un'icona in testa alla colonna, il blocco note si apre sotto. */
function Note() {
  const [aperte, setAperte] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!aperte) return;
    const fuori = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAperte(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setAperte(false);
    document.addEventListener("mousedown", fuori);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", fuori);
      document.removeEventListener("keydown", esc);
    };
  }, [aperte]);
  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setAperte((n) => !n)}
        aria-pressed={aperte}
        aria-label="Note rapide"
        title="Note rapide / promemoria personale"
        className={`flex h-8 w-8 items-center justify-center rounded-full border text-sm transition ${
          aperte ? "border-accent text-white" : "border-line text-subtle hover:border-line-strong hover:text-white"
        }`}
      >
        ✎
      </button>
      {aperte && (
        <div className="absolute left-0 top-full z-40 mt-2 w-64 rounded-lg border border-line bg-raised p-1 shadow-xl">
          <QuickNotes />
        </div>
      )}
    </div>
  );
}

function ArchivioInRiga() {
  const path = usePathname();
  return (
    <div className="flex items-center gap-1 px-3 text-[0.78rem]">
      {NAV_ARCHIVIO.map((n, i) => {
        const active = attiva(path, n.href);
        return (
          <span key={n.href} className="flex items-center gap-1">
            {i > 0 && <span className="text-line-strong">·</span>}
            <Link
              href={n.href}
              aria-current={active ? "page" : undefined}
              className={`rounded px-1 py-0.5 transition ${
                active ? "text-white underline decoration-accent decoration-2 underline-offset-4" : "text-muted hover:text-white"
              }`}
            >
              {n.label}
            </Link>
          </span>
        );
      })}
    </div>
  );
}

function Voce({ href, label, icon: Icon, piccola }: (typeof NAV_SESSIONE)[number] & { piccola?: boolean }) {
  const path = usePathname();
  const active = attiva(path, href);
  return (
    <motion.div whileHover={{ x: active ? 0 : 2 }} whileTap={{ scale: 0.98 }}>
      <Link
        href={href}
        aria-current={active ? "page" : undefined}
        className={`group relative flex items-center gap-3 rounded-md px-3 transition ${piccola ? "py-1.5 text-[0.8rem]" : "py-1.5 text-sm"} ${
          active ? "bg-raised text-white" : piccola ? "text-muted hover:bg-raised hover:text-white" : "text-subtle hover:bg-raised hover:text-white"
        }`}
      >
        {active && (
          <motion.span
            layoutId="nav-active"
            className="absolute bottom-1 left-0 top-1 w-[2px] rounded-full bg-accent group-hover:bg-accent-hover"
            transition={{ type: "spring", stiffness: 420, damping: 34 }}
          />
        )}
        <span className={`${active ? "text-accent group-hover:text-accent-hover" : ""} transition-colors ${piccola ? "scale-90" : ""}`}>
          <Icon />
        </span>
        {label}
      </Link>
    </motion.div>
  );
}

export default function Sidebar() {
  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-line bg-surface">
      {/* Testa: marchio e sessione aperta. Fuori dallo scroll: il selettore apre un
          elenco sopra la navigazione e non deve essere tagliato. */}
      <div className="flex flex-col gap-3 border-b border-line px-4 pb-3 pt-4">
        <div className="flex items-start justify-between gap-2 pl-1">
          <div className="min-w-0">
            <div className="font-display text-lg font-bold tracking-wide">
              PITWALL<span className="text-accent">.AI</span>
            </div>
            <div className="mt-1 whitespace-nowrap font-mono text-[0.5rem] uppercase tracking-[0.12em] text-muted">Virtual Race Engineer</div>
          </div>
          {/* Note e utente: due icone, non due riquadri. Il piede della colonna non c'è
              più: il suo spazio va alla mappa della pista. */}
          <div className="flex shrink-0 items-center gap-1.5">
            <Note />
            <UserChip />
          </div>
        </div>
        <SelettoreSessione />
      </div>

      {/* Navigazione: prende l'altezza che le serve; scorre solo se lo schermo è più
          basso di lei. Ha la precedenza sul pannello della pista. */}
      <nav className="pw-scroll flex min-h-0 shrink flex-col gap-4 overflow-y-auto px-3 pb-2 pt-3">
        <div className="flex flex-col gap-0.5">
          <Gruppo titolo="La sessione" />
          {NAV_SESSIONE.map((n) => (
            <Voce key={n.href} {...n} />
          ))}
        </div>
        {/* Una riga sola: sono pagine che si aprono ogni tanto, e lo spazio sotto serve
            alla mappa della pista anche sugli schermi bassi. */}
        <div>
          <Gruppo titolo="Archivio e studio" />
          <ArchivioInRiga />
        </div>
      </nav>

      {/* Lo spazio che resta: la pista della sessione aperta (mappa, curva peggiore). */}
      <PannelloPista />

    </aside>
  );
}

// ─────────────────────────────────────────────
// Selettore della sessione aperta
// ─────────────────────────────────────────────

// I gruppi dell'elenco rapido (Le tue / Riferimenti / Demo) stanno in lib/sessione:
// li usa anche la pagina Sessioni. Prima erano tutte in fila per data, indistinguibili.
function SelettoreSessione() {
  const { elenco, sessione, apri, nomi, errore } = useSessione();
  const [aperto, setAperto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!aperto) return;
    const fuori = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAperto(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setAperto(false);
    document.addEventListener("mousedown", fuori);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", fuori);
      document.removeEventListener("keydown", esc);
    };
  }, [aperto]);

  if (errore && !elenco) return <p className="text-[0.72rem] text-warn">{errore}</p>;
  if (!sessione) return <p className="font-mono text-[0.6rem] text-muted">Caricamento sessioni…</p>;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setAperto((a) => !a)}
        aria-expanded={aperto}
        aria-haspopup="listbox"
        className="w-full rounded-lg border border-l-2 border-line border-l-accent bg-inset px-3 py-2.5 text-left transition hover:border-line-strong"
      >
        <div className="flex items-center justify-between gap-2">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-accent">Sessione aperta</span>
          <BadgeFonte s={sessione} />
        </div>
        <div className="mt-1.5 truncate text-sm text-white">{nomi.pista(sessione.track)}</div>
        <div className="truncate text-[0.72rem] text-subtle">{nomi.vettura(sessione.car)}</div>
        <div className="mt-1.5 flex items-center justify-between font-mono text-[0.58rem] text-muted">
          <span>
            {ETICHETTA_TIPO[sessione.tipo_sessione] ?? "Sessione"} · {giri(sessione.giri)}
          </span>
          <span className="text-subtle">{aperto ? "▴" : "cambia ▾"}</span>
        </div>
      </button>

      <AnimatePresence>
        {aperto && elenco && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.12 }}
            role="listbox"
            // Più largo della colonna (sborda sulla pagina): pista, vettura e badge
            // devono leggersi interi, non «Zandvoort · McLar…».
            className="pw-scroll absolute left-0 z-30 mt-1 max-h-[26rem] w-80 overflow-y-auto rounded-lg border border-line bg-raised p-1 shadow-xl"
          >
            {GRUPPI_SESSIONI.map((g) => {
              const tutte = elenco.filter(g.filtro);
              if (tutte.length === 0) return null;
              // La sessione aperta resta visibile anche se è oltre le prime cinque.
              const prime = tutte.slice(0, PER_GRUPPO);
              if (!prime.some((s) => s.id === sessione.id) && tutte.some((s) => s.id === sessione.id)) {
                prime[prime.length - 1] = sessione;
              }
              return (
                <div key={g.titolo} className="mb-1">
                  <div className="px-2.5 pb-0.5 pt-1.5 font-mono text-[0.5rem] uppercase tracking-widest text-muted">
                    {g.titolo} · {tutte.length}
                  </div>
                  {prime.map((s) => (
                    <VoceSessione
                      key={s.id}
                      s={s}
                      scelta={s.id === sessione.id}
                      nomi={nomi}
                      onScegli={() => {
                        apri(s.id);
                        setAperto(false);
                      }}
                    />
                  ))}
                  {tutte.length > PER_GRUPPO && (
                    <Link
                      href="/sessioni"
                      onClick={() => setAperto(false)}
                      className="block px-2.5 py-1 font-mono text-[0.55rem] text-subtle transition hover:text-white"
                    >
                      altre {tutte.length - PER_GRUPPO} in Sessioni →
                    </Link>
                  )}
                </div>
              );
            })}
            <Link
              href="/sessioni"
              onClick={() => setAperto(false)}
              className="mt-1 block rounded-md border-t border-line px-2.5 py-2 font-mono text-[0.58rem] uppercase tracking-widest text-subtle transition hover:text-white"
            >
              + Importa o crea una sessione
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function VoceSessione({
  s,
  scelta,
  nomi,
  onScegli,
}: {
  s: Riassunto;
  scelta: boolean;
  nomi: ReturnType<typeof useSessione>["nomi"];
  onScegli: () => void;
}) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={scelta}
      onClick={onScegli}
      className={`block w-full rounded-md px-2.5 py-1.5 text-left transition ${scelta ? "bg-accent/15" : "hover:bg-surface"}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className={`truncate text-[0.78rem] ${scelta ? "text-accent" : "text-white"}`}>{nomi.pista(s.track)}</span>
        <BadgeFonte s={s} />
      </div>
      <div className="truncate text-[0.7rem] text-subtle">{nomi.vettura(s.car)}</div>
      <div className="font-mono text-[0.55rem] text-subtle">
        {giri(s.giri)} · best {tempoGiro(s.miglior_giro_ms)}
        {!s.demo && (s.iniziata_il || s.importato_il) ? ` · ${data(s.iniziata_il ?? s.importato_il)}` : ""}
        {!s.ha_canali && !s.demo ? " · senza telemetria" : ""}
      </div>
    </button>
  );
}

function BadgeFonte({
  s,
}: {
  s: { fonte: Parameters<typeof etichettaFonte>[0]; piattaforma: Parameters<typeof etichettaFonte>[1]; demo: boolean; riferimento?: boolean };
}) {
  return (
    <span
      className={`shrink-0 rounded border px-1 font-mono text-[0.48rem] uppercase tracking-widest ${
        s.demo ? "border-ok/50 text-ok" : "border-line-strong text-subtle"
      }`}
    >
      {etichettaFonte(s.fonte, s.piattaforma)}
      {s.riferimento ? " · rif." : ""}
    </span>
  );
}
