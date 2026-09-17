"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { CarCard, TrackCard } from "@/components/ui/SessionBriefing";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { ApiError, getBundle, getSetupParams, postSetupFromImage, type Bundle } from "@/lib/api";
import { CAR_LIST_FALLBACK, DEFAULT_CAR, DEFAULT_TRACK, TRACK_LIST_FALLBACK } from "@/lib/catalog";
import {
  CHIAVE_BOZZA_SETUP,
  formatValue,
  groupsFor,
  suggerimentiDalVerdetto,
  type Group,
  type Param,
  type SetupParams,
  type Suggerimento,
} from "@/lib/setup";
import { useSessione } from "@/lib/sessione";
import { COLORS } from "@/lib/theme";

const GRID_COLS: Record<Group["cols"], string> = {
  1: "grid-cols-1",
  2: "grid-cols-1 sm:grid-cols-2",
  4: "grid-cols-2 lg:grid-cols-4",
};

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi);

export default function SetupPage() {
  const router = useRouter();
  const { report, sessione, nomi, catalogo, idSessione } = useSessione();
  const [params, setParams] = useState<SetupParams | null>(null);
  const [values, setValues] = useState<Record<string, number>>({});
  const [active, setActive] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);
  // Parametro da portare a schermo dopo il cambio tab (click su un suggerimento):
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

  const [showInputs, setShowInputs] = useState(false);
  const [car, setCar] = useState(DEFAULT_CAR);
  const [track, setTrack] = useState(DEFAULT_TRACK);

  // Vettura e pista partono da quelle della sessione aperta (nomi di catalogo: sono le
  // chiavi dei range per vettura di /api/setup-params).
  useEffect(() => {
    if (!sessione) return;
    if (sessione.car) setCar(nomi.vettura(sessione.car));
    if (sessione.track) setTrack(nomi.pista(sessione.track));
  }, [sessione, nomi]);

  const carOptions = useMemo<SelectOption[]>(
    () =>
      catalogo
        ? catalogo.cars.map((c) => ({ value: c.display_name, badge: c.dlc ? "DLC" : undefined }))
        : CAR_LIST_FALLBACK.map((value) => ({ value })),
    [catalogo],
  );
  const trackOptions = useMemo<SelectOption[]>(
    () =>
      catalogo
        ? catalogo.tracks.map((t) => ({ value: t.short_name || t.name, badge: t.dlc ? "DLC" : undefined }))
        : TRACK_LIST_FALLBACK.map((value) => ({ value })),
    [catalogo],
  );

  // Refetch dei range a ogni cambio vettura/circuito: applica gli override e
  // ri-clampa i valori correnti nei nuovi range (non li azzera), come la v1.
  useEffect(() => {
    getSetupParams(car, track)
      .then((d) => {
        const data = d as SetupParams;
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

  const suggeriti = useMemo(() => (report ? suggerimentiDalVerdetto(report.verdetto) : []), [report]);
  const perChiave = useMemo(() => new Map(suggeriti.map((s) => [s.key, s])), [suggeriti]);

  const setVal = (key: string, v: number) => setValues((prev) => ({ ...prev, [key]: v }));

  const findParam = (key: string): { param: Param; section: string } | undefined => {
    if (!params) return undefined;
    for (const [sk, sec] of Object.entries(params)) if (sec.params[key]) return { param: sec.params[key], section: sk };
    return undefined;
  };

  const applyVisionParams = (vp: Record<string, number>): number => {
    let applied = 0;
    setValues((prev) => {
      const next = { ...prev };
      for (const [k, raw] of Object.entries(vp || {})) {
        const trovato = findParam(k);
        const num = Number(raw);
        if (!trovato || Number.isNaN(num)) continue;
        next[k] = clamp(num, trovato.param.min, trovato.param.max);
        applied++;
      }
      return next;
    });
    return applied;
  };

  function applica(s: Suggerimento) {
    const trovato = findParam(s.key);
    if (!trovato) return;
    setActive(trovato.section);
    if (s.variazione !== null) {
      const { param } = trovato;
      setVal(s.key, clamp((values[s.key] ?? param.default) + s.variazione, param.min, param.max));
    }
    setScrollTo(s.key);
  }

  function creaSessione() {
    try {
      sessionStorage.setItem(CHIAVE_BOZZA_SETUP, JSON.stringify(values));
    } catch {
      /* no-op: la pagina Sessioni proporrà di rifarlo */
    }
    router.push("/sessioni");
  }

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
  const sectionHasSuggested = (sk: string) => Object.keys(params[sk].params).some((k) => perChiave.has(k));

  return (
    <div>
      <PageHeader title="Setup" subtitle={`${car} · ${track} · range ACC`} />

      {/* I parametri che il verdetto chiede di toccare (collega Dashboard/Console ↔ Setup) */}
      {suggeriti.length > 0 && (
        <motion.div variants={fadeInUp} initial="hidden" animate="visible" className="mb-4 rounded-xl border border-accent/30 bg-accent/[0.06] p-4">
          <div className="mb-2 flex items-center gap-2 font-mono text-[0.6rem] uppercase tracking-widest text-accent">
            🔧 Da toccare secondo il verdetto
          </div>
          <div className="flex flex-wrap gap-2">
            {suggeriti.map((s) => {
              const trovato = findParam(s.key);
              if (!trovato) return null;
              return (
                <button
                  key={s.key}
                  onClick={() => applica(s)}
                  title={s.motivi.join(" · ")}
                  className="rounded-md border border-accent/40 bg-accent/10 px-2.5 py-1 text-[0.78rem] text-white transition hover:border-accent"
                >
                  {trovato.param.label}
                  <span className="ml-1.5 font-mono text-[0.68rem] text-accent">
                    {s.variazione === null ? "direzione nel verdetto" : `${s.variazione > 0 ? "+" : ""}${s.variazione} ${trovato.param.unit}`}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="mt-2 text-[0.7rem] text-muted">
            Un click applica la variazione al valore sullo slider e porta al parametro. Le pressioni del setup sono a freddo:
            la variazione viene dallo scarto misurato in pista.
          </div>
        </motion.div>
      )}

      {report?.ha_setup && idSessione && <SetupDellaSessione idSessione={idSessione} params={params} />}

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex w-fit items-center gap-2.5 text-sm text-subtle">
          <Toggle checked={showInputs} onChange={setShowInputs} label="Mostra vettura, pista e screenshot" />
          <span>Vettura, pista · screenshot del setup</span>
        </div>
        <button
          type="button"
          onClick={creaSessione}
          className="rounded-md border border-line-strong px-3 py-1.5 font-mono text-[0.62rem] uppercase tracking-widest text-subtle transition hover:border-accent hover:text-white"
          title="Porta questi valori nella pagina Sessioni, per una sessione da console"
        >
          Crea una sessione con questo setup →
        </button>
      </div>

      {showInputs && (
        <div className="mb-6 rounded-xl border border-line bg-surface p-4">
          <div className="mb-3 font-mono text-[0.62rem] uppercase tracking-widest text-accent">Vettura e pista</div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <PwSelect label="Auto" value={car} options={carOptions} onChange={setCar} />
            <PwSelect label="Tracciato" value={track} options={trackOptions} onChange={setTrack} />
          </div>
          <div className="mt-4 border-t border-line pt-4">
            <ScreenshotUpload onApplyVision={applyVisionParams} />
          </div>
        </div>
      )}

      {showInputs && (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
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
              {sectionHasSuggested(k) && <span className="h-1.5 w-1.5 rounded-full bg-accent" title="Contiene parametri citati dal verdetto" />}
            </button>
          );
        })}
      </div>

      {/* Gruppi di slider — transizione morbida al cambio tab (AnimatePresence) */}
      <AnimatePresence mode="wait">
        <motion.div key={active} variants={staggerContainer} initial="hidden" animate="visible" exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}>
          {groups.map((g, gi) => (
            <motion.div key={gi} variants={fadeInUp} className="mb-6">
              {g.title && <div className="mb-3 font-mono text-[0.62rem] uppercase tracking-widest text-accent">{g.title}</div>}
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
                      suggerimento={perChiave.get(key)}
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
// Il setup registrato nella sessione, com'è nel file di ACC
// ─────────────────────────────────────────────
function SetupDellaSessione({ idSessione, params }: { idSessione: string; params: SetupParams }) {
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [aperto, setAperto] = useState(false);

  useEffect(() => {
    let vivo = true;
    getBundle(idSessione)
      .then((b) => vivo && setBundle(b))
      .catch(() => vivo && setBundle(null));
    return () => {
      vivo = false;
    };
  }, [idSessione]);

  const setup = bundle?.setup;
  if (!setup) return null;
  const etichette = new Map(Object.values(params).flatMap((s) => Object.entries(s.params).map(([k, p]) => [k, p.label] as const)));
  const verificati = Object.values(setup.valori).filter((v) => v.verificato).length;

  return (
    <div className="mb-4 rounded-xl border border-line bg-surface p-4">
      <button type="button" onClick={() => setAperto((a) => !a)} aria-expanded={aperto} className="flex w-full items-center justify-between text-left">
        <span className="font-mono text-[0.62rem] uppercase tracking-widest text-subtle">
          Setup della sessione · {setup.nome ?? "senza nome"} · {Object.keys(setup.valori).length} parametri
        </span>
        <span className="font-mono text-[0.6rem] text-muted">{aperto ? "▴" : "▾"}</span>
      </button>
      {aperto && (
        <>
          <p className="mt-2 text-[0.72rem] text-muted">
            Valori come li scrive ACC: {verificati === 0 ? "tutti in click" : `${verificati} in unità reali, gli altri in click`}. La
            conversione in unità reali non è ancora verificata per questa vettura, quindi non si caricano negli slider (che
            sono in unità reali): si leggono qui.
          </p>
          <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 font-mono text-[0.72rem] sm:grid-cols-3 lg:grid-cols-4">
            {Object.entries(setup.valori).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2 border-b border-line/50 py-0.5">
                <span className="truncate text-muted">{etichette.get(k) ?? k}</span>
                <span className="text-white">
                  {v.verificato && v.reale !== null ? `${v.reale} ${v.unita}` : Array.isArray(v.raw) ? v.raw.join("/") : v.raw}
                </span>
              </div>
            ))}
          </div>
          {setup.assunzioni.length > 0 && (
            <ul className="mt-2 flex flex-col gap-0.5 text-[0.68rem] text-muted">
              {setup.assunzioni.map((a) => (
                <li key={a}>· {a}</li>
              ))}
            </ul>
          )}
        </>
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
      <div className="mb-1.5 font-mono text-[0.6rem] uppercase tracking-widest text-muted">Screenshot setup ACC</div>
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
      {summary && <pre className="mt-2 whitespace-pre-wrap font-mono text-[0.7rem] text-subtle">{summary}</pre>}
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
function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${checked ? "bg-accent" : "bg-line-strong"}`}
    >
      <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${checked ? "left-[1.125rem]" : "left-0.5"}`} />
    </button>
  );
}

// Opzione di un selettore: il valore è la stringa inviata all'API; `badge` è
// un'etichetta accessoria (es. "DLC") mostrata a destra nella tendina.
type SelectOption = { value: string; badge?: string };

function PwSelect({ label, value, options, onChange }: { label: string; value: string; options: SelectOption[]; onChange: (v: string) => void }) {
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
                    o.value === value ? "bg-accent/15 text-accent" : "text-subtle hover:bg-surface hover:text-white"
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

// ─────────────────────────────────────────────
// Slider ACC + Rake
// ─────────────────────────────────────────────
function Slider({
  paramKey,
  param,
  value,
  suggerimento,
  onChange,
}: {
  paramKey: string;
  param: Param;
  value: number;
  suggerimento?: Suggerimento; // parametro citato dal verdetto
  onChange: (v: number) => void;
}) {
  const citato = !!suggerimento;
  return (
    <div id={`param-${paramKey}`} className={`py-2 ${citato ? "border-l-2 border-accent pl-2.5" : ""}`} title={suggerimento ? suggerimento.motivi.join(" · ") : param.tip || undefined}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="flex items-center gap-1.5 font-mono text-[0.66rem] uppercase tracking-wider text-subtle">
          {param.label}
          {citato && (
            <span className="rounded border border-accent px-1 py-px text-[0.5rem] font-semibold not-italic text-accent">
              VERDETTO{suggerimento?.variazione !== null && suggerimento?.variazione !== undefined ? ` ${suggerimento.variazione > 0 ? "+" : ""}${suggerimento.variazione}` : ""}
            </span>
          )}
        </span>
        <span className="font-mono text-[0.82rem] font-semibold" style={{ color: citato ? COLORS.accent : COLORS.text }}>
          {formatValue(param, value)}
        </span>
      </div>
      <input
        type="range"
        min={param.min}
        max={param.max}
        step={param.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="pw-range mt-1.5 h-2 w-full cursor-pointer rounded-full border border-line-strong bg-[#2a2a2a]"
        aria-label={param.label}
      />
    </div>
  );
}

// Il rake si mostra, non si giudica: una soglia «giusta» non è pubblicata.
function RakeInfo({ front, rear }: { front: number; rear: number }) {
  return <div className="mt-2 font-mono text-sm text-subtle">Rake attuale: {(rear - front).toFixed(0)} mm</div>;
}
