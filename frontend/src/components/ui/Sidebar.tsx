"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

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
            <Link
              key={n.href}
              href={n.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                active ? "bg-accent text-white" : "text-subtle hover:bg-raised"
              }`}
            >
              <span>{n.icon}</span>
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto font-mono text-[0.6rem] text-muted">v0.1.0 · v2 scaffold</div>
    </aside>
  );
}
