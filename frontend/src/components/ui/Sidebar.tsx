"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import GigiAvatar from "@/components/ui/GigiAvatar";
import { getSession } from "@/lib/api";
import { DEFAULT_CONDITIONS } from "@/lib/catalog";
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

  useEffect(() => {
    getSession()
      .then(setSession)
      .catch(() => setSession(null)); // sidebar resta usabile anche senza backend
  }, []);

  const s = session?.session;

  return (
    <aside className="flex w-60 shrink-0 flex-col gap-4 border-r border-line bg-surface p-4">
      <div className="border-b border-line pb-3">
        <div className="font-display text-lg font-bold tracking-wide">
          PITWALL<span className="text-accent">.AI</span>
        </div>
        <div className="mt-1 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted">
          Virtual Race Engineer
        </div>
      </div>

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
                {/* Indicatore attivo condiviso: scorre da una voce all'altra (layoutId). */}
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

      {/* Sessione corrente (sempre visibile) */}
      {s && (
        <div className="rounded-lg border border-l-2 border-line border-l-accent bg-inset p-3">
          <div className="mb-1 font-mono text-[0.55rem] uppercase tracking-widest text-accent">
            Sessione corrente
          </div>
          <div className="text-sm text-white">{s.track}</div>
          <div className="font-mono text-[0.62rem] text-muted">
            {s.car} · stint {s.stint.toLowerCase()}
          </div>
          <div className="font-mono text-[0.62rem] text-muted">{DEFAULT_CONDITIONS}</div>
        </div>
      )}

      {/* Sessioni recenti (per ora la sola demo; predisposta per lo storico futuro) */}
      <div>
        <div className="mb-1.5 font-mono text-[0.55rem] uppercase tracking-widest text-muted">
          Sessioni recenti
        </div>
        <div className="rounded-lg border border-line bg-surface p-2.5">
          <div className="text-[0.8rem] text-white">{s?.track ?? "Monza"}</div>
          <div className="font-mono text-[0.6rem] text-muted">
            {(s?.car ?? "BMW M4 GT3")} · best {s?.best_lap ?? "—"}
          </div>
        </div>
        <div className="mt-1 font-mono text-[0.55rem] text-muted">Storico completo · prossimamente</div>
      </div>

      {/* Presenza di Gigi */}
      <div className="mt-auto flex items-center gap-2 rounded-lg border border-line bg-surface p-2">
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
    </aside>
  );
}
