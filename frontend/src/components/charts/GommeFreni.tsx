"use client";

// Tab «Gomme e freni» della Telemetria (L4, riordinato nella #051).
//
// In alto le quattro ruote al loro posto (al centro solo le sagome delle gomme), con
// pressione, temperatura al core e freno; sotto un grafico solo, giro per giro, con il
// selettore della grandezza.
// Si legge come si ragiona al box: ruota per ruota.
//
// Le soglie hanno due pesi e si vedono diversi (decisione del 16/09/2026):
// * finestra **Kunos** (26-27 psi, 70-100 °C al core, gomme da asciutto): banda
//   neutra sui grafici, e il giudizio «fuori» arriva dal motore;
// * valori **community** (freni): linee tratteggiate con l'etichetta «community · da
//   confermare», mai un colore di allarme.
import { useState } from "react";
import { CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Riquadro } from "@/components/charts/GiriSessione";
import type { Finestra, Freni, Gomme, GiroGomme, PerRuota, Report, Ruota } from "@/lib/api";
import { giri, numero, RUOTE } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { COLORS } from "@/lib/theme";

type Campo = "pressione" | "temperatura" | "freni_max";

export default function GommeFreni({ report }: { report: Report }) {
  const gf = report.gomme_e_freni;
  const [scelta, setScelta] = useState<Campo | null>(null);
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

  // Le grandezze che hanno una serie giro per giro, nell'ordine in cui si guardano.
  const serie = gf.per_giro.length >= 2;
  const grandezze: { id: Campo; label: string; unita: string; cifre: number }[] = [
    ...(serie && g ? [{ id: "pressione" as const, label: "Pressione", unita: "psi", cifre: 1 }] : []),
    ...(serie && g && g.temperatura_media.FL !== null ? [{ id: "temperatura" as const, label: "Temperatura al core", unita: "°C", cifre: 0 }] : []),
    ...(serie && f ? [{ id: "freni_max" as const, label: "Freni, massima", unita: "°C", cifre: 0 }] : []),
  ];
  const attiva = grandezze.find((x) => x.id === scelta) ?? grandezze[0] ?? null;

  return (
    <div className="flex flex-col gap-4">
      <Riquadro titolo={g ? `Ruota per ruota · medie su ${giri(g.misurato_su_giri, "utili")}` : "Ruota per ruota"}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-[minmax(0,1fr)_7.5rem_minmax(0,1fr)]">
          <SchedaRuota ruota="FL" g={g} f={f} />
          <Sagoma g={g} />
          <SchedaRuota ruota="FR" g={g} f={f} />
          <SchedaRuota ruota="RL" g={g} f={f} />
          <SchedaRuota ruota="RR" g={g} f={f} />
        </div>
        {g && <NotaFinestra testo={g.nota_finestra} />}
        {g && <p className="mt-1 text-[0.7rem] text-muted">{g.nota_assi}</p>}
        {g?.temperatura_motec_media && g.nota_temperatura_motec && (
          <p className="mt-1 text-[0.7rem] text-muted">{g.nota_temperatura_motec.trim().replace(/[.;]?$/, ".")}</p>
        )}
      </Riquadro>

      {attiva && (
        <Riquadro
          titolo={`Giro per giro · ${attiva.label.toLowerCase()} · ${attiva.unita}`}
          azioni={
            <div className="flex flex-wrap items-center gap-3">
              <Legenda />
              {grandezze.length > 1 && (
                <div role="tablist" className="flex overflow-hidden rounded-md border border-line">
                  {grandezze.map((x) => (
                    <button
                      key={x.id}
                      role="tab"
                      aria-selected={x.id === attiva.id}
                      onClick={() => setScelta(x.id)}
                      className={`px-2.5 py-1 font-mono text-[0.62rem] uppercase tracking-widest transition ${
                        x.id === attiva.id ? "bg-raised text-white" : "text-muted hover:text-subtle"
                      }`}
                    >
                      {x.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          }
        >
          <SeriePerGiro
            per_giro={gf.per_giro}
            campo={attiva.id}
            finestra={attiva.id === "pressione" ? fp : attiva.id === "temperatura" ? ft : null}
            cifre={attiva.cifre}
            community={
              attiva.id === "freni_max" && f?.riferimento_community
                ? [
                    { y: f.riferimento_community.anteriori_max_c, testo: "ant. community" },
                    { y: f.riferimento_community.posteriori_max_c, testo: "post. community" },
                  ]
                : []
            }
          />
          {attiva.id === "freni_max" && f?.riferimento_community && (
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

// Una ruota: pressione e temperatura al core con la quota di tempo nella finestra Kunos,
// poi il freno. Il pallino ha il colore della ruota nel grafico sotto.
function SchedaRuota({ ruota, g, f }: { ruota: Ruota; g: Gomme | null; f: Freni | null }) {
  const r = RUOTE.find((x) => x.key === ruota)!;
  const fp = g?.finestra_pressione ?? null;
  const ft = g?.finestra_temperatura ?? null;
  const core = g && g.temperatura_media[ruota] !== null;
  const motec = g?.temperatura_motec_media?.[ruota] ?? null;
  return (
    <div className="rounded-lg border border-line bg-inset px-3 py-2.5">
      <div className="mb-1.5 flex items-center gap-2 font-mono text-[0.62rem] uppercase tracking-widest text-subtle">
        <span className="h-2 w-2 rounded-full" style={{ background: r.colore }} />
        {r.label}
      </div>
      <div className="flex flex-col gap-1 font-mono">
        {g && g.pressione_media[ruota] !== null && (
          <Riga
            nome="Pressione"
            valore={`${numero(g.pressione_media[ruota], 1)} psi`}
            finestra={fp}
            ruota={ruota}
            nota={`${numero(g.pressione_minima[ruota], 1)}–${numero(g.pressione_massima[ruota], 1)}`}
          />
        )}
        {core && (
          <Riga
            nome="Core"
            valore={`${numero(g.temperatura_media[ruota], 0)} °C`}
            finestra={ft}
            ruota={ruota}
            nota={`max ${numero(g.temperatura_massima[ruota], 0)}`}
          />
        )}
        {!core && motec !== null && (
          <Riga nome="Gomma" valore={`${numero(motec, 0)} °C`} finestra={null} ruota={ruota} nota="MoTeC · non giudicata" />
        )}
        {f && f.temperatura_massima[ruota] !== null && (
          <Riga
            nome="Freno"
            valore={`${numero(f.temperatura_massima[ruota], 0)} °C`}
            finestra={null}
            ruota={ruota}
            nota={`max · media ${numero(f.temperatura_media[ruota], 0)}${
              f.pastiglie_consumate_mm ? ` · pastiglie −${numero(f.pastiglie_consumate_mm[ruota], 2)} mm` : ""
            }`}
          />
        )}
      </div>
    </div>
  );
}

// Una riga della scheda: nome, valore (colorato solo se c'è una finestra), e a destra la
// barra sotto/dentro/sopra con la sua quota, oppure la nota.
function Riga({
  nome,
  valore,
  finestra,
  ruota,
  nota,
}: {
  nome: string;
  valore: string;
  finestra: Finestra | null;
  ruota: Ruota;
  nota: string;
}) {
  const fuori = finestra?.ruote_fuori.includes(ruota) ?? false;
  const colore = !finestra ? COLORS.text : fuori ? STATE.warn : STATE.ok;
  return (
    <div className="flex items-baseline gap-2 text-[0.7rem]">
      <span className="w-[4.5rem] shrink-0 text-[0.58rem] uppercase tracking-widest text-muted">{nome}</span>
      <span className="w-[4.5rem] shrink-0 text-[0.82rem]" style={{ color: colore }}>
        {valore}
      </span>
      {finestra ? (
        <span className="flex min-w-0 flex-1 items-center gap-2 text-muted">
          <BarraFinestra finestra={finestra} ruota={ruota} />
          <span className="shrink-0" style={{ color: fuori ? STATE.warn : COLORS.muted }}>
            {statoFinestra(finestra, ruota)}
          </span>
          <span className="ml-auto hidden shrink-0 text-[0.6rem] lg:inline">{nota}</span>
        </span>
      ) : (
        <span className="min-w-0 flex-1 truncate text-[0.6rem] text-muted">{nota}</span>
      )}
    </div>
  );
}

// Quota di tempo sotto / dentro / sopra la finestra: le percentuali del motore.
function BarraFinestra({ finestra, ruota }: { finestra: Finestra; ruota: Ruota }) {
  const sotto = finestra.sotto_pct[ruota] ?? 0;
  const dentro = finestra.dentro_pct[ruota] ?? 0;
  const sopra = finestra.sopra_pct[ruota] ?? 0;
  return (
    <span
      className="flex h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-raised"
      title={`sotto ${numero(sotto, 0)}% · dentro ${numero(dentro, 0)}% · sopra ${numero(sopra, 0)}%`}
    >
      <span style={{ width: `${sotto}%`, background: COLORS.blue }} />
      <span style={{ width: `${dentro}%`, background: INSTRUMENT.ink }} />
      <span style={{ width: `${sopra}%`, background: STATE.warn }} />
    </span>
  );
}

// Al centro le sole sagome delle quattro gomme (niente carrozzeria, scelta di Edoardo):
// dicono dov'è il davanti; sotto gli squilibri fra gli assi (strumento di setup per
// Kunos: si riportano, non si giudicano).
function Sagoma({ g }: { g: Gomme | null }) {
  const righe = [
    g?.squilibrio_ant_post_psi != null ? `ant−post ${segno(g.squilibrio_ant_post_psi, 1)} psi` : null,
    g?.squilibrio_sx_dx_psi != null ? `sx−dx ${segno(g.squilibrio_sx_dx_psi, 1)} psi` : null,
    g?.squilibrio_temp_ant_post_c != null ? `ant−post ${segno(g.squilibrio_temp_ant_post_c, 0)} °C` : null,
  ].filter(Boolean) as string[];
  return (
    <div className="row-span-2 hidden flex-col items-center justify-center gap-2 md:flex">
      <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">▲ davanti</span>
      <svg viewBox="0 0 60 100" className="h-24 w-auto" aria-hidden>
        {[
          [8, 10],
          [40, 10],
          [8, 62],
          [40, 62],
        ].map(([x, y]) => (
          <rect key={`${x}-${y}`} x={x} y={y} width="12" height="28" rx="3" fill="none" stroke={INSTRUMENT.track} strokeWidth={1.5} />
        ))}
      </svg>
      {righe.length > 0 && (
        <div className="flex flex-col items-center gap-0.5 font-mono text-[0.58rem] text-muted">
          {righe.map((t) => (
            <span key={t}>{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function Legenda() {
  return (
    <span className="flex flex-wrap gap-2.5 font-mono text-[0.58rem] uppercase tracking-widest text-muted">
      {RUOTE.map((r) => (
        <span key={r.key} className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: r.colore }} />
          {r.label}
        </span>
      ))}
    </span>
  );
}

// Il segno dopo l'arrotondamento: −0.04 psi è «0.0», non «−0.0».
function segno(v: number, cifre: number): string {
  const r = Number(v.toFixed(cifre));
  return `${r > 0 ? "+" : r < 0 ? "−" : ""}${Math.abs(r).toFixed(cifre)}`;
}

function statoFinestra(f: Finestra, ruota: keyof PerRuota): string {
  const sotto = f.sotto_pct[ruota] ?? 0;
  const sopra = f.sopra_pct[ruota] ?? 0;
  if (!f.ruote_fuori.includes(ruota)) return `dentro ${numero(f.dentro_pct[ruota], 0)}%`;
  return sotto >= sopra ? `sotto ${numero(sotto, 0)}%` : `sopra ${numero(sopra, 0)}%`;
}

function NotaFinestra({ testo }: { testo: string }) {
  if (!testo) return null;
  return (
    <p className="mt-3 text-[0.7rem] text-muted">
      <span className="mr-1 rounded border border-accent/40 px-1 font-mono text-[0.5rem] uppercase tracking-widest text-accent">
        Kunos
      </span>
      {testo.trim().replace(/[.;]?$/, ".")} Le percentuali sono la quota del tempo in pista sotto, dentro o sopra la
      finestra.
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
  campo: Campo;
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
