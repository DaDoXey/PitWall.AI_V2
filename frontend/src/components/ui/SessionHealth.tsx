"use client";

// Modulo "Salute sessione" (megaprompt #5, FASE 3): semaforo aggregato di
// gomme/pressioni/carburante per la Sidebar. Colore = SOLO stato (verde/ambra/
// rosso), pallini piatti senza glow — coerente col design system strumentale.
import { buildHealth, HEALTH_COLOR } from "@/lib/health";
import type { SessionData } from "@/lib/telemetry";

// Corpo-only: il titolo "Salute sessione" e il badge dello stato aggregato sono
// forniti da SidebarSection (così restano visibili anche a sezione compressa).
export default function SessionHealth({ data }: { data: SessionData }) {
  const h = buildHealth(data);

  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-line bg-inset p-3">
      {h.items.map((it) => (
        <div key={it.key} className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: HEALTH_COLOR[it.state] }} />
          <span className="w-[4.75rem] shrink-0 font-mono text-[0.6rem] uppercase tracking-wider text-subtle">{it.label}</span>
          <span className="truncate font-mono text-[0.58rem] text-muted">{it.detail}</span>
        </div>
      ))}
    </div>
  );
}
