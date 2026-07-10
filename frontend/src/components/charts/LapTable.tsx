"use client";

// Tabella giro-per-giro — stile "Channel Report" MoTeC (megaprompt di rifinitura, FASE 4):
// intestazioni RAGGRUPPATE (Temperature | Pressioni), righe dati per giro con numeri
// colorati per soglia (riusa temp.limit e hot_window — nessuna soglia nuova), e blocco
// di SINTESI min/max/Δ per canale in fondo. Il "modo grafico" (barre) sta nel pannello
// separato LapChannelBars. Solo presentazione, nessuna logica di dominio.
import { COLORS } from "@/lib/theme";
import { STATE } from "@/lib/instrument";
import { TYRE_SERIES, type Corner, type SessionData } from "@/lib/telemetry";

type Stat = { mn: number; mx: number; d: number };

// Cella numerica dati: numero colorato per stato; bordo sinistro sul confine di gruppo
// (prima colonna Temperature / prima colonna Pressioni) per delimitare i due blocchi.
function Cell({ value, color, groupStart }: { value: string; color: string; groupStart?: boolean }) {
  return (
    <td className={`py-2 px-3 text-right font-mono ${groupStart ? "border-l border-line" : ""}`} style={{ color }}>
      {value}
    </td>
  );
}

export default function LapTable({ data }: { data: SessionData }) {
  const limit = data.temp.limit;
  const [plo, phi] = data.pressure.hot_window;

  // Soglie riusate dal cross-check: temp oltre limite = allarme; pressione fuori finestra = warn.
  const tempColor = (v: number) => (v > limit ? STATE.alarm : STATE.ok);
  const pressColor = (v: number) => (v < plo || v > phi ? STATE.warn : STATE.ok);
  const fmtT = (n: number) => String(Math.round(n));
  const fmtP = (n: number) => n.toFixed(1);
  const fmtF = (n: number) => n.toFixed(1);

  // Sintesi per canale (min/max/Δ), stile Channel Report.
  const stat = (arr: number[]): Stat => {
    const mn = Math.min(...arr);
    const mx = Math.max(...arr);
    return { mn, mx, d: mx - mn };
  };
  const fuelS = stat(data.fuel_per_lap);
  const tempS = Object.fromEntries(TYRE_SERIES.map((c) => [c.key, stat(data.temp.series[c.key])])) as Record<Corner, Stat>;
  const pressS = Object.fromEntries(TYRE_SERIES.map((c) => [c.key, stat(data.pressure.hot_series[c.key])])) as Record<Corner, Stat>;

  const neutralColor = () => COLORS.subtle;
  const thresholdColor = (kind: "temp" | "press", v: number) => (kind === "temp" ? tempColor(v) : pressColor(v));

  // Riga di sintesi (min/max/Δ): label + fuel + 4 temp + 4 press, con selettore valore/colore.
  const summaryRow = (label: string, pick: (s: Stat) => number, color: (kind: "temp" | "press", v: number) => string) => (
    <tr key={label} className="border-t border-line">
      <td className="py-1.5 px-3 font-mono text-[0.62rem] uppercase text-muted">{label}</td>
      <td className="py-1.5 px-3 text-right font-mono text-[0.72rem]" style={{ color: COLORS.subtle }}>
        {fmtF(pick(fuelS))}
      </td>
      {TYRE_SERIES.map((c, idx) => (
        <td
          key={`t-${c.key}`}
          className={`py-1.5 px-3 text-right font-mono text-[0.72rem] ${idx === 0 ? "border-l border-line" : ""}`}
          style={{ color: color("temp", pick(tempS[c.key])) }}
        >
          {fmtT(pick(tempS[c.key]))}
        </td>
      ))}
      {TYRE_SERIES.map((c, idx) => (
        <td
          key={`p-${c.key}`}
          className={`py-1.5 px-3 text-right font-mono text-[0.72rem] ${idx === 0 ? "border-l border-line" : ""}`}
          style={{ color: color("press", pick(pressS[c.key])) }}
        >
          {fmtP(pick(pressS[c.key]))}
        </td>
      ))}
    </tr>
  );

  return (
    <table className="w-full text-sm">
      <thead>
        {/* Intestazioni di GRUPPO */}
        <tr className="font-mono text-[0.58rem] uppercase tracking-widest text-subtle">
          <th className="px-3" />
          <th className="px-3" />
          <th colSpan={4} className="border-l border-line py-1 text-center">
            Temperature · °C
          </th>
          <th colSpan={4} className="border-l border-line py-1 text-center">
            Pressioni · psi
          </th>
        </tr>
        {/* Intestazioni di COLONNA */}
        <tr className="font-mono text-[0.62rem] uppercase text-muted">
          <th className="py-2 px-3 text-left">Giro</th>
          <th className="px-3 text-right">Cons. (L)</th>
          {TYRE_SERIES.map((c, idx) => (
            <th key={c.key} className={`px-3 text-right ${idx === 0 ? "border-l border-line" : ""}`}>
              {c.label}
            </th>
          ))}
          {TYRE_SERIES.map((c, idx) => (
            <th key={`p-${c.key}`} className={`px-3 text-right ${idx === 0 ? "border-l border-line" : ""}`}>
              {c.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.laps.map((lap, i) => (
          <tr key={lap} className="border-t border-line">
            <td className="py-2 px-3 font-mono">{lap}</td>
            <Cell value={fmtF(data.fuel_per_lap[i])} color={COLORS.subtle} />
            {TYRE_SERIES.map((c, idx) => {
              const v = data.temp.series[c.key][i];
              return <Cell key={c.key} value={String(v)} color={tempColor(v)} groupStart={idx === 0} />;
            })}
            {TYRE_SERIES.map((c, idx) => {
              const v = data.pressure.hot_series[c.key][i];
              return <Cell key={`p-${c.key}`} value={fmtP(v)} color={pressColor(v)} groupStart={idx === 0} />;
            })}
          </tr>
        ))}
      </tbody>
      {/* Sintesi Channel Report: min / max / Δ per canale (max colorato per soglia) */}
      <tfoot className="border-t-2 border-line-strong">
        {summaryRow("min", (s) => s.mn, neutralColor)}
        {summaryRow("max", (s) => s.mx, thresholdColor)}
        {summaryRow("Δ", (s) => s.d, neutralColor)}
      </tfoot>
    </table>
  );
}
