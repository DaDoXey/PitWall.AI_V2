"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { CarCard, TrackCard } from "@/components/ui/SessionBriefing";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import {
  ApiError,
  getCatalog,
  getSession,
  getSetupParams,
  postCsvParse,
  postSetupFromImage,
  type CsvResult,
} from "@/lib/api";
import {
  CAR_LIST_FALLBACK,
  CONDITIONS,
  DEFAULT_CAR,
  DEFAULT_CONDITIONS,
  DEFAULT_TRACK,
  TRACK_LIST_FALLBACK,
} from "@/lib/catalog";
import {
  COLD_PRESS_WINDOW,
  formatValue,
  GIGI_TARGETS,
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
  // Parametro da portare a schermo dopo il cambio tab (click su un chip suggerito):
  // lo slider monta con un piccolo ritardo (AnimatePresence mode="wait") → si
  // riprova finché l'elemento non esiste, con deadline di sicurezza.
  const [scrollTo, setScrollTo] = useState<string | null>(null);
  useEffect(() => {
    if (!scrollTo) return;
    const poll = setInterval(() => {
      const el = document.getElementById(`param-${scrollTo}`);
      if (!el) return;
      clearInterval(poll);
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      setScrollTo(null);
    }, 100);
    const deadline = setTimeout(() => {
      clearInterval(poll);
      setScrollTo(null);
    }, 1500);
    return () => {
      clearInterval(poll);
      clearTimeout(deadline);
    };
  }, [scrollTo]);

  // Input sessione (Fase 7): default nascosto → demo pulita.
  const [showInputs, setShowInputs] = useState(false);
  const [car, setCar] = useState(DEFAULT_CAR);
  const [track, setTrack] = useState(DEFAULT_TRACK);
  const [conditions, setConditions] = useState(DEFAULT_CONDITIONS);
  const [tempAmb, setTempAmb] = useState(20);
  const [tempTrack, setTempTrack] = useState(30);

  // Catalogo ACC completo dal backend (31 vetture, 25 circuiti). Se la
  // chiamata fallisce restano le liste storiche: i selettori non si svuotano.
  const [carOptions, setCarOptions] = useState<SelectOption[]>(() =>
    CAR_LIST_FALLBACK.map((value) => ({ value })),
  );
  const [trackOptions, setTrackOptions] = useState<SelectOption[]>(() =>
    TRACK_LIST_FALLBACK.map((value) => ({ value })),
  );

  useEffect(() => {
    let alive = true;
    getCatalog()
      .then((cat) => {
        if (!alive) return;
        // `badge` = pacchetto DLC: dice perché una vettura potrebbe non essere
        // installata, senza nasconderla dalla lista.
        setCarOptions(
          cat.cars.map((c) => ({
            value: c.display_name,
            badge: c.dlc ? "DLC" : undefined,
          })),
        );
        setTrackOptions(
          cat.tracks.map((t) => ({
            // short_name ("Monza"), non il nome ufficiale: coerente col resto
            // dell'app e leggibile nel selettore. Il backend risolve entrambi.
            value: t.short_name || t.name,
            badge: t.dlc ? "DLC" : undefined,
          })),
        );
      })
      .catch(() => {
        /* backend giù: restano le liste di fallback già impostate */
      });
    return () => {
      alive = false;
    };
  }, []);

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
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
          className="mb-4 rounded-xl border border-accent/30 bg-accent/[0.06] p-4"
        >
          <div className="mb-2 flex items-center gap-2 font-mono text-[0.6rem] uppercase tracking-widest text-accent">
            🔧 Suggeriti da Gigi
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedItems.map((it) => {
              const target = GIGI_TARGETS[it.key];
              const p = findParam(it.key);
              return (
                <button
                  key={it.key}
                  onClick={() => {
                    // Applica il consiglio di Gigi e porta lo slider a schermo
                    // (prima: solo cambio tab, poi scroll e valore a mano).
                    setActive(it.section);
                    if (target !== undefined && p) setVal(it.key, clamp(target, p.min, p.max));
                    setScrollTo(it.key);
                  }}
                  title={
                    target !== undefined && p
                      ? `Applica ${formatValue(p, target)} e vai al parametro`
                      : `Vai al tab ${params[it.section].label}`
                  }
                  className="rounded-md border border-accent/40 bg-accent/10 px-2.5 py-1 text-[0.78rem] text-white transition hover:border-accent"
                >
                  {it.label}
                  {target !== undefined && p && (
                    <span className="ml-1.5 font-mono text-[0.68rem] text-accent">→ {formatValue(p, target)}</span>
                  )}
                </button>
              );
            })}
          </div>
          <div className="mt-2 text-[0.7rem] text-muted">
            Un click applica il valore consigliato da Gigi e porta al parametro (tacca rossa sullo slider).
          </div>
        </motion.div>
      )}

      {/* Toggle input sessione */}
      <div className="mb-4 flex w-fit items-center gap-2.5 text-sm text-subtle">
        <Toggle checked={showInputs} onChange={setShowInputs} label="Mostra input sessione" />
        <span>Input sessione (selettori auto/pista · upload CSV/screenshot)</span>
      </div>

      {showInputs && (
        <SessionInputs
          car={car}
          track={track}
          conditions={conditions}
          tempAmb={tempAmb}
          tempTrack={tempTrack}
          carOptions={carOptions}
          trackOptions={trackOptions}
          onCar={setCar}
          onTrack={setTrack}
          onConditions={setConditions}
          onTempAmb={setTempAmb}
          onTempTrack={setTempTrack}
          onApplyVision={applyVisionParams}
        />
      )}

      {/* Contesto della combinazione scelta: qui il "focus setup" del tracciato
          e l'indole della vettura sono azionabili — si leggono mentre si
          muovono gli slider. Compaiono con i selettori aperti. */}
      {showInputs && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2"
        >
          <TrackCard track={track} />
          <CarCard car={car} />
        </motion.div>
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

      {/* Gruppi di slider — transizione morbida al cambio tab (AnimatePresence) */}
      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}
        >
          {groups.map((g, gi) => (
            <motion.div key={gi} variants={fadeInUp} className="mb-6">
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
                      gigiTarget={suggested.has(key) ? GIGI_TARGETS[key] : undefined}
                      onChange={(v) => setVal(key, v)}
                    />
                  );
                })}
              </div>

              {active === "aero" && g.title.startsWith("Ride height") && (
                <RakeInfo front={values["ride_height_front"] ?? 0} rear={values["ride_height_rear"] ?? 0} />
              )}
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>
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
  carOptions,
  trackOptions,
}: {
  car: string;
  track: string;
  conditions: string;
  tempAmb: number;
  tempTrack: number;
  carOptions: SelectOption[];
  trackOptions: SelectOption[];
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
        <PwSelect label="Auto" value={car} options={carOptions} onChange={onCar} />
        <PwSelect label="Tracciato" value={track} options={trackOptions} onChange={onTrack} />
        <Segmented label="Condizioni" value={conditions} options={CONDITIONS} onChange={onConditions} />
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

// Switch on/off custom (sostituisce il checkbox nativo). role="switch" accessibile.
function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${checked ? "bg-accent" : "bg-line-strong"}`}
    >
      <span
        className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${checked ? "left-[1.125rem]" : "left-0.5"}`}
      />
    </button>
  );
}

