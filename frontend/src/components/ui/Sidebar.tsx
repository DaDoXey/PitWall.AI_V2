"use client";

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
import SidebarSection from "@/components/ui/SidebarSection";
import QuickNotes from "@/components/ui/QuickNotes";
import { useProfile } from "@/lib/profile";
import { useSessione } from "@/lib/sessione";
import { data, ETICHETTA_TIPO, etichettaFonte, giri, tempoGiro } from "@/lib/formato";
import { COLORS } from "@/lib/theme";

// Icone: set line-style coerente (NavIcons, FASE 4 #7) al posto delle emoji miste.
const NAV = [
  { href: "/", label: "Dashboard", icon: IconDashboard },
  { href: "/console", label: "Engineer Console", icon: IconConsole },
  { href: "/telemetry", label: "Telemetria", icon: IconTelemetry },
  { href: "/setup", label: "Setup", icon: IconSetup },
  { href: "/sessioni", label: "Sessioni", icon: IconSessions },
  { href: "/tracciati", label: "Tracciati", icon: IconTracks },
  { href: "/lezioni", label: "Lezioni", icon: IconLessons },
];

export default function Sidebar() {
  const path = usePathname();
  // Pannello footer aperto (note rapide). null = chiuso.
  const [footerPanel, setFooterPanel] = useState<"notes" | null>(null);
  // Replay onboarding (megaprompt #9, FASE 1): rilancia wizard → tour per la demo.
  const { startOnboarding } = useProfile();
  const { report } = useSessione();

  const primo = report?.verdetto[0] ?? null;

  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-line bg-surface">
      {/* Header fisso in alto (megaprompt #7, FASE 2): brand + chip utente + NAV.
          La navigazione sta QUI, fuori dalla zona scrollabile: resta visibile
          sempre, ovunque sia lo scroll del corpo sidebar. */}
      <div className="border-b border-line p-4">
        <div className="font-display text-lg font-bold tracking-wide">
          PITWALL<span className="text-accent">.AI</span>
        </div>
        <div className="mt-1 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted">
          Virtual Race Engineer
        </div>
        <div className="mt-3">
          <UserChip />
        </div>
        <nav className="mt-3 flex flex-col gap-1">
          {NAV.map((n) => {
            // Match anche le sotto-rotte (es. /lezioni/[slug]); "/" resta esatto.
            const active = n.href === "/" ? path === "/" : path === n.href || path.startsWith(`${n.href}/`);
            const Icon = n.icon;
            return (
              <motion.div key={n.href} whileHover={{ x: active ? 0 : 2 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href={n.href}
                  aria-current={active ? "page" : undefined}
                  className={`group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                    active ? "bg-raised text-white" : "text-subtle hover:bg-raised hover:text-white"
                  }`}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-active"
                      className="absolute bottom-1 left-0 top-1 w-[2px] rounded-full bg-accent group-hover:bg-accent-hover"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <span className={active ? "text-accent transition-colors group-hover:text-accent-hover" : "transition-colors"}>
                    <Icon />
                  </span>
                  {n.label}
                </Link>
              </motion.div>
            );
          })}
        </nav>
      </div>

      {/* Area centrale scrollabile: la sessione aperta e cosa dice il motore. */}
      <div className="pw-scroll flex flex-1 flex-col gap-4 overflow-y-auto p-4">
        <SelettoreSessione />

        {/* Il verdetto in una riga: il problema numero uno della sessione aperta. */}
        {report && (
          <SidebarSection
            id="verdetto"
            title="Verdetto"
            badge={
              <span
                className="inline-flex items-center gap-1 font-mono text-[0.5rem] uppercase tracking-widest"
                style={{ color: report.verdetto.length ? COLORS.warn : COLORS.ok }}
              >
                <span
                  className="h-1 w-1 rounded-full"
                  style={{ background: report.verdetto.length ? COLORS.warn : COLORS.ok }}
                />
                {report.verdetto.length ? `${report.verdetto.length} voci` : "pulito"}
              </span>
            }
          >
            {primo ? (
              <div className="rounded-lg border border-line bg-inset p-2.5">
                <div className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">Priorità 1</div>
                <div className="mt-0.5 text-[0.78rem] leading-snug text-white">{primo.titolo}</div>
                <div className="mt-1.5 text-[0.7rem] leading-snug text-subtle">{primo.azione}</div>
                <Link
                  href="/"
                  className="mt-2 inline-block font-mono text-[0.55rem] uppercase tracking-widest text-accent transition hover:underline"
                >
                  Tutto il verdetto →
                </Link>
              </div>
            ) : (
              <p className="text-[0.72rem] text-subtle">
                {report.giri_totali
                  ? "Nessuna perdita dimostrabile con i dati di questa sessione."
                  : "Nessun giro misurato: il verdetto parte dai tempi."}
              </p>
            )}
          </SidebarSection>
        )}
      </div>

      {/* Footer ancorato in fondo */}
      <div className="flex flex-col gap-2 border-t border-line p-4">
        {footerPanel === "notes" && <QuickNotes />}

        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setFooterPanel((p) => (p === "notes" ? null : "notes"))}
            aria-pressed={footerPanel === "notes"}
            title="Note rapide / promemoria personale"
            className={`flex h-8 items-center justify-center gap-1 rounded-md border font-mono text-[0.58rem] transition ${
              footerPanel === "notes" ? "border-accent text-white" : "border-line text-subtle hover:border-accent hover:text-white"
            }`}
          >
            ✎ Note
          </button>
          {/* Replay onboarding (megaprompt #9): rilancia wizard "Conosci il pilota" → tour. */}
          <button
            type="button"
            onClick={startOnboarding}
            aria-haspopup="dialog"
            title="Rifai il wizard Conosci il pilota e il tour delle schermate"
            className="flex h-8 items-center justify-center gap-1 rounded-md border border-line font-mono text-[0.58rem] text-subtle transition hover:border-accent hover:text-white"
          >
            ↻ Tutorial
          </button>
        </div>

        <div className="font-mono text-[0.6rem] text-muted">
          v1.1.0 · rework dati
          <span className="block">© 2026 Edoardo Ferlito · MIT</span>
          {/* Attribuzione asset: le licenze CC BY/BY-SA la vogliono
              raggiungibile dall'utente, non solo nel repo. */}
          <Link href="/crediti" className="mt-1 block transition hover:text-white">
            Crediti immagini
          </Link>
        </div>
      </div>
    </aside>
  );
}

