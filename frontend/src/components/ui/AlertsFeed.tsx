"use client";

// Feed avvisi rapidi (megaprompt #5, FASE 5): mostra in Sidebar le incongruenze
// rilevate dal cross-check (temp oltre limite, pressioni fuori finestra). Riusa
// lib/crosscheck (stessa logica della Telemetria). Colore = stato, niente glow.
import { buildAlerts } from "@/lib/crosscheck";
import type { SessionData } from "@/lib/telemetry";

export default function AlertsFeed({ data }: { data: SessionData }) {
  const alerts = buildAlerts(data);

  if (alerts.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-inset px-2.5 py-2 font-mono text-[0.6rem] text-ok">
        Nessun avviso · tutto in finestra
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      {alerts.map((a, i) => (
        <div key={i} className="flex items-start gap-2 rounded-md border border-line bg-inset px-2 py-1.5">
          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: a.color }} />
          <span className="font-mono text-[0.58rem] leading-snug text-subtle">{a.msg}</span>
        </div>
      ))}
    </div>
  );
}
