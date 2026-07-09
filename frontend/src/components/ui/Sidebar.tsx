"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const NAV = [
  { href: "/", label: "Dashboard", icon: "▦" },
  { href: "/console", label: "Engineer Console", icon: "🎧" },
  { href: "/telemetry", label: "Telemetria", icon: "📈" },
  { href: "/setup", label: "Setup", icon: "🔧" },
];

export default function Sidebar() {
  const path = usePathname();
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
      <div className="mt-auto font-mono text-[0.6rem] text-muted">v0.1.0 · v2 scaffold</div>
    </aside>
  );
}
