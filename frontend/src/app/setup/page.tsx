"use client";

import { useEffect, useMemo, useState } from "react";
import PageHeader from "@/components/ui/PageHeader";
import {
  ApiError,
  getSession,
  getSetupParams,
  postCsvParse,
  postSetupFromImage,
  type CsvResult,
} from "@/lib/api";
import {
  CAR_LIST,
  CONDITIONS,
  DEFAULT_CAR,
  DEFAULT_CONDITIONS,
  DEFAULT_TRACK,
  TRACK_LIST,
} from "@/lib/catalog";
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

const GRID_COLS: Record<Group["cols"], string> = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  4: "grid-cols-2 lg:grid-cols-4",
};

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);

export default function SetupPage() {
  const [params, setParams] = useState<SetupParams | null>(null);
  const [values, setValues] = useState<Record<string, number>>({});
  const [active, setActive] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);
  // Parametri suggeriti da Gigi (dallo scenario di sessione): evidenziati sugli slider.
  const [suggested, setSuggested] = useState<Set<string>>(new Set());

  // Input sessione (Fase 7): default nascosto → demo pulita.
  const [showInputs, setShowInputs] = useState(false);
  const [car, setCar] = useState(DEFAULT_CAR);
  const [track, setTrack] = useState(DEFAULT_TRACK);
  const [conditions, setConditions] = useState(DEFAULT_CONDITIONS);
  const [tempAmb, setTempAmb] = useState(20);
  const [tempTrack, setTempTrack] = useState(30);

  // Refetch dei range a ogni cambio vettura/circuito: applica gli override e
  // ri-clampa i valori correnti nei nuovi range (non li azzera), come la v1.
  useEffect(() => {
    getSetupParams(car, track)
      .then((data: SetupParams) => {
        setParams(data);
        setValues((prev) => {
          const next: Record<string, number> = {};
          for (const sec of Object.values(data))
            for (const [k, p] of Object.entries(sec.params))
              next[k] = prev[k] === undefined ? p.default : clamp(prev[k], p.min, p.max);
          return next;
        });
        setActive((a) => a || Object.keys(data)[0] || "");
        setErr(null);
      })
      .catch(() => setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
  }, [car, track]);

  // Suggerimenti di Gigi: statici dallo scenario demo (/api/session). Caricati una volta.
  useEffect(() => {
    getSession()
      .then((s) => setSuggested(new Set(s.suggested_params ?? [])))
      .catch(() => setSuggested(new Set()));
  }, []);

  const setVal = (key: string, v: number) => setValues((prev) => ({ ...prev, [key]: v }));

  // Ricerca la definizione di un parametro per chiave (per l'apply della vision).
  const findParam = (key: string): Param | undefined => {
    if (!params) return undefined;
    for (const sec of Object.values(params)) if (sec.params[key]) return sec.params[key];
    return undefined;
  };

  const applyVisionParams = (vp: Record<string, number>): number => {
    let applied = 0;
    setValues((prev) => {
      const next = { ...prev };
      for (const [k, raw] of Object.entries(vp || {})) {
        const p = findParam(k);
        const num = Number(raw);
        if (!p || Number.isNaN(num)) continue;
        next[k] = clamp(num, p.min, p.max);
        applied++;
      }
      return next;
    });
    return applied;
  };

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

  // Parametri suggeriti da Gigi risolti in {chiave,label,sezione} per il banner,
  // e helper per il pallino sui tab che contengono almeno un suggerimento.
  const suggestedItems = suggested.size
    ? Object.entries(params).flatMap(([sk, sec]) =>
        Object.entries(sec.params)
          .filter(([k]) => suggested.has(k))
          .map(([k, p]) => ({ key: k, label: p.label, section: sk })),
      )
    : [];
  const sectionHasSuggested = (sk: string) =>
    Object.keys(params[sk].params).some((k) => suggested.has(k));

  return (
    <div>
      <PageHeader title="Setup" subtitle={`${car} · ${track} · range ACC`} />

      {/* Banner suggerimenti di Gigi (collega Console↔Setup) */}
      {suggestedItems.length > 0 && (
        <div className="mb-4 rounded-xl border border-accent/30 bg-accent/[0.06] p-4">
          <div className="mb-2 flex items-center gap-2 font-mono text-[0.6rem] uppercase tracking-widest text-accent">
            🔧 Suggeriti da Gigi
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedItems.map((it) => (
              <button
                key={it.key}
                onClick={() => setActive(it.section)}
                title={`Vai al tab ${params[it.section].label}`}
                className="rounded-md border border-accent/40 bg-accent/10 px-2.5 py-1 text-[0.78rem] text-white transition hover:border-accent"
              >
                {it.label}
              </button>
            ))}
          </div>
          <div className="mt-2 text-[0.7rem] text-muted">
            Parametri evidenziati dallo scenario analizzato nella Console.
          </div>
        </div>
      )}

      {/* Toggle input sessione */}
      <label className="mb-4 flex w-fit cursor-pointer items-center gap-2 text-sm text-subtle">
        <input
          type="checkbox"
          checked={showInputs}
          onChange={(e) => setShowInputs(e.target.checked)}
          className="h-4 w-4 accent-accent"
        />
        Input sessione (selettori auto/pista · upload CSV/screenshot)
      </label>

      {showInputs && (
        <SessionInputs
          car={car}
          track={track}
          conditions={conditions}
          tempAmb={tempAmb}
          tempTrack={tempTrack}
          onCar={setCar}
          onTrack={setTrack}
          onConditions={setConditions}
          onTempAmb={setTempAmb}
          onTempTrack={setTempTrack}
          onApplyVision={applyVisionParams}
        />
      )}

      {/* Tab */}
      <div className="mb-5 flex flex-wrap gap-1 border-b border-line">
        {tabKeys.map((k) => {
          const on = k === active;
          return (
            <button
              key={k}
              onClick={() => setActive(k)}
              className={`-mb-px flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm transition ${
                on ? "border-accent text-white" : "border-transparent text-subtle hover:text-white"
              }`}
            >
              {params[k].label}
              {sectionHasSuggested(k) && (
                <span
                  className="h-1.5 w-1.5 rounded-full bg-accent"
                  title="Contiene parametri suggeriti da Gigi"
                />
              )}
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
                  suggested={suggested.has(key)}
                  onChange={(v) => setVal(key, v)}
                />
              );
            })}
          </div>

          {active === "aero" && g.title.startsWith("Ride height") && (
            <RakeInfo front={values["ride_height_front"] ?? 0} rear={values["ride_height_rear"] ?? 0} />
          )}
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────
// Pannello input sessione (Fase 7)
// ─────────────────────────────────────────────
function SessionInputs({
  car,
  track,
  conditions,
  tempAmb,
  tempTrack,
  onCar,
  onTrack,
  onConditions,
  onTempAmb,
  onTempTrack,
  onApplyVision,
}: {
  car: string;
  track: string;
  conditions: string;
  tempAmb: number;
  tempTrack: number;
  onCar: (v: string) => void;
  onTrack: (v: string) => void;
  onConditions: (v: string) => void;
  onTempAmb: (v: number) => void;
  onTempTrack: (v: number) => void;
  onApplyVision: (vp: Record<string, number>) => number;
}) {
  return (
    <div className="mb-6 rounded-xl border border-line bg-surface p-4">
      <div className="mb-3 font-mono text-[0.62rem] uppercase tracking-widest text-accent">
        Configurazione sessione
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Select label="Auto" value={car} options={CAR_LIST} onChange={onCar} />
        <Select label="Tracciato" value={track} options={TRACK_LIST} onChange={onTrack} />
        <Select label="Condizioni" value={conditions} options={CONDITIONS} onChange={onConditions} />
      </div>

      <div className="mt-3 grid grid-cols-1 gap-x-6 sm:grid-cols-2">
        <MiniSlider label="Temp. Ambiente" value={tempAmb} min={0} max={50} unit="°C" onChange={onTempAmb} />
        <MiniSlider label="Temp. Pista" value={tempTrack} min={0} max={60} unit="°C" onChange={onTempTrack} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 border-t border-line pt-4 md:grid-cols-2">
        <CsvUpload />
        <ScreenshotUpload onApplyVision={onApplyVision} />
      </div>
    </div>
  );
}

function CsvUpload() {
  const [result, setResult] = useState<CsvResult | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setMsg(null);
    setResult(null);
    try {
      const r = await postCsvParse(file);
      setResult(r);
      setMsg({ ok: true, text: `CSV letto: ${r.laps_count} giri · consumo medio ${r.fuel_cons_avg.toFixed(2)} L/giro` });
    } catch (err) {
      const text = err instanceof ApiError ? err.message : "Impossibile leggere il CSV.";
      setMsg({ ok: false, text });
    }
  }

  return (
    <div>
      <div className="mb-1.5 font-mono text-[0.6rem] uppercase tracking-widest text-muted">
        Carica CSV sessione
      </div>
      <input
        type="file"
        accept=".csv"
        onChange={onFile}
        className="block w-full text-xs text-subtle file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line-strong file:bg-raised file:px-3 file:py-1.5 file:text-xs file:text-white hover:file:border-accent"
      />
      {msg && (
        <p className={`mt-2 text-xs ${msg.ok ? "text-ok" : "text-warn"}`}>{msg.text}</p>
      )}
      {result && result.warnings.length > 0 && (
        <p className="mt-1 text-[0.7rem] text-muted">{result.warnings.length} avvisi di range nei dati.</p>
      )}
    </div>
  );
}

