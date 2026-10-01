"use client";

// «La sessione» nella colonna di sinistra, solo sulla Engineer Console (#060, scelta di
// Edoardo dell'01/10): lì la pista è già al centro, quindi al posto di PannelloPista
// stanno i numeri della sessione aperta — giro migliore, media e, sotto, i giri di ritmo
// uno per uno con il tempo e lo scarto (sulla striscia della Console sono solo barre).
// Niente mappa e niente curve: nessun doppione.
//
// Come PannelloPista, lo spazio lo decide lo schermo (ResizeObserver): entrano tanti
// giri quanti ce ne stanno e si spartiscono l'altezza, così il riquadro arriva in fondo
// alla colonna senza vuoti sotto.
import { useEffect, useState } from "react";
import { getDebrief, type Debrief } from "@/lib/api";
import { tempoGiro } from "@/lib/formato";
import { useSessione } from "@/lib/sessione";
import { COLORS } from "@/lib/theme";

const FISSO = 96; // titoli, margini, i due riquadri di riepilogo (misurato a schermo)
const RIGA_MINIMA = 19; // px: sotto questa altezza un giro non entra

export default function PannelloSessione() {
  const { idSessione, report } = useSessione();
  const [zona, setZona] = useState<HTMLDivElement | null>(null);
  const [altezza, setAltezza] = useState(0);
  // I giri di ritmo sono quelli del debrief (gli stessi della striscia della Console).
  const [giri, setGiri] = useState<Debrief["giri"]>([]);

  useEffect(() => {
    if (!zona) return;
    const osserva = new ResizeObserver(([voce]) => setAltezza(voce.contentRect.height));
    osserva.observe(zona);
    return () => osserva.disconnect();
  }, [zona]);

  useEffect(() => {
    setGiri([]);
    if (!idSessione) return;
    let vivo = true;
    getDebrief(idSessione)
      .then((d) => vivo && setGiri(d.giri))
      .catch(() => undefined);
    return () => {
      vivo = false;
    };
  }, [idSessione]);

  const migliore = report?.ritmo.miglior_giro_ms ?? null;
  const media = report?.ritmo.media_ms ?? null;
  const quanti = Math.max(0, Math.floor((altezza - FISSO) / RIGA_MINIMA));
  const mostrati = giri.slice(0, quanti);

  return (
    // Nessun margine sul contenitore: vuoto deve valere zero pixel, o ruba spazio alla
    // navigazione sugli schermi bassi.
    <div ref={setZona} className="min-h-0 flex-1 basis-0 overflow-hidden">
      {report && migliore != null && altezza >= 70 && (
        <div className="flex h-full flex-col gap-2 px-4 pb-3 pt-2">
          <span className="px-1 font-mono text-[0.58rem] uppercase tracking-[0.18em] text-muted">La sessione</span>
          <div className="grid shrink-0 grid-cols-2 gap-2">
            <div className="flex flex-col gap-0.5 rounded-lg border border-line px-2.5 py-1.5">
              <span className="font-mono text-[0.52rem] uppercase tracking-widest text-muted">Migliore</span>
              <span className="font-mono text-[0.8rem] font-semibold" style={{ color: COLORS.best }}>
                {tempoGiro(migliore)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5 rounded-lg border border-line px-2.5 py-1.5">
              <span className="font-mono text-[0.52rem] uppercase tracking-widest text-muted">Media</span>
              <span className="font-mono text-[0.8rem] font-semibold text-white">{tempoGiro(media)}</span>
            </div>
          </div>

          {mostrati.length > 0 && (
            <>
              <span className="mt-1 px-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                Giri di ritmo · {giri.length}
              </span>
              <div className="flex min-h-0 flex-1 flex-col">
                {mostrati.map((g) => (
                  <div
                    key={g.numero}
                    className="flex min-h-0 flex-1 items-center gap-2 border-t border-line px-1 font-mono text-[0.7rem] first:border-t-0"
                  >
                    <span className="w-6 shrink-0 text-muted">G{g.numero}</span>
                    <span className="flex-1" style={{ color: g.migliore ? COLORS.best : COLORS.text }}>
                      {tempoGiro(g.tempo_ms)}
                    </span>
                    <span className="shrink-0 text-[0.64rem]" style={{ color: g.migliore ? COLORS.best : COLORS.subtle }}>
                      {g.migliore ? "migliore" : `+${(g.delta_ms / 1000).toFixed(3)}`}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
