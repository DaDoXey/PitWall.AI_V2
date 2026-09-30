"use client";

// Pagina Setup (#058, 30/09/2026): il setup della sessione aperta, in CLICK come nel
// file di ACC. Frecce − / + come nel gioco; accanto al click il valore che il gioco
// mostra, solo dove la tabella della vettura ha la regola (car_setup_ranges.json).
// Niente range generici né valori di partenza inventati: senza file di setup la pagina
// invita a importarlo. Le modifiche restano nella scheda del browser; «Scarica il
// setup per ACC» restituisce il file originale con i click cambiati.

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { ApiError, esportaSetupAcc, getBundle, getSetupParams, type Bundle } from "@/lib/api";
import {
  clickDaVariazione,
  clickMax,
  formatReale,
  groupsFor,
  reale,
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

// Le modifiche di una sessione, {parametro: click}, finché la scheda è aperta.
const chiaveModifiche = (id: string) => `pw_setup_modifiche_${id}`;

const clickIntero = (raw: unknown): number | null => (typeof raw === "number" && Number.isInteger(raw) && raw >= 0 ? raw : null);

export default function SetupPage() {
  const { report, nomi, idSessione } = useSessione();
  const [bundle, setBundle] = useState<Bundle | null | undefined>(undefined);
  const [params, setParams] = useState<SetupParams | null>(null);
  const [modifiche, setModifiche] = useState<Record<string, number>>({});
  const [active, setActive] = useState<string>("");
  const [err, setErr] = useState<string | null>(null);
  const [scrollTo, setScrollTo] = useState<string | null>(null);
  const [download, setDownload] = useState<{ ok: boolean; testo: string } | null>(null);

  // Il bundle della sessione aperta (il setup con il file originale di ACC).
  useEffect(() => {
    if (!idSessione) {
      setBundle(null);
      return;
    }
    let vivo = true;
    setBundle(undefined);
    getBundle(idSessione)
      .then((b) => vivo && setBundle(b))
      .catch(() => vivo && setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
    try {
      const salvate = sessionStorage.getItem(chiaveModifiche(idSessione));
      setModifiche(salvate ? (JSON.parse(salvate) as Record<string, number>) : {});
    } catch {
      setModifiche({});
    }
    return () => {
      vivo = false;
    };
  }, [idSessione]);

  const setup = bundle?.setup ?? null;
  const car = setup?.car ?? bundle?.meta.car ?? null;

  // Etichette e regole della vettura del setup.
  useEffect(() => {
    if (!setup) return;
    getSetupParams(car ?? undefined)
      .then((d) => {
        const data = d as SetupParams;
        setParams(data);
        setActive((a) => a || Object.keys(data)[0] || "");
      })
      .catch(() => setErr("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)."));
  }, [setup, car]);

  useEffect(() => {
    if (!idSessione) return;
    try {
      if (Object.keys(modifiche).length) sessionStorage.setItem(chiaveModifiche(idSessione), JSON.stringify(modifiche));
      else sessionStorage.removeItem(chiaveModifiche(idSessione));
    } catch {
      /* no-op: le modifiche restano solo in memoria */
    }
  }, [modifiche, idSessione]);

  // Porta a schermo il parametro dopo il cambio tab (clic su un suggerimento).
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

  const originali = useMemo(() => {
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(setup?.valori ?? {})) {
      const c = clickIntero(v.raw);
      if (c !== null) out[k] = c;
    }
    return out;
  }, [setup]);

  const suggeriti = useMemo(() => (report ? suggerimentiDalVerdetto(report.verdetto) : []), [report]);
  const perChiave = useMemo(() => new Map(suggeriti.map((s) => [s.key, s])), [suggeriti]);

  const trova = (key: string): { param: Param; section: string } | undefined => {
    if (!params) return undefined;
    for (const [sk, sec] of Object.entries(params)) if (sec.params[key]) return { param: sec.params[key], section: sk };
    return undefined;
  };

  const valore = (key: string) => modifiche[key] ?? originali[key];

  function imposta(key: string, click: number) {
    const trovato = trova(key);
    const massimo = trovato ? clickMax(trovato.param.regola) : null;
    const c = Math.max(0, massimo === null ? click : Math.min(click, massimo));
    setDownload(null);
    setModifiche((prev) => {
      const next = { ...prev };
      if (c === originali[key]) delete next[key];
      else next[key] = c;
      return next;
    });
  }

  function applica(s: Suggerimento) {
    const trovato = trova(s.key);
    if (!trovato) return;
    setActive(trovato.section);
    const passi = s.variazione === null ? null : clickDaVariazione(trovato.param.regola, valore(s.key), s.variazione);
    if (passi !== null && originali[s.key] !== undefined) imposta(s.key, valore(s.key) + passi);
    setScrollTo(s.key);
  }

  async function scarica() {
    if (!idSessione) return;
    setDownload(null);
    try {
      const { file, nome } = await esportaSetupAcc(idSessione, modifiche);
      const url = URL.createObjectURL(file);
      const a = document.createElement("a");
      a.href = url;
      a.download = nome;
      a.click();
      URL.revokeObjectURL(url);
      setDownload({ ok: true, testo: `Scaricato «${nome}»: mettilo in Documenti\\Assetto Corsa Competizione\\Setups\\${car ?? "<auto>"}\\<pista>\\ e caricalo in gioco.` });
    } catch (e) {
      setDownload({ ok: false, testo: e instanceof ApiError ? e.message : "Download non riuscito." });
    }
  }

  const titolo = (
    <PageHeader
      title="Setup"
      subtitle={bundle ? `${nomi.vettura(car)} · ${nomi.pista(bundle.meta.track)}${setup?.nome ? ` · ${setup.nome}` : ""}` : "il setup della sessione"}
    />
  );

  if (err)
    return (
      <div>
        {titolo}
        <p className="text-sm text-warn">{err}</p>
      </div>
    );
  if (bundle === undefined || (setup && !params))
    return (
      <div>
        {titolo}
        <p className="text-sm text-subtle">Caricamento del setup…</p>
      </div>
    );
  if (!setup || !Object.keys(setup.valori).length)
    return (
      <div>
        {titolo}
        <div className="max-w-2xl rounded-xl border border-line bg-surface p-5">
          <div className="mb-2 font-mono text-[0.62rem] uppercase tracking-widest text-accent">Nessun setup in questa sessione</div>
          <p className="text-sm text-subtle">
            Il setup arriva dal file JSON che ACC salva in <span className="font-mono text-[0.78rem]">Documenti\Assetto Corsa Competizione\Setups\&lt;auto&gt;\&lt;pista&gt;\</span>.
            Aggiungilo dalla pagina{" "}
            <Link href="/sessioni" className="text-white underline-offset-2 hover:underline">
              Sessioni
            </Link>{" "}
            (Aggiungi una sessione → File di ACC, oppure insieme all&apos;export MoTeC): qui si vede e si modifica click per click.
          </p>
        </div>
      </div>
    );
  if (!params) return null;

  const tuttiParam = Object.values(params).flatMap((s) => Object.entries(s.params));
  const conTabella = tuttiParam.some(([, p]) => p.regola !== null);
  const convertiti = tuttiParam.filter(([k, p]) => p.regola !== null && originali[k] !== undefined).length;
  const daFonti = tuttiParam.some(([, p]) => p.regola?.stato === "fonti");
  const nModifiche = Object.keys(modifiche).length;
  const puoScaricare = Object.keys(setup.raw ?? {}).length > 0;

  const section = params[active];
  const groups = section ? groupsFor(active, section) : [];
  const sectionHasSuggested = (sk: string) => Object.keys(params[sk].params).some((k) => perChiave.has(k));
  const sectionHasChanged = (sk: string) => Object.keys(params[sk].params).some((k) => k in modifiche);

  const rh = (k: string) => {
    const p = trova(k)?.param;
    return p && valore(k) !== undefined ? reale(p.regola, valore(k)) : null;
  };
  const rakeFront = rh("ride_height_front");
  const rakeRear = rh("ride_height_rear");

  return (
    <div>
      {titolo}

      {/* Da dove vengono i numeri, in una riga */}
      <p className="mb-4 max-w-4xl text-[0.74rem] text-muted">
        {conTabella ? (
          <>
            Valori come in ACC: il click del file e, accanto, il valore che il gioco mostra ({convertiti} parametri su {Object.keys(setup.valori).length}).
            {daFonti && " Conversioni da fonti community concordi, non ancora viste in gioco."} Gli altri restano in click.
          </>
        ) : (
          <>Per {nomi.vettura(car)} non c&apos;è ancora una tabella: i valori sono i click del file di ACC, come li conta il gioco.</>
        )}
      </p>

      {/* I parametri che il verdetto chiede di toccare */}
      {suggeriti.length > 0 && (
        <motion.div variants={fadeInUp} initial="hidden" animate="visible" className="mb-4 rounded-xl border border-accent/30 bg-accent/[0.06] p-4">
          <div className="mb-2 flex items-center gap-2 font-mono text-[0.6rem] uppercase tracking-widest text-accent">🔧 Da toccare secondo il verdetto</div>
          <div className="flex flex-wrap gap-2">
            {suggeriti.map((s) => {
              const trovato = trova(s.key);
              if (!trovato) return null;
              const passi = s.variazione === null ? null : clickDaVariazione(trovato.param.regola, valore(s.key), s.variazione);
              const unita = trovato.param.regola?.unita ?? trovato.param.unit;
              const variazione = s.variazione === null ? "" : `${s.variazione > 0 ? "+" : ""}${s.variazione} ${unita}`.trim();
              return (
                <button
                  key={s.key}
                  onClick={() => applica(s)}
                  title={s.motivi.join(" · ")}
                  className="rounded-md border border-accent/40 bg-accent/10 px-2.5 py-1 text-[0.78rem] text-white transition hover:border-accent"
                >
                  {trovato.param.label}
                  <span className="ml-1.5 font-mono text-[0.68rem] text-accent">
                    {passi !== null
                      ? `${passi > 0 ? "+" : ""}${passi} click (${variazione})`
                      : s.variazione === null
                        ? "direzione nel verdetto"
                        : `${variazione} · senza tabella, solo la direzione`}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="mt-2 text-[0.7rem] text-muted">
            Un clic applica i click al parametro (dove c&apos;è la tabella) e lo porta a schermo. Le pressioni del setup sono a freddo: la variazione viene dallo scarto misurato in pista.
          </div>
        </motion.div>
      )}

      {/* Tab + azioni sul file */}
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-line">
        <div className="flex flex-wrap gap-1">
          {Object.keys(params).map((k) => {
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
                {sectionHasChanged(k) && <span className="h-1.5 w-1.5 rounded-full bg-white" title="Contiene parametri modificati" />}
              </button>
            );
          })}
        </div>
        <div className="mb-1.5 flex items-center gap-2">
          <span className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">
            {nModifiche === 0 ? "nessuna modifica" : `${nModifiche} ${nModifiche === 1 ? "modifica" : "modifiche"}`}
          </span>
          <button
            type="button"
            onClick={() => {
              setModifiche({});
              setDownload(null);
            }}
            disabled={nModifiche === 0}
            className="rounded-md border border-line-strong px-3 py-1.5 font-mono text-[0.62rem] uppercase tracking-widest text-subtle transition hover:border-accent hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            Ripristina
          </button>
          <button
            type="button"
            onClick={scarica}
            disabled={!puoScaricare}
            title={puoScaricare ? "Il file di setup originale con i click cambiati, da caricare in ACC" : "Questa sessione non ha il file di setup di ACC"}
            className="rounded-md border border-accent/60 bg-accent/10 px-3 py-1.5 font-mono text-[0.62rem] uppercase tracking-widest text-white transition hover:border-accent disabled:cursor-not-allowed disabled:opacity-40"
          >
            Scarica il setup per ACC ↓
          </button>
        </div>
      </div>
      {download && <p className={`-mt-3 mb-4 text-[0.72rem] ${download.ok ? "text-ok" : "text-warn"}`}>{download.testo}</p>}

      <AnimatePresence mode="wait">
        <motion.div key={active} variants={staggerContainer} initial="hidden" animate="visible" exit={{ opacity: 0, y: -8, transition: { duration: 0.15 } }}>
          {groups.map((g, gi) => (
            <motion.div key={gi} variants={fadeInUp} className="mb-5">
              {g.title && <div className="mb-2 font-mono text-[0.62rem] uppercase tracking-widest text-accent">{g.title}</div>}
              <div className={`grid gap-x-6 gap-y-1 ${GRID_COLS[g.cols]}`}>
                {g.keys.map((key) => {
                  const p = section.params[key];
                  if (!p) return null;
                  return (
                    <Frecce
                      key={key}
                      paramKey={key}
                      param={p}
                      click={valore(key)}
                      originale={originali[key]}
                      grezzo={setup.valori[key]?.raw}
                      conTabella={conTabella}
                      compatto={g.cols === 4}
                      suggerimento={perChiave.get(key)}
                      onChange={(c) => imposta(key, c)}
                    />
                  );
                })}
              </div>
              {active === "aero" && g.title.startsWith("Ride height") && rakeFront !== null && rakeRear !== null && (
                <div className="mt-2 font-mono text-sm text-subtle">Rake attuale: {(rakeRear - rakeFront).toFixed(0)} mm</div>
              )}
            </motion.div>
          ))}
        </motion.div>
      </AnimatePresence>

      {setup.assunzioni.length > 0 && (
        <ul className="mt-2 flex flex-col gap-0.5 border-t border-line pt-3 text-[0.68rem] text-muted">
          {setup.assunzioni.map((a) => (
            <li key={a}>· {a}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Un parametro: frecce − / + come in ACC, click e valore del gioco
// ─────────────────────────────────────────────
function Frecce({
  paramKey,
  param,
  click,
  originale,
  grezzo,
  conTabella,
  compatto,
  suggerimento,
  onChange,
}: {
  paramKey: string;
  param: Param;
  click: number | undefined;
  originale: number | undefined;
  grezzo: number | number[] | undefined;
  conTabella: boolean;
  compatto: boolean;
  suggerimento?: Suggerimento;
  onChange: (click: number) => void;
}) {
  const r = param.regola;
  const citato = !!suggerimento;
  const massimo = clickMax(r);
  const cambiato = click !== undefined && originale !== undefined && click !== originale;
  const mostra = (c: number) => {
    const v = reale(r, c);
    // Se il gioco mostra lo stesso numero del click (TC, barre, ammortizzatori…) basta una volta.
    if (v === null || !r || (v === c && !r.unita)) return `${c}`;
    return `${c} · ${formatReale(r, v)}`;
  };
  const freccia =
    "h-6 w-6 shrink-0 rounded border border-line-strong font-mono text-xs text-subtle transition hover:border-accent hover:text-white disabled:cursor-not-allowed disabled:opacity-30";

  return (
    <div
      id={`param-${paramKey}`}
      className={`py-1.5 ${citato ? "border-l-2 border-accent pl-2.5" : ""}`}
      title={suggerimento ? suggerimento.motivi.join(" · ") : r?.nota ?? param.tip ?? undefined}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5 truncate font-mono text-[0.64rem] uppercase tracking-wider text-subtle">
          {param.label}
          {citato && <span className="rounded border border-accent px-1 py-px text-[0.5rem] font-semibold text-accent">VERDETTO</span>}
          {conTabella && !r && (
            <span className="rounded border border-warn/60 px-1 py-px text-[0.5rem] font-semibold normal-case tracking-normal text-warn" title="Le fonti non concordano: resta in click finché non si vede in gioco">
              da verificare
            </span>
          )}
        </span>
        {click === undefined ? (
          <span className="font-mono text-[0.78rem] text-muted" title="Nel file non c'è un click intero per questo parametro">
            {grezzo === undefined ? "—" : Array.isArray(grezzo) ? grezzo.join("/") : grezzo}
          </span>
        ) : (
          <div className="flex shrink-0 items-center gap-1.5">
            <button type="button" className={freccia} onClick={() => onChange(click - 1)} disabled={click <= 0} aria-label={`${param.label}: un click in meno`}>
              ◀
            </button>
            <span
              className={`${compatto ? "min-w-[2.5rem]" : "min-w-[8.5rem]"} text-center font-mono text-[0.8rem] font-semibold`}
              style={{ color: citato ? COLORS.accent : COLORS.text }}
            >
              {compatto ? click : mostra(click)}
              {!r || compatto ? <span className="ml-1 text-[0.6rem] font-normal text-muted">click</span> : null}
            </span>
            <button
              type="button"
              className={freccia}
              onClick={() => onChange(click + 1)}
              disabled={massimo !== null && click >= massimo}
              aria-label={`${param.label}: un click in più`}
            >
              ▶
            </button>
          </div>
        )}
      </div>
      {cambiato && (
        <div className="mt-0.5 text-right font-mono text-[0.6rem] text-muted">
          era {compatto ? originale : mostra(originale!)}
          <button type="button" onClick={() => onChange(originale!)} className="ml-1.5 text-subtle underline-offset-2 hover:text-white hover:underline">
            ripristina
          </button>
        </div>
      )}
    </div>
  );
}
