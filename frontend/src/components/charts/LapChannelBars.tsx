"use client";

// Channel Report GRAFICO (megaprompt di rifinitura, FASE 4): per ogni canale
// (4 temperature + 4 pressioni) mini-barre per giro. Colore = stato (soglie riusate:
// temp.limit e hot_window), griglia/baseline hairline, niente glow. È un pannello
// SEPARATO dalla tabella (le barre NON tornano nelle celle → niente sovrapposizioni).
// Solo presentazione, nessuna logica di dominio.
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";

// Mini istogramma per canale: una barra per giro, altezza ∝ valore (scala sul range
// del canale), colorata per stato. Baseline hairline. SVG a mano (leggero, coerente).
function MiniBars({ series, colorOf }: { series: number[]; colorOf: (v: number) => string }) {
  const w = 120;
  const h = 40;
  const gap = 2;
  const padY = 3;
  const min = Math.min(...series);
  const max = Math.max(...series);
  const span = max - min || 1;
  const lo = min - span * 0.3; // baseline sotto il minimo → anche il min ha un po' d'altezza
  const n = series.length;
  const bw = (w - gap * (n - 1)) / n;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="block w-full" style={{ height: "auto" }} aria-hidden="true">
      {series.map((v, i) => {
        const bh = Math.max(1.5, ((v - lo) / (max - lo)) * (h - padY));
        return (
          <rect key={i} x={+(i * (bw + gap)).toFixed(2)} y={+(h - bh).toFixed(2)} width={+bw.toFixed(2)} height={+bh.toFixed(2)} fill={colorOf(v)} />
        );
      })}
      <line x1={0} y1={h - 0.5} x2={w} y2={h - 0.5} stroke={INSTRUMENT.grid} strokeWidth={1} />
    </svg>
  );
}

export default function LapChannelBars({ data }: { data: SessionData }) {
  const limit = data.temp.limit;
  const [plo, phi] = data.pressure.hot_window;
  const tempColor = (v: number) => (v > limit ? STATE.alarm : STATE.ok);
  const pressColor = (v: number) => (v < plo || v > phi ? STATE.warn : STATE.ok);

  const groups = [
    { title: "Temperature · °C", pick: (c: Corner) => data.temp.series[c], colorOf: tempColor, fmt: (n: number) => String(Math.round(n)) },
    { title: "Pressioni · psi", pick: (c: Corner) => data.pressure.hot_series[c], colorOf: pressColor, fmt: (n: number) => n.toFixed(1) },
  ];

  return (
    <div className="flex flex-col gap-4">
      {groups.map((g) => (
        <div key={g.title}>
          <div className="mb-2 font-mono text-[0.58rem] uppercase tracking-widest text-subtle">{g.title}</div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {TYRE_SERIES.map((c) => {
              const s = g.pick(c.key);
              const mn = Math.min(...s);
              const mx = Math.max(...s);
              return (
                <div key={c.key} className="rounded-lg border border-line bg-inset p-2">
                  <div className="mb-1 flex items-baseline justify-between">
                    <span className="font-mono text-[0.6rem] text-subtle">{c.label}</span>
                    <span className="font-mono text-[0.55rem] text-muted">Δ {g.fmt(mx - mn)}</span>
                  </div>
                  <MiniBars series={s} colorOf={g.colorOf} />
                  <div className="mt-1 flex justify-between font-mono text-[0.5rem] text-muted">
                    <span>min {g.fmt(mn)}</span>
                    <span>max {g.fmt(mx)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
