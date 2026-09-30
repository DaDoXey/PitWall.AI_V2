"use client";

// Dashboard (riordinata il 29/09/2026, Entry #050, con le regole del #008/#010: niente
// doppioni, niente vuoti, il verdetto prima di tutto).
//   * in alto una FASCIA con la sessione (pista, vettura, tipo, giri, fonte, gomme, data);
//   * sotto due colonne: a sinistra il VERDETTO; a destra «Cosa regge», gli INDICATORI
//     come righe compatte (clic = dettaglio col grafico); le note sui dati sotto il verdetto;
//   * in fondo pista e vettura in versione compatta.
// Via: i numeri della vecchia scheda (erano gli stessi degli indicatori), i riquadri
// grandi con trascina/allarga, le foto a tutta larghezza, «Prossime azioni» (doppione
// della colonna di sinistra). Da ~2350 px a circa una schermata e mezza.
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import PageHeader from "@/components/ui/PageHeader";
import CountUp from "@/components/ui/CountUp";
import { CarCard, TrackCard } from "@/components/ui/SessionBriefing";
import { CosaRegge, ElencoVerdetto, NoteDati, StatoSessione } from "@/components/ui/Verdetto";
import { fadeInUp, staggerContainer, useReducedMotion } from "@/lib/motion";
import type { Finestra, Report, Riassunto } from "@/lib/api";
import { useSessione } from "@/lib/sessione";
import { data, ETICHETTA_TIPO, etichettaFonte, giri, numero, RUOTE, tempoGiro } from "@/lib/formato";
import { COLORS } from "@/lib/theme";
import { INSTRUMENT, STATE } from "@/lib/instrument";

export default function Dashboard() {
  const { report, sessione, caricamento, errore, nomi } = useSessione();
  const [selected, setSelected] = useState<string | null>(null); // indicatore aperto nel dettaglio

  if (!report || !sessione)
    return (
      <div>
        <PageHeader title="Dashboard" subtitle="Il verdetto della sessione" />
        <StatoSessione errore={errore} caricamento={caricamento || !report} />
      </div>
    );

  const kpis = buildKpis(report);
  const openKpi = selected ? kpis.find((k) => k.id === selected) ?? null : null;

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Il verdetto della sessione" />

      <FasciaSessione report={report} sessione={sessione} pista={nomi.pista(report.track)} vettura={nomi.vettura(report.car)} />

      {/* Il verdetto viene prima dei numeri: è la ragione per cui si apre la pagina. */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <Titoletto>Verdetto · ordinato per gravità</Titoletto>
          <ElencoVerdetto voci={report.verdetto} />
          {/* Su quali dati poggia il verdetto: sta sotto di lui, e pareggia le colonne. */}
          <div className="mt-4">
            <NoteDati note={report.dati_mancanti} />
          </div>
        </section>
        <aside className="flex flex-col gap-5">
          {report.cosa_regge.length > 0 && (
            <div>
              <Titoletto>Cosa regge</Titoletto>
              <CosaRegge punti={report.cosa_regge} />
            </div>
          )}
          <div>
            <Titoletto>Indicatori · clic per il dettaglio</Titoletto>
            <Indicatori kpis={kpis} onApri={setSelected} />
          </div>
        </aside>
      </div>

      {/* Contesto dal catalogo ACC: chi è questa pista e questa vettura, in piccolo. */}
      {(report.track || report.car) && (
        <div className="mt-8">
          <Titoletto>Pista e vettura</Titoletto>
          <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {report.track && <TrackCard track={report.track} compatta />}
            {report.car && <CarCard car={report.car} compatta />}
          </motion.div>
        </div>
      )}

      <AnimatePresence>{openKpi && <KpiModal kpi={openKpi} onClose={() => setSelected(null)} />}</AnimatePresence>
    </div>
  );
}

function Titoletto({ children }: { children: React.ReactNode }) {
  return <div className="mb-2 font-mono text-[0.6rem] uppercase tracking-widest text-muted">{children}</div>;
}