function ScreenshotUpload({ onApplyVision }: { onApplyVision: (vp: Record<string, number>) => number }) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [vparams, setVparams] = useState<Record<string, number> | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function read() {
    if (!file) return;
    setBusy(true);
    setMsg(null);
    setSummary(null);
    setVparams(null);
    try {
      const r = await postSetupFromImage(file);
      setSummary(r.summary);
      setVparams(r.params);
      setMsg({ ok: true, text: `Riconosciuti ${Object.keys(r.params).length} parametri.` });
    } catch (err) {
      const text =
        err instanceof ApiError && err.status === 503
          ? "🔒 Richiede la chiave server (in demo non è attiva)."
          : err instanceof ApiError
            ? err.message
            : "Lettura screenshot fallita.";
      setMsg({ ok: false, text });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="mb-1.5 font-mono text-[0.6rem] uppercase tracking-widest text-muted">
        Screenshot setup ACC
      </div>
      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="block w-full text-xs text-subtle file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line-strong file:bg-raised file:px-3 file:py-1.5 file:text-xs file:text-white hover:file:border-accent"
      />
      <button
        onClick={read}
        disabled={!file || busy}
        className="mt-2 rounded-md border border-line-strong bg-raised px-3 py-1.5 text-xs text-white transition hover:border-accent disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Analisi…" : "Leggi parametri dallo screenshot"}
      </button>
      {msg && <p className={`mt-2 text-xs ${msg.ok ? "text-ok" : "text-warn"}`}>{msg.text}</p>}
      {summary && (
        <pre className="mt-2 whitespace-pre-wrap font-mono text-[0.7rem] text-subtle">{summary}</pre>
      )}
      {vparams && Object.keys(vparams).length > 0 && (
        <button
          onClick={() => {
            const n = onApplyVision(vparams);
            setMsg({ ok: true, text: `${n} parametri applicati agli slider.` });
          }}
          className="mt-2 rounded-md bg-accent px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-accent-hover"
        >
          Usa questi parametri negli slider
        </button>
      )}
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-line bg-inset px-3 py-2 text-sm text-white focus:border-accent focus:outline-none"
      >
        {options.map((o) => (
          <option key={o} value={o} className="bg-inset">
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

function MiniSlider({
  label,
  value,
  min,
  max,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="py-2">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[0.66rem] uppercase tracking-wider text-subtle">{label}</span>
        <span className="font-mono text-[0.82rem] font-semibold text-white">
          {value} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-1.5 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-line-strong accent-accent"
        aria-label={label}
      />
    </div>
  );
}

// ─────────────────────────────────────────────
// Slider ACC + Rake (invariati)
// ─────────────────────────────────────────────
function Slider({
  paramKey,
  param,
  value,
  suggested,
  onChange,
}: {
  paramKey: string;
  param: Param;
  value: number;
  suggested?: boolean;
  onChange: (v: number) => void;
}) {
  // Pressioni: colore-stato vs finestra. Altri suggeriti da Gigi: valore accent.
  const valColor = isPressure(paramKey)
    ? pressureStatusColor(value)
    : suggested
      ? COLORS.accent
      : COLORS.text;
  return (
    <div
      className={`py-2 ${suggested ? "border-l-2 border-accent pl-2.5" : ""}`}
      title={param.tip || undefined}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="flex items-center gap-1.5 font-mono text-[0.66rem] uppercase tracking-wider text-subtle">
          {param.label}
          {suggested && (
            <span className="rounded border border-accent px-1 py-px text-[0.5rem] font-semibold not-italic text-accent">
              GIGI
            </span>
          )}
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

function RakeInfo({ front, rear }: { front: number; rear: number }) {
  const rake = rear - front;
  const color = rake < 10 || rake > 35 ? COLORS.accent : COLORS.ok;
  return (
    <div className="mt-2 font-mono text-sm" style={{ color }}>
      Rake attuale: {rake.toFixed(0)} mm
    </div>
  );
}
