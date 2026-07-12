"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import UserChip from "@/components/ui/UserChip";
import { IconConsole, IconDashboard, IconLessons, IconSetup, IconTelemetry } from "@/components/ui/NavIcons";
import HealthStatus from "@/components/ui/HealthStatus";
import GigiAdvice from "@/components/ui/GigiAdvice";
import SidebarSection from "@/components/ui/SidebarSection";
import QuickNotes from "@/components/ui/QuickNotes";
import StintCompareModal from "@/components/charts/StintCompare";
import { getSession } from "@/lib/api";
import { DEFAULT_CONDITIONS } from "@/lib/catalog";
import { buildHealth, HEALTH_COLOR, HEALTH_LABEL } from "@/lib/health";
import { buildAlerts } from "@/lib/crosscheck";
import type { SessionData } from "@/lib/telemetry";

// Icone: set line-style coerente (NavIcons, FASE 4 #7) al posto delle emoji miste.
const NAV = [
  { href: "/", label: "Dashboard", icon: IconDashboard },
  { href: "/console", label: "Engineer Console", icon: IconConsole },
  { href: "/telemetry", label: "Telemetria", icon: IconTelemetry },
  { href: "/setup", label: "Setup", icon: IconSetup },
  { href: "/lezioni", label: "Lezioni", icon: IconLessons },
];