// ─────────────────────────────────────────────
// La fascia della sessione aperta: chi, dove, cosa. I numeri stanno negli indicatori.
// ─────────────────────────────────────────────
function FasciaSessione({ report, sessione, pista, vettura }: { report: Report; sessione: Riassunto; pista: string; vettura: string }) {
  const quando = sessione.demo ? null : data(sessione.iniziata_il ?? sessione.importato_il);
  const voci = [
    ETICHETTA_TIPO[report.tipo_sessione] ?? "Sessione",
    `${giri(report.giri_totali)}${report.giri_buttati ? ` · ${report.giri_buttati} buttati` : ""}`,
    report.mescola ? `gomme da ${report.mescola}` : null,
    report.ha_canali ? "con telemetria" : "senza telemetria",
    quando,
  ].filter(Boolean) as string[];
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className="mb-6 flex flex-wrap items-center justify-between gap-x-6 gap-y-2 rounded-xl border border-l-4 border-line border-l-accent bg-surface px-5 py-3"
    >
      <div className="flex min-w-0 items-baseline gap-3">
        <span className="font-display text-xl font-bold">{pista}</span>
        <span className="truncate text-sm text-subtle">{vettura}</span>
      </div>
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[0.62rem] uppercase tracking-widest text-subtle">
        {voci.map((v, i) => (
          <span key={i} className="flex items-center gap-2">
            {i > 0 && <span className="text-muted">·</span>}
            {v}
          </span>
        ))}
        <span
          className="ml-1 rounded border px-1.5 py-0.5 text-[0.55rem]"
          style={{ borderColor: sessione.demo ? COLORS.ok : COLORS.line, color: sessione.demo ? COLORS.ok : COLORS.subtle }}
        >
          {etichettaFonte(sessione.fonte, sessione.piattaforma)}
          {sessione.riferimento ? " · rif." : ""}
        </span>
      </div>
    </motion.div>
  );
}

