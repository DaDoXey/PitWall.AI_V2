"use client";

// Tab «Gomme e freni» della Telemetria (L4).
//
// Le soglie hanno due pesi e si vedono diversi (decisione del 16/09/2026):
// * finestra **Kunos** (26-27 psi, 70-100 °C al core, gomme da asciutto): banda
//   neutra sui grafici, e il giudizio «fuori» arriva dal motore;
// * valori **community** (freni): linee tratteggiate con l'etichetta «community · da
//   confermare», mai un colore di allarme.
import { CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PressureGauge from "@/components/charts/PressureGauge";
import { Riquadro } from "@/components/charts/GiriSessione";
import type { Finestra, GiroGomme, PerRuota, Report } from "@/lib/api";
import { numero, RUOTE } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { COLORS } from "@/lib/theme";

export default function GommeFreni({ report }: { report: Report }) {
  const gf = report.gomme_e_freni;
  if (!gf || (!gf.gomme && !gf.freni)) {
    return (
      <Riquadro titolo="Gomme e freni">
        <p className="text-sm text-subtle">
          {report.ha_canali
            ? "Gomme e freni non registrati in questa sessione."
            : "Pressioni, temperature e freni arrivano solo dalla telemetria registrata su PC. Per questa sessione il motore non li vede: il verdetto lo dichiara invece di stimarli."}
        </p>
      </Riquadro>
    );
  }
  const g = gf.gomme;
  const f = gf.freni;
  const fp = g?.finestra_pressione ?? null;
  const ft = g?.finestra_temperatura ?? null;

  return (
    <div className="flex flex-col gap-4">
      {g && (
        <Riquadro titolo={`Pressioni in pista · media su ${g.misurato_su_giri} giri utili`}>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {RUOTE.map((r) => {
              const valore = g.pressione_media[r.key];
              if (valore === null) return null;
              const fuori = fp?.ruote_fuori.includes(r.key) ?? false;
              return (
                <div key={r.key} className="rounded-xl border border-line bg-inset p-3">
                  <PressureGauge
                    label={r.label}
                    value={valore}
                    window={fp ? [fp.min, fp.max] : null}
                    fuori={fuori}
                    stato={fp ? statoFinestra(fp, r.key) : "nessuna finestra"}
                  />
                  <div className="mt-1 text-center font-mono text-[0.58rem] text-muted">
                    min {numero(g.pressione_minima[r.key], 1)} · max {numero(g.pressione_massima[r.key], 1)}
                  </div>
                </div>
              );
            })}
          </div>
          <NotaFinestra testo={g.nota_finestra} />
          <p className="mt-1 text-[0.7rem] text-muted">{g.nota_assi}</p>
        </Riquadro>
      )}

      {g && gf.per_giro.length >= 2 && (
        <Riquadro titolo="Pressioni giro per giro · psi">
          <SeriePerGiro per_giro={gf.per_giro} campo="pressione" finestra={fp} cifre={1} />
        </Riquadro>
      )}

      {g && gf.per_giro.length >= 2 && g.temperatura_media.FL !== null && (
        <Riquadro titolo="Temperatura al core giro per giro · °C">
          <SeriePerGiro per_giro={gf.per_giro} campo="temperatura" finestra={ft} cifre={0} />
          {ft && <BarreFinestra finestra={ft} />}
        </Riquadro>
      )}

      {f && (
        <Riquadro titolo="Freni">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {RUOTE.map((r) => (
              <div key={r.key} className="rounded-lg border border-line bg-inset p-3">
                <div className="font-mono text-[0.6rem] uppercase tracking-widest text-subtle">{r.label}</div>
                <div className="mt-1 font-mono text-lg text-white">{numero(f.temperatura_massima[r.key], 0)} °C</div>
                <div className="font-mono text-[0.6rem] text-muted">massima · media {numero(f.temperatura_media[r.key], 0)} °C</div>
                {f.pastiglie_consumate_mm && (
                  <div className="mt-1 font-mono text-[0.6rem] text-muted">
                    pastiglie −{numero(f.pastiglie_consumate_mm[r.key], 2)} mm
                  </div>
                )}
              </div>
            ))}
          </div>
          {gf.per_giro.length >= 2 && (
            <div className="mt-4">
              <div className="mb-1 pl-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">Massima per giro · °C</div>
              <SeriePerGiro
                per_giro={gf.per_giro}
                campo="freni_max"
                finestra={null}
                cifre={0}
                community={
                  f.riferimento_community
                    ? [
                        { y: f.riferimento_community.anteriori_max_c, testo: "ant. community" },
                        { y: f.riferimento_community.posteriori_max_c, testo: "post. community" },
                      ]
                    : []
                }
              />
            </div>
          )}
          {f.riferimento_community && (
            <p className="mt-2 text-[0.7rem] text-muted">
              <span className="mr-1 rounded border border-line-strong px-1 font-mono text-[0.5rem] uppercase tracking-widest">
                community · da confermare
              </span>
              Riferimenti che circolano fra i piloti (ant. ≤{f.riferimento_community.anteriori_max_c} °C, post. ≤
              {f.riferimento_community.posteriori_max_c} °C): Kunos non pubblica una finestra per i freni.{" "}
              {f.riferimento_community.limiti}
            </p>
          )}
        </Riquadro>
      )}
    </div>
  );
}

function statoFinestra(f: Finestra, ruota: keyof PerRuota): string {
  const sotto = f.sotto_pct[ruota] ?? 0;
  const sopra = f.sopra_pct[ruota] ?? 0;
  if (!f.ruote_fuori.includes(ruota)) return `dentro ${numero(f.dentro_pct[ruota], 0)}% del tempo`;
  return sotto >= sopra ? `sotto ${numero(sotto, 0)}% del tempo` : `sopra ${numero(sopra, 0)}% del tempo`;
}

function NotaFinestra({ testo }: { testo: string }) {
  if (!testo) return null;
  return (
    <p className="mt-3 text-[0.7rem] text-muted">
      <span className="mr-1 rounded border border-accent/40 px-1 font-mono text-[0.5rem] uppercase tracking-widest text-accent">
        Kunos
      </span>
      {testo}
    </p>
  );
}

function SeriePerGiro({
  per_giro,
  campo,
  finestra,
  cifre,
  community = [],
}: {
  per_giro: GiroGomme[];
  campo: "pressione" | "temperatura" | "freni_max";
  finestra: Finestra | null;
  cifre: number;
  community?: { y: number; testo: string }[];
}) {
  const righe = per_giro.map((g) => ({ giro: g.giro, ...g[campo] }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={righe} margin={{ top: 8, right: 16, bottom: 18, left: 4 }}>
        <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
        <XAxis dataKey="giro" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} label={{ value: "Giro", position: "insideBottom", offset: -8, style: { fill: COLORS.muted, fontSize: 10 } }} />
        <YAxis domain={["auto", "auto"]} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={44} tickFormatter={(v: number) => v.toFixed(cifre)} />
        <Tooltip
          contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
          labelFormatter={(l) => `Giro ${l}`}
          formatter={(v: number, nome: string) => [v?.toFixed(cifre), RUOTE.find((r) => r.key === nome)?.label ?? nome]}
        />
        {finestra && (
          <ReferenceArea
            y1={finestra.min}
            y2={finestra.max}
            fill={INSTRUMENT.track}
            fillOpacity={0.35}
            label={{ value: `Kunos ${finestra.min}–${finestra.max}`, position: "insideTopRight", fill: COLORS.muted, fontSize: 9 }}
          />
        )}
        {community.map((c) => (
          <ReferenceLine key={c.testo} y={c.y} stroke={COLORS.muted} strokeDasharray="2 4" label={{ value: c.testo, position: "insideTopLeft", fill: COLORS.muted, fontSize: 9 }} />
        ))}
        {RUOTE.map((r) => (
          <Line key={r.key} type="monotone" dataKey={r.key} stroke={r.colore} strokeWidth={1.8} dot={{ r: 2, fill: r.colore, strokeWidth: 0 }} isAnimationActive={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// Quota di tempo sotto / dentro / sopra la finestra, per ruota: le percentuali del motore.
function BarreFinestra({ finestra }: { finestra: Finestra }) {
  return (
    <div className="mt-3 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
      {RUOTE.map((r) => {
        const sotto = finestra.sotto_pct[r.key] ?? 0;
        const dentro = finestra.dentro_pct[r.key] ?? 0;
        const sopra = finestra.sopra_pct[r.key] ?? 0;
        return (
          <div key={r.key} className="flex items-center gap-2 font-mono text-[0.6rem] text-muted">
            <span className="w-14 shrink-0">{r.label}</span>
            <span className="flex h-2 flex-1 overflow-hidden rounded-full bg-inset" title={`sotto ${sotto}% · dentro ${dentro}% · sopra ${sopra}%`}>
              <span style={{ width: `${sotto}%`, background: COLORS.blue }} />
              <span style={{ width: `${dentro}%`, background: INSTRUMENT.track }} />
              <span style={{ width: `${sopra}%`, background: finestra.ruote_fuori.includes(r.key) ? STATE.warn : INSTRUMENT.ink }} />
            </span>
            <span className="w-16 shrink-0 text-right">{numero(dentro, 0)}% dentro</span>
          </div>
        );
      })}
    </div>
  );
}