export default function Sidebar() {
  const path = usePathname();
  const [session, setSession] = useState<SessionData | null>(null);
  // Pannello footer aperto (note rapide). null = chiuso.
  const [footerPanel, setFooterPanel] = useState<"notes" | null>(null);
  // Modal confronto metà stint (FASE 8 #7): il bottone ⇄ è un launcher, non un toggle.
  const [compareOpen, setCompareOpen] = useState(false);

  useEffect(() => {
    getSession()
      .then(setSession)
      .catch(() => setSession(null)); // sidebar resta usabile anche senza backend
  }, []);

  const s = session?.session;
  // Stato aggregato + avvisi per i badge delle sezioni (visibili anche da compresse).
  const health = session ? buildHealth(session) : null;
  const alertCount = session ? buildAlerts(session).length : 0;

  return (
    <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-line bg-surface">
      {/* Header fisso in alto (megaprompt #7, FASE 2): brand + chip utente + NAV.
          I 4 tasti di navigazione stanno QUI, fuori dalla zona scrollabile: restano
          visibili sempre, ovunque sia lo scroll del corpo sidebar. */}
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
        {/* Stato attivo (FASE 4 #7): barra accent a sinistra + icona accent
            (hover: accent-hover), stesso pattern del filetto sinistro usato da
            Sessione corrente / Gigi consiglia — via la pillola piena. */}
        <nav className="mt-3 flex flex-col gap-1">
          {NAV.map((n) => {
            const active = path === n.href;
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

      {/* Area centrale scrollabile (solo moduli, la nav è nell'header fisso).
          Assorbe l'eccesso di altezza come coda in fondo invece di lasciare un
          vuoto a metà colonna; a finestra bassa scrolla, header e footer restano
          sempre raggiungibili. */}
      <div className="pw-scroll flex flex-1 flex-col gap-4 overflow-y-auto p-4">

      {/* Sessione corrente + stato sessione più visibile (badge demo) */}
      {s && (
        <div className="rounded-lg border border-l-2 border-line border-l-accent bg-inset p-3">
          <div className="mb-1 flex items-center justify-between">
            <span className="font-mono text-[0.55rem] uppercase tracking-widest text-accent">Sessione corrente</span>
            <span className="inline-flex items-center gap-1 font-mono text-[0.5rem] uppercase tracking-widest text-ok">
              <span className="h-1 w-1 rounded-full bg-ok" />
              demo
            </span>
          </div>
          <div className="text-sm text-white">{s.track}</div>
          <div className="font-mono text-[0.62rem] text-muted">
            {s.car} · stint {s.stint.toLowerCase()}
          </div>
          <div className="font-mono text-[0.62rem] text-muted">{DEFAULT_CONDITIONS}</div>
        </div>
      )}

      {/* Salute sessione + Avvisi FUSI (megaprompt #6, FASE 2): un solo modulo a due
          stati (semaforo sempre, lista avvisi su richiesta). Il badge resta visibile
          anche a sezione compressa: stato aggregato + conteggio avvisi se > 0. */}
      {session && health && (
        <SidebarSection
          id="health"
          title="Salute sessione"
          badge={
            <span
              className="inline-flex items-center gap-1 font-mono text-[0.5rem] uppercase tracking-widest"
              style={{ color: HEALTH_COLOR[health.overall] }}
            >
              <span className="h-1 w-1 rounded-full" style={{ background: HEALTH_COLOR[health.overall] }} />
              {HEALTH_LABEL[health.overall]}
              {alertCount > 0 && <span style={{ color: HEALTH_COLOR.warn }}>· {alertCount}</span>}
            </span>
          }
        >
          <HealthStatus data={session} />
        </SidebarSection>
      )}

      {/* Gigi consiglia (megaprompt #7, FASE 3): 1 sola voce (prossima azione) +
          link "vedi tutti" → Console. Il badge "online" migra qui dal widget
          footer rimosso: una sola rappresentazione di Gigi nella sidebar. */}
      {session && (
        <SidebarSection
          id="gigi"
          title="Gigi consiglia"
          badge={
            <span className="inline-flex items-center gap-1 font-mono text-[0.5rem] uppercase tracking-widest text-ok">
              <span className="h-1 w-1 rounded-full bg-ok" />
              online
            </span>
          }
        >
          <GigiAdvice data={session} />
        </SidebarSection>
      )}

      {/* Storico sessioni: riga coming-soon. La card "Sessioni recenti" è stata
          rimossa (megaprompt #7, FASE 3): mostrava la stessa identica sessione
          della card "Sessione corrente" qui sopra. */}
      <button
        type="button"
        disabled
        aria-disabled="true"
        title="Lo storico completo delle sessioni arriverà prossimamente"
        className="flex w-full cursor-not-allowed items-center justify-between rounded-md border border-dashed border-line px-2 py-1.5 text-left"
      >
        <span className="font-mono text-[0.58rem] text-subtle">Storico sessioni</span>
        <span className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">prossimamente</span>
      </button>
      </div>

      {/* Footer ancorato in fondo (niente più mt-auto → niente vuoto a metà colonna) */}
      <div className="flex flex-col gap-2 border-t border-line p-4">
        {/* Pannello footer attivo: note rapide (FASE 6 #5). Il confronto è un
            modal (FASE 8 #7): QuickCompare e la sua "precedente" statica finta
            sono stati sostituiti dal confronto metà stint su dati reali. */}
        {footerPanel === "notes" && <QuickNotes />}

        {/* Azioni rapide: sostituiscono i due shortcut-icona (FASE 6) */}
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setCompareOpen(true)}
            aria-haspopup="dialog"
            title="Confronta prima e seconda metà dello stint"
            className="flex h-8 items-center justify-center gap-1 rounded-md border border-line font-mono text-[0.58rem] text-subtle transition hover:border-accent hover:text-white"
          >
            ⇄ Confronto
          </button>
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
        </div>

        <div className="font-mono text-[0.6rem] text-muted">
          v0.1.0 · v2 scaffold
          <span className="block">© 2026 Edoardo Ferlito · MIT</span>
        </div>
      </div>

      {/* Modal confronto metà stint (overlay full-screen, raggiungibile da ogni pagina) */}
      <AnimatePresence>
        {compareOpen && session && <StintCompareModal data={session} onClose={() => setCompareOpen(false)} />}
      </AnimatePresence>
    </aside>
  );
}
