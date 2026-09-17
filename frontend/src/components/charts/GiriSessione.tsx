"use client";

// Tab «Giri» della Telemetria (L4): la tabella dei giri, i settori e il delta dal
// migliore. Tutto dal report: stato del giro (di ritmo, migliore, box, invalido),
// delta e perdite per settore sono decisi dal motore.
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Report } from "@/lib/api";
import { delta, numero, secondi, tempoGiro } from "@/lib/formato";
import { INSTRUMENT, STATE } from "@/lib/instrument";
import { COLORS } from "@/lib/theme";

export default function GiriSessione({ report }: { report: Report }) {
  if (report.giri.length === 0) {
    return (
      <Riquadro titolo="Giri">
        <p className="text-sm text-subtle">
          Questa sessione non ha giri misurati: si possono analizzare il setup e il racconto, non i tempi.
        </p>
      </Riquadro>
    );
  }
  const conDelta = report.giri.filter((g) => g.delta_migliore_ms !== null);

  return (
    <div className="flex flex-col gap-4">
      <Riquadro titolo="Tempi sul giro">
        <div className="pw-scroll overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse font-mono text-[0.78rem]">
            <thead>
              <tr className="border-b border-line text-left text-[0.58rem] uppercase tracking-widest text-muted">
                <th className="py-2 pr-3">Giro</th>
                <th className="py-2 pr-3">Tempo</th>
                <th className="py-2 pr-3">S1</th>
                <th className="py-2 pr-3">S2</th>
                <th className="py-2 pr-3">S3</th>
                <th className="py-2 pr-3">Δ migliore</th>
                <th className="py-2 pr-3">Carburante</th>
                <th className="py-2">Stato</th>
              </tr>
            </thead>
            <tbody>
              {report.giri.map((g) => (
                <tr key={g.numero} className="border-b border-line/60">
                  <td className="py-1.5 pr-3 text-subtle">{g.numero}</td>
                  <td className="py-1.5 pr-3" style={{ color: g.migliore ? STATE.best : g.valido ? COLORS.text : COLORS.muted }}>
                    {tempoGiro(g.tempo_ms)}
                  </td>
                  {[0, 1, 2].map((i) => {
                    const settore = report.settori[i];
                    const valore = g.splits_ms[i];
                    const migliore = settore && valore === settore.migliore_ms;
                    return (
                      <td key={i} className="py-1.5 pr-3" style={{ color: migliore ? STATE.best : COLORS.subtle }}>
                        {valore ? (valore >= 60000 ? tempoGiro(valore) : (valore / 1000).toFixed(3)) : "—"}
                      </td>
                    );
                  })}
                  <td className="py-1.5 pr-3 text-subtle">{g.migliore ? "—" : delta(g.delta_migliore_ms)}</td>
                  <td className="py-1.5 pr-3 text-subtle">{g.carburante_usato_l !== null ? `${numero(g.carburante_usato_l, 2)} l` : "—"}</td>
                  <td className="py-1.5">
                    <span className="flex flex-wrap gap-1">
                      {g.migliore && <Stato testo="migliore" colore={STATE.best} />}
                      {!g.valido && <Stato testo="invalido" colore={STATE.alarm} />}
                      {g.in_pit && <Stato testo="box" colore={COLORS.subtle} />}
                      {g.valido && g.tempo_ms !== null && !g.di_ritmo && <Stato testo="fuori ritmo" colore={COLORS.muted} />}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[0.7rem] text-muted">
          In viola il giro e i settori migliori. «Fuori ritmo» = oltre il +10% dal migliore: contato, ma escluso da
          medie, costanza e degrado.
        </p>
      </Riquadro>

      {conDelta.length >= 2 && (
        <Riquadro titolo="Distacco dal giro migliore">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={conDelta.map((g) => ({ giro: g.numero, delta: (g.delta_migliore_ms ?? 0) / 1000, ritmo: g.di_ritmo }))} margin={{ top: 6, right: 12, bottom: 18, left: 4 }}>
              <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
              <XAxis dataKey="giro" stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} label={{ value: "Giro", position: "insideBottom", offset: -8, style: { fill: COLORS.muted, fontSize: 10 } }} />
              <YAxis stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={44} tickFormatter={(v: number) => `+${v.toFixed(1)}`} />
              <Tooltip
                contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
                labelFormatter={(l) => `Giro ${l}`}
                formatter={(v: number) => [`+${v.toFixed(3)} s`, "dal migliore"]}
              />
              <ReferenceLine y={0} stroke={COLORS.muted} />
              <Bar dataKey="delta" isAnimationActive={false}>
                {conDelta.map((g) => (
                  <Cell key={g.numero} fill={g.migliore ? STATE.best : g.di_ritmo ? INSTRUMENT.ink : INSTRUMENT.track} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Riquadro>
      )}

      <Riquadro titolo="Settori">
        {report.settori.length === 0 ? (
          <p className="text-sm text-subtle">{report.ritmo.motivo_teorico ?? "Settori non disponibili."}</p>
        ) : (
          <div className="pw-scroll overflow-x-auto">
            <table className="w-full min-w-[480px] border-collapse font-mono text-[0.78rem]">
              <thead>
                <tr className="border-b border-line text-left text-[0.58rem] uppercase tracking-widest text-muted">
                  <th className="py-2 pr-3">Settore</th>
                  <th className="py-2 pr-3">Migliore</th>
                  <th className="py-2 pr-3">Media</th>
                  <th className="py-2 pr-3">Dispersione</th>
                  <th className="py-2 pr-3">Perdita media a giro</th>
                  <th className="py-2">Nel giro migliore</th>
                </tr>
              </thead>
              <tbody>
                {report.settori.map((s) => (
                  <tr key={s.numero} className="border-b border-line/60">
                    <td className="py-1.5 pr-3 text-subtle">S{s.numero}</td>
                    <td className="py-1.5 pr-3" style={{ color: STATE.best }}>{secondi(s.migliore_ms)}</td>
                    <td className="py-1.5 pr-3 text-white">{secondi(s.media_ms)}</td>
                    <td className="py-1.5 pr-3 text-subtle">{s.deviazione_ms} ms</td>
                    <td className="py-1.5 pr-3 text-warn">{s.perdita_media_ms} ms</td>
                    <td className="py-1.5 text-subtle">{s.perdita_sul_giro_migliore_ms !== null ? `${s.perdita_sul_giro_migliore_ms} ms` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {report.ritmo.giro_teorico_ms !== null && (
              <p className="mt-2 text-[0.7rem] text-muted">
                Giro teorico {tempoGiro(report.ritmo.giro_teorico_ms)} su {report.ritmo.giri_per_teorico} giri con tutti i settori ·{" "}
                {report.ritmo.lasciato_sul_tavolo_ms} ms dal migliore.
              </p>
            )}
          </div>
        )}
      </Riquadro>
    </div>
  );
}

function Stato({ testo, colore }: { testo: string; colore: string }) {
  return (
    <span className="rounded border px-1 py-px text-[0.5rem] uppercase tracking-widest" style={{ color: colore, borderColor: `${colore}66` }}>
      {testo}
    </span>
  );
}

export function Riquadro({ titolo, children, azioni }: { titolo: string; children: React.ReactNode; azioni?: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="font-mono text-xs uppercase tracking-wider text-subtle">{titolo}</div>
        {azioni}
      </div>
      {children}
    </div>
  );
}