// Dropdown custom coerente col design system (sostituisce il <select> grigio nativo).
// Opzione di un selettore: il valore è la stringa inviata all'API; `badge` è
// un'etichetta accessoria (es. "DLC") mostrata a destra nella tendina.
type SelectOption = { value: string; badge?: string };

function PwSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <label className="flex flex-col gap-1">
      <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">{label}</span>
      <div ref={ref} className="relative">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex w-full items-center justify-between rounded-md border border-line bg-inset px-3 py-2 text-sm text-white transition hover:border-line-strong focus:border-accent focus:outline-none"
        >
          <span className="truncate">{value}</span>
          <span className={`ml-2 text-muted transition-transform ${open ? "rotate-180" : ""}`}>▾</span>
        </button>
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.12 }}
              className="pw-scroll absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-md border border-line bg-raised p-1 shadow-xl"
            >
              {options.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center justify-between gap-2 rounded px-2.5 py-1.5 text-left text-sm transition ${
                    o.value === value
                      ? "bg-accent/15 text-accent"
                      : "text-subtle hover:bg-surface hover:text-white"
                  }`}
                >
                  <span className="truncate">{o.value}</span>
                  {o.badge && (
                    <span className="shrink-0 rounded border border-line px-1 font-mono text-[0.5rem] uppercase tracking-wider text-muted">
                      {o.badge}
                    </span>
                  )}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </label>
  );
}

// Segmented control per poche opzioni fisse (Condizioni).
function Segmented({
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
      <div className="inline-flex rounded-md border border-line bg-inset p-0.5">
        {options.map((o) => (
          <button
            key={o}
            type="button"
            onClick={() => onChange(o)}
            className={`flex-1 rounded px-3 py-1.5 text-sm transition ${
              value === o ? "bg-accent text-white" : "text-subtle hover:text-white"
            }`}
          >
            {o}
          </button>
        ))}
      </div>
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
        className="pw-range mt-1.5 h-2 w-full cursor-pointer rounded-full border border-line-strong bg-[#2a2a2a]"
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
  gigiTarget,
  onChange,
}: {
  paramKey: string;
  param: Param;
  value: number;
  suggested?: boolean;
  gigiTarget?: number; // valore consigliato da Gigi → tacca rossa verticale sulla traccia
  onChange: (v: number) => void;
}) {
  // Pressioni: colore-stato vs finestra. Altri suggeriti da Gigi: valore accent.
  const valColor = isPressure(paramKey)
    ? pressureStatusColor(value)
    : suggested
      ? COLORS.accent
      : COLORS.text;
  // Posizione del marker sulla traccia: percentuale + compensazione della corsa
  // del thumb nativo (16px), stesso trucco dei range stilizzati.
  const targetPct =
    gigiTarget === undefined ? null : (clamp(gigiTarget, param.min, param.max) - param.min) / (param.max - param.min);
  return (
    <div
      id={`param-${paramKey}`}
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
      <div className="relative mt-1.5">
        <input
          type="range"
          min={param.min}
          max={param.max}
          step={param.step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="pw-range h-2 w-full cursor-pointer rounded-full border border-line-strong bg-[#2a2a2a]"
          aria-label={param.label}
        />
        {targetPct !== null && (
          // Tick da strumento: attraversa la traccia (h-2 = 8px) sporgendo ~3px
          // sopra e sotto, come le tacche di riferimento dei gauge.
          <span
            aria-hidden="true"
            title={`Gigi consiglia ${formatValue(param, gigiTarget as number)}`}
            className="pointer-events-none absolute top-1/2 h-3.5 w-[3px] -translate-x-1/2 -translate-y-1/2 rounded-[1px] bg-accent"
            style={{ left: `calc(${targetPct * 100}% + ${(0.5 - targetPct) * 16}px)` }}
          />
        )}
      </div>
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
