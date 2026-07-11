"use client";

// Mini "values window" (megaprompt #5, FASE 6): 3 valori chiave di sessione in
// formato strumento (numeri monospace). Onestà dei dati:
//  - Giro: numero giri della sessione (dato reale).
//  - Δ giro: delta del TEMPO sul giro → i tempi arrivano in FASE 7 (placeholder ora).
//  - Consumo: consumo medio/giro (dato reale). Il "residuo" non è modellato nella
//    demo — non c'è capacità serbatoio — quindi mostriamo il consumo, non il residuo.
import type { SessionData } from "@/lib/telemetry";

function Cell({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg border border-line bg-inset px-2 py-1.5 text-center">
      <div className="font-mono text-[0.5rem] uppercase tracking-widest text-muted">{label}</div>
      <div className="font-mono text-sm text-white">{value}</div>
      <div className="font-mono text-[0.5rem] text-muted">{sub}</div>
    </div>
  );
}

export default function MiniValues({ data }: { data: SessionData }) {
  const s = data.session;
  return (
    <div className="grid grid-cols-3 gap-2">
      <Cell label="Giro" value={String(s.laps)} sub={`di ${s.laps}`} />
      <Cell label="Δ giro" value="—" sub="in arrivo" />
      <Cell label="Consumo" value={s.fuel_avg_per_lap.toFixed(1)} sub="L/giro" />
    </div>
  );
}
