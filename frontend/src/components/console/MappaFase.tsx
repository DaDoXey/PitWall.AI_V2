"use client";

// La pista della fase in onda (#060): la mappa verificata con i punti dove la fase
// perde tempo (quando la pista è agganciata alla guida) e le quattro gomme colorate
// con lo stato che dà il motore per quei giri. Senza mappa verificata, i punti in elenco.
import type { FaseDebrief } from "@/lib/api";
import { useAssets } from "@/lib/assets";
import { useSessione } from "@/lib/sessione";
import { COLORS } from "@/lib/theme";
import { COLORE_FASE } from "@/components/console/StrisciaGiri";

const COLORE_GOMMA: Record<string, { bordo: string; fondo: string; testo: string }> = {
  ok: { bordo: "#2f6b45", fondo: "#13241a", testo: "in finestra" },
  bassa: { bordo: COLORS.blue, fondo: "#0f1a2e", testo: "pressione bassa" },
  alta: { bordo: COLORS.warn, fondo: "#2a2210", testo: "pressione alta" },
  calda: { bordo: COLORS.accent, fondo: "#2a0d12", testo: "oltre i 100 °C al core" },
};
const RUOTE = [
  ["FL", "Ant.SX"],
  ["FR", "Ant.DX"],
  ["RL", "Post.SX"],
  ["RR", "Post.DX"],
] as const;

const s = (ms: number) => `+${(Math.floor(ms / 10 + 0.5) / 100).toFixed(2)} s`;

export default function MappaFase({ fase }: { fase: FaseDebrief | undefined }) {
  const { report, catalogo } = useSessione();
  const pista = report?.track ? catalogo?.tracks.find((t) => t.id === report.track) : undefined;
  const assets = useAssets("tracks", pista?.id);
  const mappa = pista?.mappa_verificata ? assets.map : undefined;
  const colore = fase ? COLORE_FASE[fase.tipo] : COLORS.accent;
  const conPunto = (fase?.punti ?? []).filter((p) => p.mappa);
  const agganciata = Boolean(report?.aggancio && report.aggancio.curve.length > 0);

  return (
    <div className="relative min-h-0 flex-1 overflow-hidden rounded-2xl bg-[#f4f1ea]">
      {mappa ? (
        <div className="absolute inset-3 flex items-center justify-center">
          <div className="relative max-h-full w-full">
            {/* eslint-disable-next-line @next/next/no-img-element -- asset statico locale */}
            <img src={mappa} alt={`Mappa di ${pista?.short_name || pista?.name}`} className="block h-auto max-h-full w-full object-contain" />
            {conPunto.map((p, i) => (
              <span
                key={p.curva}
                title={`${p.nome ?? `curva ${p.curva}`} ${s(p.perdita_ms)}`}
                className="absolute -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${p.mappa!.x * 100}%`, top: `${p.mappa!.y * 100}%`, zIndex: i === 0 ? 2 : 1 }}
              >
                <span className="relative flex h-6 w-6 items-center justify-center rounded-full border-2 border-white font-mono text-[0.65rem] font-bold text-white" style={{ background: i === 0 ? colore : "#262626" }}>
                  {i === 0 && <span className="absolute inset-0 rounded-full opacity-50 motion-safe:animate-ping" style={{ background: colore }} />}
                  <span className="relative">{i + 1}</span>
                </span>
                {/* Il nome solo sul punto peggiore, sopra il punto (sotto se è in cima alla
                    mappa): gli altri sono pallini, con il nome nel tooltip. */}
                {i === 0 && (
                  <span
                    className="absolute whitespace-nowrap rounded-md bg-[#111111] px-2 py-0.5 font-mono text-[0.62rem] text-white"
                    style={{
                      ...(p.mappa!.y < 0.15 ? { top: "calc(100% + 5px)" } : { bottom: "calc(100% + 5px)" }),
                      ...(p.mappa!.x > 0.75
                        ? { right: 0 }
                        : p.mappa!.x < 0.25
                          ? { left: 0 }
                          : { left: "50%", transform: "translateX(-50%)" }),
                    }}
                  >
                    {p.nome ?? `curva ${p.curva}`} {s(p.perdita_ms)}
                  </span>
                )}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex h-full items-center justify-center p-6 text-center font-mono text-[0.68rem] text-muted">
          {pista ? `La mappa di ${pista.short_name || pista.name} non è ancora verificata.` : "Pista non indicata."}
        </div>
      )}

      {/* Un solo riquadro, nell'angolo vuoto della mappa: le gomme della fase e, quando
          i punti non stanno sulla mappa, dove perde tempo. */}
      {fase && (fase.stato_gomme || (fase.punti.length > 0 && conPunto.length === 0)) && (
        <div className="absolute right-3 top-3 flex max-w-[15rem] flex-col gap-2 rounded-xl bg-[#111111]/95 px-3 py-2.5">
          {fase.stato_gomme && (
            <div className="flex items-center gap-2.5" aria-label="Gomme in questa fase">
              <div className="grid shrink-0 grid-cols-2 gap-1">
                {RUOTE.map(([r, nome]) => {
                  const st = COLORE_GOMMA[fase.stato_gomme![r]];
                  return (
                    <span
                      key={r}
                      title={`${nome}: ${st.testo}`}
                      className="h-5 w-3 rounded border-2"
                      style={{ borderColor: st.bordo, background: st.fondo }}
                    />
                  );
                })}
              </div>
              <span className="font-mono text-[0.58rem] leading-snug text-subtle">
                {RUOTE.filter(([r]) => fase.stato_gomme![r] !== "ok")
                  .map(([r, nome]) => `${nome} ${COLORE_GOMMA[fase.stato_gomme![r]].testo}`)
                  .join(" · ") || "tutte in finestra"}
              </span>
            </div>
          )}
          {fase.punti.length > 0 && conPunto.length === 0 && (
            <div className={`flex flex-col gap-0.5 ${fase.stato_gomme ? "border-t border-line pt-2" : ""}`}>
              {fase.punti.slice(0, 1).map((p) => (
                <span
                  key={p.curva}
                  className="font-mono text-[0.64rem] text-white"
                  title={agganciata ? undefined : "I punti vanno sulla mappa quando la pista è agganciata alla guida"}
                >
                  <span style={{ color: colore }}>Perdi di più</span> · {p.nome ?? `curva ${p.curva}`} {s(p.perdita_ms)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {mappa && <span className="absolute bottom-1.5 right-3 font-mono text-[0.5rem] text-[#8a8a8a]">mappa: Wikimedia Commons · /crediti</span>}
    </div>
  );
}
