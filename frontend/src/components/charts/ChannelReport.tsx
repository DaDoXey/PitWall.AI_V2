"use client";

// Channel Report (megaprompt #6, FASE 6): unifica la tabella "dati giro-per-giro"
// (LapTable) e le "barre per canale" (LapChannelBars) in UN solo componente con
// switch Tabella ↔ Grafico — come il Channel Report reale di MoTeC i2 Pro, che è
// un'unica vista con modalità alternative, non due pannelli impilati.
// Min/max/Δ restano leggibili in entrambe le modalità (riga di sintesi in LapTable,
// header delle card in LapChannelBars). Riuso puro dei due componenti esistenti.
import { useState } from "react";
import LapTable from "@/components/charts/LapTable";
import LapChannelBars from "@/components/charts/LapChannelBars";
import type { SessionData } from "@/lib/telemetry";

type Mode = "table" | "chart";

const MODES: { id: Mode; label: string }[] = [
  { id: "table", label: "Tabella" },
  { id: "chart", label: "Grafico" },
];

export default function ChannelReport({ data }: { data: SessionData }) {
  const [mode, setMode] = useState<Mode>("table");

  return (
    <div>
      {/* Switch modalità (stesso linguaggio dei toggle esistenti: border-accent su attivo) */}
      <div className="mb-3 flex items-center gap-2">
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">Vista</span>
        {MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            onClick={() => setMode(m.id)}
            aria-pressed={mode === m.id}
            className={`rounded border px-2 py-0.5 font-mono text-[0.58rem] transition ${
              mode === m.id ? "border-accent text-white" : "border-line text-subtle hover:text-white"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {mode === "table" ? (
        <div className="pw-scroll overflow-x-auto">
          <LapTable data={data} />
        </div>
      ) : (
        <LapChannelBars data={data} />
      )}
    </div>
  );
}
