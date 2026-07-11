"use client";

// Fusione "Salute sessione" + "Avvisi" (megaprompt #6, FASE 2): un solo modulo
// a due stati. Collassato (default) = semaforo aggregato (riusa SessionHealth);
// espanso (click/tap) = in più la lista avvisi dettagliata (riusa AlertsFeed)
// nello stesso blocco, invece che in una sezione separata più in basso.
// Nessuna nuova soglia né logica di calcolo: solo fusione di presentazione.
import { useState } from "react";
import SessionHealth from "@/components/ui/SessionHealth";
import AlertsFeed from "@/components/ui/AlertsFeed";
import { buildAlerts } from "@/lib/crosscheck";
import { HEALTH_COLOR } from "@/lib/health";
import type { SessionData } from "@/lib/telemetry";

export default function HealthStatus({ data }: { data: SessionData }) {
  const [expanded, setExpanded] = useState(false);
  const count = buildAlerts(data).length;

  return (
    <div className="flex flex-col gap-1.5">
      {/* Stato collassato: il semaforo aggregato di sempre */}
      <SessionHealth data={data} />

      {/* Toggle dettaglio: il conteggio è la maniglia per la lista completa */}
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between rounded-md border border-line px-2 py-1 font-mono text-[0.55rem] uppercase tracking-widest transition hover:border-accent"
      >
        <span style={{ color: count > 0 ? HEALTH_COLOR.warn : HEALTH_COLOR.ok }}>
          {count > 0 ? `${count} avvisi attivi` : "Nessun avviso"}
        </span>
        <svg
          width="9"
          height="9"
          viewBox="0 0 10 10"
          aria-hidden
          className={`text-muted transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
        >
          <path d="M2 3.5 L5 6.5 L8 3.5" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* Stato espanso: la lista dettagliata dentro lo stesso blocco */}
      {expanded && <AlertsFeed data={data} />}
    </div>
  );
}
