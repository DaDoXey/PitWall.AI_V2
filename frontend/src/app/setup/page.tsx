"use client";

import { useEffect, useMemo, useState } from "react";
import PageHeader from "@/components/ui/PageHeader";
import { getSetupParams } from "@/lib/api";
import {
  COLD_PRESS_WINDOW,
  formatValue,
  groupsFor,
  isPressure,
  pressureStatusColor,
  type Group,
  type Param,
  type SetupParams,
} from "@/lib/setup";
import { COLORS } from "@/lib/theme";

// Classi griglia statiche (Tailwind non accetta classi dinamiche).
const GRID_COLS: Record<Group["cols"], string> = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  4: "grid-cols-2 lg:grid-cols-4",
};

export default function SetupPage() {
  const [params, setParams] = useState<SetupParams | null>(null);
  const [values, setValues] = useState<Record<string, number>>({});
  const [active, setActive] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getSetupParams()
      .then((data: SetupParams) => {
        setParams(data);
        // Valori iniziali = default di ogni parametro.
        const init: Record<string, number> = {};
        for (const sec of Object.values(data))
          for (const [k, p] of Object.entries(sec.params)) init[k] = p.default;
        setValues(init);
        setActive(Object.keys(data)[0] ?? "");
      })
      .catch(() => setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
  }, []);

  const setVal = (key: string, v: number) => setValues((prev) => ({ ...prev, [key]: v }));

  const tabKeys = useMemo(() => (params ? Object.keys(params) : []), [params]);

  if (err)
    return (
      <div>
        <PageHeader title="Setup" subtitle="range ACC" />
        <p className="text-sm text-warn">{err}</p>
      </div>
    );
  if (!params)
    return (
      <div>
        <PageHeader title="Setup" subtitle="range ACC" />
        <p className="text-sm text-subtle">Caricamento parametri…</p>
      </div>
    );

  const section = params[active];
  const groups = section ? groupsFor(active, section) : [];

  return (
    <div>
      <PageHeader title="Setup" subtitle="BMW M4 GT3 · Monza · range ACC" />

      {/* Tab */}
      <div className="mb-5 flex flex-wrap gap-1 border-b border-line">
        {tabKeys.map((k) => {
          const on = k === active;
          return (
            <button
              key={k}
              onClick={() => setActive(k)}
              className={`-mb-px border-b-2 px-4 py-2 text-sm transition ${
                on
                  ? "border-accent text-white"
                  : "border-transparent text-subtle hover:text-white"
              }`}
            >
              {params[k].label}
            </button>
          );
        })}
      </div>

      {/* Legenda pressioni (solo tab gomme) */}
      {active === "tyres" && (
        <div className="mb-4 flex flex-wrap items-center gap-4 font-mono text-[0.6rem] text-muted">
          <span>
            <span style={{ color: COLORS.ok }}>●</span> ottimale {COLD_PRESS_WINDOW[0].toFixed(1)}–
            {COLD_PRESS_WINDOW[1].toFixed(1)} psi
          </span>
          <span>
            <span style={{ color: COLORS.warn }}>●</span> limite
          </span>
          <span>
            <span style={{ color: COLORS.accent }}>●</span> fuori finestra
          </span>
        </div>
      )}

      {/* Gruppi di slider */}
      {groups.map((g, gi) => (
        <div key={gi} className="mb-6">
          {g.title && (
            <div className="mb-3 font-mono text-[0.62rem] uppercase tracking-widest text-accent">
              {g.title}
            </div>
          )}
          <div className={`grid gap-x-6 gap-y-1 ${GRID_COLS[g.cols]}`}>
            {g.keys.map((key) => {
              const p = section.params[key];
              if (!p) return null;
              return (
                <Slider
                  key={key}
                  paramKey={key}
                  param={p}
                  value={values[key] ?? p.default}
                  onChange={(v) => setVal(key, v)}
                />
              );
            })}
          </div>

          {/* Rake informativo sotto il gruppo ride height (tab aero). */}
          {active === "aero" && g.title.startsWith("Ride height") && (
            <RakeInfo
              front={values["ride_height_front"] ?? 0}
              rear={values["ride_height_rear"] ?? 0}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────
// Slider ACC: riga nome + valore (colore-stato per pressioni) + range nativo.
// ─────────────────────────────────────────────
function Slider({
  paramKey,
  param,
  value,
  onChange,
}: {
  paramKey: string;
  param: Param;
  value: number;
  onChange: (v: number) => void;
}) {
  const valColor = isPressure(paramKey) ? pressureStatusColor(value) : COLORS.text;
  return (
    <div className="py-2" title={param.tip || undefined}>
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[0.66rem] uppercase tracking-wider text-subtle">
          {param.label}
        </span>
        <span className="font-mono text-[0.82rem] font-semibold" style={{ color: valColor }}>
          {formatValue(param, value)}
          {isPressure(paramKey) && <span className="ml-1 text-[0.7rem]">●</span>}
        </span>
      </div>
      <input
        type="range"
        min={param.min}
        max={param.max}
        step={param.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-1.5 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-line-strong accent-accent"
        aria-label={param.label}
      />
    </div>
  );
}

// Rake = ride height posteriore − anteriore (mm). Accent fuori 10–35, ok dentro.
function RakeInfo({ front, rear }: { front: number; rear: number }) {
  const rake = rear - front;
  const color = rake < 10 || rake > 35 ? COLORS.accent : COLORS.ok;
  return (
    <div className="mt-2 font-mono text-sm" style={{ color }}>
      Rake attuale: {rake.toFixed(0)} mm
    </div>
  );
}
