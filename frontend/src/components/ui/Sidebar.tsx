"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import GigiAvatar from "@/components/ui/GigiAvatar";
import HealthStatus from "@/components/ui/HealthStatus";
import GigiAdvice from "@/components/ui/GigiAdvice";
import SidebarSection from "@/components/ui/SidebarSection";
import MiniValues from "@/components/ui/MiniValues";
import QuickNotes from "@/components/ui/QuickNotes";
import QuickCompare from "@/components/ui/QuickCompare";
import { getSession } from "@/lib/api";
import { DEFAULT_CONDITIONS } from "@/lib/catalog";
import { buildHealth, HEALTH_COLOR, HEALTH_LABEL } from "@/lib/health";
import { buildAlerts } from "@/lib/crosscheck";
import type { SessionData } from "@/lib/telemetry";

const NAV = [
  { href: "/", label: "Dashboard", icon: "▦" },
  { href: "/console", label: "Engineer Console", icon: "🎧" },
  { href: "/telemetry", label: "Telemetria", icon: "📈" },
  { href: "/setup", label: "Setup", icon: "🔧" },
];

export default function Sidebar() {
  const path = usePathname();
  const [session, setSession] = useState<SessionData | null>(null);
  // Pannello footer aperto (note rapide / confronto), esclusivo. null = chiuso.
  const [footerPanel, setFooterPanel] = useState<"notes" | "compare" | null>(null);

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
      {/* Header fisso in alto */}
      <div className="border-b border-line p-4">
        <div className="font-display text-lg font-bold tracking-wide">
          PITWALL<span className="text-accent">.AI</span>
        </div>
        <div className="mt-1 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted">
          Virtual Race Engineer
        </div>
      </div>

      {/* Area centrale scrollabile (nav + moduli). Assorbe l'eccesso di altezza
          come coda in fondo invece di lasciare un vuoto a metà colonna (fix layout);
          a finestra bassa scrolla, header e footer restano sempre raggiungibili. */}
      <div className="pw-scroll flex flex-1 flex-col gap-4 overflow-y-auto p-4">
      <nav className="flex flex-col gap-1">
        {NAV.map((n) => {
          const active = path === n.href;
          return (
            <motion.div key={n.href} whileHover={{ x: active ? 0 : 2 }} whileTap={{ scale: 0.98 }}>
              <Link
                href={n.href}
                className={`relative flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                  active ? "text-white" : "text-subtle hover:bg-raised"
                }`}
              >
                {active && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-0 rounded-md bg-accent"
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  />
                )}
                <span className="relative z-10">{n.icon}</span>
                <span className="relative z-10">{n.label}</span>
              </Link>
            </motion.div>
          );
        })}
      </nav>

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

      {/* Mini values window: 3 valori chiave di sessione (FASE 6) */}
      {session && <MiniValues data={session} />}

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

      {/* Sessioni recenti (per ora la sola demo; predisposta per lo storico futuro) */}
      <SidebarSection id="recent" title="Sessioni recenti">
        <div className="rounded-lg border border-line bg-surface p-2.5">
          <div className="text-[0.8rem] text-white">{s?.track ?? "Monza"}</div>
          <div className="font-mono text-[0.6rem] text-muted">
            {(s?.car ?? "BMW M4 GT3")} · best {s?.best_lap ?? "—"}
          </div>
        </div>
        {/* Link Storico sessioni: coming-soon (non attende il backend SQLite) */}
        <button
          type="button"
          disabled
          aria-disabled="true"
          title="Lo storico completo delle sessioni arriverà prossimamente"
          className="mt-1.5 flex w-full cursor-not-allowed items-center justify-between rounded-md border border-dashed border-line px-2 py-1.5 text-left"
        >
          <span className="font-mono text-[0.58rem] text-subtle">Storico sessioni</span>
          <span className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">prossimamente</span>
        </button>
      </SidebarSection>

      {/* Gigi consiglia: CTA prossima azione + ultimi consigli (FASE 4), sezione comprimibile */}
      {session && (
        <SidebarSection id="gigi" title="Gigi consiglia">
          <GigiAdvice data={session} />
        </SidebarSection>
      )}
      </div>

      {/* Footer ancorato in fondo (niente più mt-auto → niente vuoto a metà colonna) */}
      <div className="flex flex-col gap-2 border-t border-line p-4">
        {/* Pannello footer attivo: note rapide / confronto (FASE 6) */}
        {footerPanel === "notes" && <QuickNotes />}
        {footerPanel === "compare" && session && <QuickCompare data={session} />}

        {/* Azioni rapide: sostituiscono i due shortcut-icona (FASE 6) */}
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setFooterPanel((p) => (p === "compare" ? null : "compare"))}
            aria-pressed={footerPanel === "compare"}
            title="Confronta la sessione corrente con la precedente"
            className={`flex h-8 items-center justify-center gap-1 rounded-md border font-mono text-[0.58rem] transition ${
              footerPanel === "compare" ? "border-accent text-white" : "border-line text-subtle hover:border-accent hover:text-white"
            }`}
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

        {/* Presenza di Gigi */}
        <div className="flex items-center gap-2 rounded-lg border border-line bg-surface p-2">
          <GigiAvatar size={28} />
          <div className="flex-1">
            <div className="text-xs text-white">Gigi</div>
            <div className="flex items-center gap-1 font-mono text-[0.55rem] uppercase tracking-widest text-ok">
              <span className="h-1 w-1 rounded-full bg-ok" />
              online
            </div>
          </div>
        </div>

        <div className="font-mono text-[0.6rem] text-muted">v0.1.0 · v2 scaffold</div>
      </div>
    </aside>
  );
}