// ─────────────────────────────────────────────
// Selettore della sessione aperta
// ─────────────────────────────────────────────
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
        className="w-full rounded-lg border border-l-2 border-line border-l-accent bg-inset p-3 text-left transition hover:border-line-strong"
      >
        <div className="mb-1 flex items-center justify-between">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-accent">Sessione aperta</span>
          <BadgeFonte s={sessione} />
        </div>
        <div className="text-sm text-white">{nomi.pista(sessione.track)}</div>
        <div className="truncate font-mono text-[0.62rem] text-muted">{nomi.vettura(sessione.car)}</div>
        <div className="mt-1 flex items-center justify-between font-mono text-[0.58rem] text-subtle">
          <span>
            {ETICHETTA_TIPO[sessione.tipo_sessione] ?? "Sessione"} · {giri(sessione.giri)}
          </span>
          <span className="text-muted">{aperto ? "▴" : "cambia ▾"}</span>
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
            className="pw-scroll absolute left-0 right-0 z-30 mt-1 max-h-80 overflow-y-auto rounded-lg border border-line bg-raised p-1 shadow-xl"
          >
            {elenco.map((s) => {
              const scelta = s.id === sessione.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  role="option"
                  aria-selected={scelta}
                  onClick={() => {
                    apri(s.id);
                    setAperto(false);
                  }}
                  className={`block w-full rounded-md px-2.5 py-2 text-left transition ${
                    scelta ? "bg-accent/15" : "hover:bg-surface"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`truncate text-[0.78rem] ${scelta ? "text-accent" : "text-white"}`}>
                      {nomi.pista(s.track)}
                    </span>
                    <BadgeFonte s={s} />
                  </div>
                  <div className="truncate font-mono text-[0.58rem] text-muted">{nomi.vettura(s.car)}</div>
                  <div className="font-mono text-[0.56rem] text-subtle">
                    {giri(s.giri)} · best {tempoGiro(s.miglior_giro_ms)}
                    {!s.demo && (s.iniziata_il || s.importato_il) ? ` · ${data(s.iniziata_il ?? s.importato_il)}` : ""}
                  </div>
                </button>
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
