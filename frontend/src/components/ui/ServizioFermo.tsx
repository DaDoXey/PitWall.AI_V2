"use client";

// Il servizio non risponde: detto al pilota, con un modo per riprovare (pacchetto 1.2).
// Prima cinque schermate dicevano «Backend non raggiungibile — avvia FastAPI su :8000
// (vedi README)»: un messaggio per chi sviluppa, non per chi guida.
import { SERVIZIO_FERMO } from "@/lib/errori";

export default function ServizioFermo({ onRiprova, className = "" }: { onRiprova: () => void; className?: string }) {
  return (
    <div role="alert" className={`flex flex-wrap items-center gap-3 rounded-xl border border-[#4a3a12] bg-[#17130a] px-4 py-3 ${className}`}>
      <p className="min-w-0 flex-1 text-sm text-warn">{SERVIZIO_FERMO}</p>
      <button
        type="button"
        onClick={onRiprova}
        className="shrink-0 rounded-full border border-line-strong px-4 py-1.5 text-[0.8rem] font-semibold text-white transition hover:border-accent"
      >
        Riprova
      </button>
    </div>
  );
}