// Gli indicatori come righe: nome, valore, stato. Il grafico e il «come si calcola»
// restano nel dettaglio, come prima.
function Indicatori({ kpis, onApri }: { kpis: Kpi[]; onApri: (id: string) => void }) {
  return (
    <div className="flex flex-col divide-y divide-line overflow-hidden rounded-xl border border-line bg-surface">
      {kpis.map((k) => {
        const vuoto = k.valueNum === null;
        const attenzione = k.color === STATE.warn || k.color === STATE.alarm;
        return (
          <button
            key={k.id}
            type="button"
            onClick={() => onApri(k.id)}
            title={k.note}
            className="group flex flex-col gap-0.5 px-3.5 py-2 text-left transition hover:bg-raised"
          >
            <div className="flex items-center gap-2">
              <StatusDot color={vuoto ? COLORS.muted : k.color} pulse={attenzione} />
              <span className="min-w-0 flex-1 truncate text-[0.8rem] text-subtle group-hover:text-white">{k.label}</span>
              <span className="shrink-0 font-mono text-sm" style={{ color: vuoto ? COLORS.muted : k.color }}>
                {vuoto ? "—" : k.display ?? `${numero(k.valueNum, k.decimals)}${k.suffix}`}
              </span>
            </div>
            <div className="truncate pl-3.5 text-[0.68rem] text-muted">{k.note}</div>
          </button>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────
// KPI: modello dati. Tutti letti dal report del motore: qui niente medie, niente
// soglie — solo la scelta di cosa mostrare e in che unità.
// ─────────────────────────────────────────────
type Kpi = {
  id: string;
  label: string;
  valueNum: number | null; // null = non calcolabile (si mostra `display` o «—»)
  display?: string; // valore testuale (tempi sul giro) al posto del CountUp
  suffix: string;
  decimals: number;
  note: string;
  detail: string; // "come si calcola" mostrato nel modal
  color: string;
  series?: number[];
  xs?: number[]; // numeri di giro della serie
  refLines?: number[];
  unit?: string; // unità dell'asse del grafico
  refs: string[];
};

function finestraKpi(id: string, label: string, f: Finestra | null, report: Report): Kpi {
  if (!f) {
    const motivo = !report.ha_canali
      ? "Serve la telemetria della sessione"
      : report.mescola !== "asciutto"
        ? "Finestra Kunos solo per gomme da asciutto"
        : "Non misurata";
    return { id, label, valueNum: null, suffix: "", decimals: 0, note: motivo, detail: motivo, color: COLORS.muted, refs: [] };
  }
  const fuori = f.ruote_fuori;
  const nomi = RUOTE.filter((r) => fuori.includes(r.key)).map((r) => r.label);
  return {
    id,
    label,
    valueNum: RUOTE.length - fuori.length,
    suffix: "/4",
    decimals: 0,
    note: fuori.length === 0 ? `Tutte dentro ${f.min}–${f.max} ${f.unita}` : `Fuori: ${nomi.join(", ")}`,
    detail: `Ruote rimaste dentro la finestra indicativa Kunos (${f.min}–${f.max} ${f.unita}) nei giri completi fuori dai box. Una ruota conta «fuori» quando ci passa almeno il 20% del tempo.`,
    color: fuori.length === 0 ? STATE.ok : STATE.warn,
    refs: [
      ...RUOTE.map((r) => `${r.label}: dentro ${numero(f.dentro_pct[r.key], 0)}% · sotto ${numero(f.sotto_pct[r.key], 0)}% · sopra ${numero(f.sopra_pct[r.key], 0)}%`),
      `Fonte: ${f.fonte}`,
    ],
  };
}

function buildKpis(report: Report): Kpi[] {
  const r = report.ritmo;
  const conTempo = report.giri.filter((g) => g.tempo_ms !== null);
  const ritmici = conTempo.filter((g) => g.di_ritmo);
  const gomme = report.gomme_e_freni?.gomme ?? null;
  const d = report.degrado;
  const dalGiro = d.dal_giro ?? 1;
  const giriDegrado = ritmici.filter((g) => g.numero >= dalGiro);
  const conConsumo = report.giri.filter((g) => g.carburante_usato_l !== null);

  return [
    {
      id: "best",
      label: "Miglior giro",
      valueNum: r.miglior_giro_ms,
      display: tempoGiro(r.miglior_giro_ms),
      suffix: "",
      decimals: 0,
      note: r.miglior_giro_ms ? `Giro ${r.miglior_giro_numero} · media ${tempoGiro(r.media_ms)}` : "Nessun giro valido",
      detail: "Il giro valido più veloce della sessione; la media è sui giri di ritmo (entro il +10% dal migliore).",
      color: STATE.best,
      series: conTempo.map((g) => (g.tempo_ms as number) / 1000),
      xs: conTempo.map((g) => g.numero),
      refLines: r.miglior_giro_ms ? [r.miglior_giro_ms / 1000] : undefined,
      unit: "s",
      refs: [`Giri di ritmo: ${report.giri_di_ritmo}`, `Esclusi dal ritmo: ${report.giri_esclusi_dal_ritmo}`],
    },
    {
      id: "teorico",
      label: "Giro teorico",
      valueNum: r.giro_teorico_ms,
      display: tempoGiro(r.giro_teorico_ms),
      suffix: "",
      decimals: 0,
      note:
        r.lasciato_sul_tavolo_ms !== null
          ? `${r.lasciato_sul_tavolo_ms} ms lasciati sul tavolo`
          : r.motivo_teorico ?? "Non calcolabile",
      detail: "Somma dei tuoi tre settori migliori. La differenza con il miglior giro è il tempo che sai già fare ma non hai messo insieme.",
      color: r.lasciato_sul_tavolo_ms === null ? COLORS.muted : r.lasciato_sul_tavolo_ms < 100 ? STATE.ok : STATE.warn,
      refs: [
        ...report.settori.map((s) => `S${s.numero}: migliore ${(s.migliore_ms / 1000).toFixed(3)} s · perdita media ${s.perdita_media_ms} ms`),
        ...(r.giri_per_teorico ? [`Costruito su ${r.giri_per_teorico} giri con tutti i settori`] : []),
      ],
    },
    {
      id: "costanza",
      label: "Costanza",
      valueNum: report.costanza.deviazione_ms,
      suffix: " ms",
      decimals: 0,
      note: report.costanza.deviazione_ms !== null
        ? `${report.costanza.giudizio} · ${numero(report.costanza.percentuale_entro_mezzo_secondo, 0)}% entro 0,5 s`
        : report.costanza.giudizio ?? "Non calcolabile",
      detail: "Deviazione standard dei tempi sui giri di ritmo: quanto assomigli a te stesso giro dopo giro.",
      color: report.costanza.giudizio === "da cronometro" || report.costanza.giudizio === "solida" ? STATE.ok : report.costanza.deviazione_ms === null ? COLORS.muted : STATE.warn,
      series: ritmici.map((g) => (g.delta_migliore_ms ?? 0) / 1000),
      xs: ritmici.map((g) => g.numero),
      refLines: [0],
      unit: "s dal migliore",
      refs: [`Scarto massimo: ${report.costanza.scarto_max_ms ?? "—"} ms`, `Giri entro 0,5 s: ${report.costanza.giri_entro_mezzo_secondo}`],
    },
    {
      id: "degrado",
      label: "Degrado",
      valueNum: d.calcolabile ? d.pendenza_ms_giro : null,
      suffix: " ms/giro",
      decimals: 0,
      note: d.calcolabile ? `Dal giro ${d.dal_giro} · R² ${d.r_quadro}${d.significativo ? " · calo dimostrato" : ""}` : d.motivo ?? "Non calcolabile",
      detail: "Pendenza dei tempi dal giro migliore in poi (regressione lineare). Un calo conta solo se la retta spiega i dati (R² ≥ 0,3).",
      color: !d.calcolabile ? COLORS.muted : d.significativo ? STATE.warn : STATE.ok,
      series: giriDegrado.map((g) => (g.tempo_ms as number) / 1000),
      xs: giriDegrado.map((g) => g.numero),
      unit: "s",
      refs: d.calcolabile ? [`Giri considerati: ${d.giri_considerati}`, `Se continua per 10 giri: ${d.perdita_su_10_giri_ms} ms`] : [],
    },
    {
      id: "consumo",
      label: "Consumo",
      valueNum: report.carburante.calcolabile ? report.carburante.consumo_medio_l_giro : null,
      suffix: " l/giro",
      decimals: 2,
      note: report.carburante.calcolabile
        ? report.carburante.fonte === "manuale"
          ? `Inserito da te: media ripartita su ${giri(report.carburante.giri_misurati)}`
          : report.carburante.fonte === "setup"
            ? "Dal setup: stima salvata da ACC, non misurata"
            : `Misurato su ${giri(report.carburante.giri_misurati)}`
        : report.carburante.motivo ?? "Non calcolabile",
      detail: "Carburante usato giro per giro, misurato dal serbatoio registrato (non stimato).",
      color: report.carburante.calcolabile ? STATE.ok : COLORS.muted,
      series: conConsumo.map((g) => g.carburante_usato_l as number),
      xs: conConsumo.map((g) => g.numero),
      refLines: report.carburante.consumo_medio_l_giro ? [report.carburante.consumo_medio_l_giro] : undefined,
      unit: "l",
      refs: [],
    },
    finestraKpi("pressione", "Pressioni in finestra", gomme?.finestra_pressione ?? null, report),
    finestraKpi("temperatura", "Temperature al core", gomme?.finestra_temperatura ?? null, report),
  ];
}

// Pallino di stato: pulse discreto quando lo stato richiede attenzione.
function StatusDot({ color, pulse }: { color: string; pulse: boolean }) {
  const reduce = useReducedMotion();
  if (!pulse || reduce) return <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: color }} />;
  return (
    <motion.span
      className="h-1.5 w-1.5 shrink-0 rounded-full"
      style={{ background: color }}
      animate={{ opacity: [1, 0.35, 1], scale: [1, 1.25, 1] }}
      transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

function ValoreKpi({ kpi, size }: { kpi: Kpi; size: string }) {
  return (
    <div className={`block font-mono ${size}`} style={{ color: kpi.valueNum === null ? COLORS.muted : kpi.color }}>
      {kpi.valueNum === null ? "—" : kpi.display ?? <CountUp value={kpi.valueNum} decimals={kpi.decimals} suffix={kpi.suffix} />}
    </div>
  );
}

// Passo "nice" per l'asse Y (stile MoTeC): arrotonda a 1/2/5×10ⁿ.
function niceStep(range: number): number {
  const raw = (range > 1e-6 ? range : 1) / 4;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  const step = norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10;
  return step * mag;
}

// Grafico del dettaglio di un indicatore.
function KpiChart({
  series,
  xs,
  color,
  refLines,
  unit,
  height = 190,
  showTooltip = true,
}: {
  series: number[];
  xs?: number[];
  color: string;
  refLines?: number[];
  unit?: string;
  height?: number;
  showTooltip?: boolean;
}) {
  const rows = series.map((v, i) => ({ i: xs?.[i] ?? i + 1, v }));
  const pool = [...series, ...(refLines ?? [])];
  const lo = Math.min(...pool);
  const hi = Math.max(...pool);
  const pad = (hi - lo) * 0.15 || 1;
  const step = niceStep(hi - lo);
  const dLo = Math.floor((lo - pad) / step) * step;
  const dHi = Math.ceil((hi + pad) / step) * step;
  const ticks: number[] = [];
  for (let t = dLo, n = 0; t <= dHi + 1e-9 && n < 20; t += step, n++) ticks.push(Number(t.toFixed(6)));
  const decimals = step >= 1 ? 0 : step >= 0.1 ? 1 : 2;

  return (
    <div>
      {unit && <div className="mb-1 pl-1 font-mono text-[0.55rem] uppercase tracking-widest text-muted">{unit}</div>}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={rows} margin={{ top: 6, right: 16, bottom: 22, left: 4 }}>
          <CartesianGrid stroke={INSTRUMENT.grid} vertical={false} />
          <XAxis
            dataKey="i"
            stroke={INSTRUMENT.tick}
            tick={{ fill: COLORS.muted, fontSize: 10 }}
            label={{ value: "Giro", position: "insideBottom", offset: -10, style: { fill: COLORS.muted, fontSize: 10, textAnchor: "middle" } }}
          />
          <YAxis domain={[dLo, dHi]} ticks={ticks} tickFormatter={(n: number) => n.toFixed(decimals)} stroke={INSTRUMENT.tick} tick={{ fill: COLORS.muted, fontSize: 10 }} width={52} />
          {showTooltip && (
            <Tooltip
              contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.line}`, borderRadius: 8, fontSize: 12, boxShadow: "none" }}
              labelFormatter={(l) => `Giro ${l}`}
            />
          )}
          {(refLines ?? []).map((y, idx) => (
            <ReferenceLine key={idx} y={y} stroke={COLORS.muted} strokeDasharray="4 4" strokeWidth={1} />
          ))}
          <Line type="monotone" dataKey="v" name="valore" stroke={color} strokeWidth={2} dot={{ r: 2.5, fill: color, strokeWidth: 0 }} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Modal dettaglio KPI (in-page): valore + grafico + riferimenti + come si calcola.
function KpiModal({ kpi, onClose }: { kpi: Kpi; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="pw-scroll max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-line bg-surface p-6"
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 16, scale: 0.98 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">{kpi.label}</div>
          <button onClick={onClose} className="font-mono text-sm text-muted transition hover:text-accent" aria-label="Chiudi">
            ✕
          </button>
        </div>
        <div className="mt-2">
          <ValoreKpi kpi={kpi} size="text-4xl" />
        </div>
        <div className="mt-2 flex items-center gap-1.5 text-sm" style={{ color: kpi.valueNum === null ? COLORS.subtle : kpi.color }}>
          <StatusDot color={kpi.valueNum === null ? COLORS.muted : kpi.color} pulse={kpi.color === STATE.warn} />
          {kpi.note}
        </div>

        {kpi.series && kpi.series.length >= 2 && (
          <div className="mt-4 rounded-lg border border-line bg-inset p-3">
            <KpiChart series={kpi.series} xs={kpi.xs} color={kpi.color} refLines={kpi.refLines} unit={kpi.unit} />
          </div>
        )}

        {kpi.refs.length > 0 && (
          <div className="mt-4">
            <div className="mb-1.5 font-mono text-[0.55rem] uppercase tracking-widest text-muted">Riferimenti</div>
            <ul className="flex flex-col gap-1">
              {kpi.refs.map((r, idx) => (
                <li key={idx} className="flex items-center gap-2 font-mono text-[0.72rem] text-subtle">
                  <span className="h-1 w-1 shrink-0 rounded-full bg-line-strong" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="mt-4 border-t border-line pt-3 text-[0.8rem] leading-relaxed text-subtle">{kpi.detail}</p>
      </motion.div>
    </motion.div>
  );
}
