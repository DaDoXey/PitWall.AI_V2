"use client";

// Sessioni (L4 del rework dati): da dove entrano i dati, e l'archivio.
//
// Due percorsi, divisi per piattaforma (idea di Edoardo, 16/09/2026), che finiscono
// nello STESSO formato e nello STESSO motore di analisi:
// * PC — i file che ACC scrive (setup, risultati) e la telemetria registrata dal
//   backend mentre si gioca;
// * console — niente file né telemetria: il pilota scrive tempi (se li ha), setup e
//   soprattutto racconta la sessione fase per fase. Gigi ragiona su quello.
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import PageHeader from "@/components/ui/PageHeader";
import { Etichetta } from "@/components/ui/Verdetto";
import {
  ApiError,
  cancellaSessione,
  creaSessioneManuale,
  getRegistrazioni,
  getStatoRegistratore,
  importaMotec,
  importaRegistrazione,
  importaRisultati,
  importaSetup,
  type Mescola,
  type Partecipante,
  type Piattaforma,
  type Racconto,
  type Registrazione,
  type StatoRegistratore,
  urlEsportaMotec,
} from "@/lib/api";
import { useProfile } from "@/lib/profile";
import { useSessione } from "@/lib/sessione";
import { data, ETICHETTA_PIATTAFORMA, ETICHETTA_TIPO, etichettaFonte, giri, tempoGiro } from "@/lib/formato";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { CHIAVE_BOZZA_SETUP } from "@/lib/setup";

type Esito = { ok: boolean; testo: string } | null;

function messaggio(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 503) return "Su questa installazione l'import è spento (vetrina pubblica).";
    return e.message;
  }
  return fallback;
}

export default function SessioniPage() {
  const { platform, setPlatform } = useProfile();
  const [altroPercorso, setAltroPercorso] = useState(false);
  const console_ = platform === "playstation" || platform === "xbox";

  return (
    <div>
      <PageHeader title="Sessioni" subtitle="Da dove arrivano i dati · archivio" />

      {!platform && <SceltaPiattaforma onScelta={setPlatform} />}

      {platform && (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="flex flex-col gap-6">
          <motion.div variants={fadeInUp} className="flex flex-wrap items-center gap-2 text-sm text-subtle">
            Giochi su <span className="text-white">{ETICHETTA_PIATTAFORMA[platform]}</span>.
            <button
              type="button"
              onClick={() => setPlatform(console_ ? "pc" : "playstation")}
              className="font-mono text-[0.6rem] uppercase tracking-widest text-muted transition hover:text-white"
            >
              cambia
            </button>
          </motion.div>

          <motion.div variants={fadeInUp}>{console_ ? <PercorsoConsole piattaforma={platform} /> : <PercorsoPC />}</motion.div>

          <motion.div variants={fadeInUp}>
            <button
              type="button"
              onClick={() => setAltroPercorso((a) => !a)}
              className="font-mono text-[0.6rem] uppercase tracking-widest text-subtle transition hover:text-white"
            >
              {altroPercorso ? "▴ Nascondi" : "▾ Mostra"} anche il percorso {console_ ? "PC" : "console"}
            </button>
            {altroPercorso && (
              <div className="mt-3">{console_ ? <PercorsoPC /> : <PercorsoConsole piattaforma="playstation" />}</div>
            )}
          </motion.div>

          <motion.div variants={fadeInUp}>
            <Archivio />
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}

function Blocco({ titolo, sottotitolo, children }: { titolo: string; sottotitolo?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-line bg-surface p-4">
      <div className="font-mono text-xs uppercase tracking-wider text-subtle">{titolo}</div>
      {sottotitolo && <p className="mt-1 text-[0.78rem] text-muted">{sottotitolo}</p>}
      <div className="mt-3">{children}</div>
    </section>
  );
}

function SceltaPiattaforma({ onScelta }: { onScelta: (p: Piattaforma) => void }) {
  return (
    <Blocco titolo="Dove giochi ad ACC?" sottotitolo="Decide da dove arrivano i dati. L'analisi funziona in tutti e due i casi.">
      <div className="grid gap-2 sm:grid-cols-3">
        {(["pc", "playstation", "xbox"] as Piattaforma[]).map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onScelta(p)}
            className="rounded-lg border border-line bg-inset p-3 text-left transition hover:border-accent/60"
          >
            <div className="text-sm text-white">{ETICHETTA_PIATTAFORMA[p]}</div>
            <div className="mt-0.5 text-[0.72rem] text-muted">
              {p === "pc" ? "File e telemetria di ACC" : "Setup, tempi e racconto scritti da te"}
            </div>
          </button>
        ))}
      </div>
    </Blocco>
  );
}

// ─────────────────────────────────────────────
// Percorso PC
// ─────────────────────────────────────────────
function PercorsoPC() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ImportaFile />
      <Registratore />
      <div className="lg:col-span-2">
        <ImportaMotec />
      </div>
    </div>
  );
}

// Export MoTeC di ACC (L5). ACC li scrive solo su PC, in Documenti\Assetto Corsa
// Competizione\MoTeC, se nell'elettronica del setup «giri di telemetria» è sopra zero.
// Di solito sono giri di altri piloti: per questo di default sono «riferimento».
function ImportaMotec() {
  const { ricarica } = useSessione();
  const router = useRouter();
  const [ld, setLd] = useState<File | null>(null);
  const [ldx, setLdx] = useState<File | null>(null);
  const [setup, setSetup] = useState<File | null>(null);
  const [inizio, setInizio] = useState("");
  const [fine, setFine] = useState("");
  const [mescola, setMescola] = useState<Mescola | "">("");
  const [mio, setMio] = useState(false);
  const [lavoro, setLavoro] = useState(false);
  const [esito, setEsito] = useState<Esito>(null);

  const litri = (t: string) => {
    const n = Number(t.trim().replace(",", "."));
    return t.trim() && Number.isFinite(n) && n >= 0 ? n : null;
  };
  const lInizio = litri(inizio);
  const lFine = litri(fine);
  const soloUno = (lInizio === null) !== (lFine === null);
  const alRovescio = lInizio !== null && lFine !== null && lFine >= lInizio;

  async function importa() {
    if (!ld) return;
    setLavoro(true);
    setEsito(null);
    try {
      const r = await importaMotec({
        ld,
        ldx,
        setup,
        carburanteInizioL: lInizio,
        carburanteFineL: lFine,
        mescola: mescola || null,
        riferimento: !mio,
      });
      await ricarica(r.id);
      setEsito({ ok: true, testo: `Importato: ${giri(r.giri_con_tempo)} con tempo, ${r.assunzioni.length} note sui dati.` });
      router.push("/telemetry");
    } catch (e) {
      setEsito({ ok: false, testo: messaggio(e, "Import MoTeC non riuscito.") });
    } finally {
      setLavoro(false);
    }
  }

  const campo = "rounded-md border border-line bg-inset px-2 py-1.5 text-sm text-white placeholder:text-muted focus:border-accent focus:outline-none";
  const etichetta = "font-mono text-[0.6rem] uppercase tracking-widest text-muted";
  const inputFile =
    "block w-full text-xs text-subtle file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line-strong file:bg-raised file:px-3 file:py-1.5 file:text-xs file:text-white hover:file:border-accent";

  return (
    <Blocco
      titolo="Importa un export MoTeC"
      sottotitolo="Documenti\Assetto Corsa Competizione\MoTeC: il .ld porta i canali, il .ldx i passaggi sul traguardo. MoTeC non esporta posizione in pista né carburante: la posizione si ricava dalla velocità, il consumo lo dai tu o il setup."
    >
      <div className="grid gap-3 md:grid-cols-3">
        <label className="flex flex-col gap-1">
          <span className={etichetta}>File .ld · obbligatorio</span>
          <input type="file" accept=".ld" onChange={(e) => setLd(e.target.files?.[0] ?? null)} className={inputFile} />
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>File .ldx · i giri</span>
          <input type="file" accept=".ldx" onChange={(e) => setLdx(e.target.files?.[0] ?? null)} className={inputFile} />
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Setup .json · facoltativo</span>
          <input type="file" accept=".json,application/json" onChange={(e) => setSetup(e.target.files?.[0] ?? null)} className={inputFile} />
        </label>
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Litri a inizio sessione</span>
          <input value={inizio} onChange={(e) => setInizio(e.target.value)} inputMode="decimal" placeholder="es. 60" className={campo} />
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Litri a fine sessione</span>
          <input value={fine} onChange={(e) => setFine(e.target.value)} inputMode="decimal" placeholder="es. 24.5" className={campo} />
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Gomme</span>
          <select value={mescola} onChange={(e) => setMescola(e.target.value as Mescola | "")} className={campo}>
            <option value="">Dal setup, o non indicate</option>
            <option value="asciutto">Da asciutto</option>
            <option value="bagnato">Da bagnato</option>
          </select>
        </label>
        <label className="flex items-end gap-2 pb-1.5 text-[0.8rem] text-subtle">
          <input type="checkbox" checked={mio} onChange={(e) => setMio(e.target.checked)} />
          È un giro mio (non un riferimento)
        </label>
      </div>
      <p className="mt-2 text-[0.7rem] text-muted">
        Consumo: i litri che scrivi valgono più del setup, e il report dice sempre da dove viene il numero. Senza .ldx i giri
        non si conoscono, salvo un giro ritagliato in MoTeC i2 lungo quanto la pista.
      </p>
      {soloUno && <p className="mt-1 text-[0.72rem] text-warn">Per il consumo servono i litri a inizio e a fine.</p>}
      {alRovescio && <p className="mt-1 text-[0.72rem] text-warn">A fine sessione ci sono più litri che all&apos;inizio.</p>}
      <button
        type="button"
        disabled={!ld || lavoro || soloUno || alRovescio}
        onClick={importa}
        className="mt-3 rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {lavoro ? "Import…" : "Importa"}
      </button>
      <Esito esito={esito} />
    </Blocco>
  );
}

function ImportaFile() {
  const { ricarica, catalogo } = useSessione();
  const router = useRouter();
  const [tipo, setTipo] = useState<"risultati" | "setup">("risultati");
  const [file, setFile] = useState<File | null>(null);
  const [pista, setPista] = useState("");
  const [partecipanti, setPartecipanti] = useState<Partecipante[] | null>(null);
  const [lavoro, setLavoro] = useState(false);
  const [esito, setEsito] = useState<Esito>(null);

  async function importa(carId?: number) {
    if (!file) return;
    setLavoro(true);
    setEsito(null);
    try {
      const r = tipo === "setup" ? await importaSetup(file, pista || undefined) : await importaRisultati(file, carId);
      setPartecipanti(null);
      await ricarica(r.id);
      setEsito({ ok: true, testo: `Sessione importata${r.assunzioni.length ? ` (${r.assunzioni.length} note sui dati)` : ""}.` });
      router.push("/");
    } catch (e) {
      if (e instanceof ApiError && e.status === 409 && e.detail && typeof e.detail === "object" && "partecipanti" in e.detail) {
        setPartecipanti((e.detail as { partecipanti: Partecipante[] }).partecipanti);
        setEsito({ ok: true, testo: "Il file contiene più vetture: scegli la tua." });
      } else {
        setEsito({ ok: false, testo: messaggio(e, "Import non riuscito.") });
      }
    } finally {
      setLavoro(false);
    }
  }

  return (
    <Blocco
      titolo="Importa un file di ACC"
      sottotitolo="Risultati: Documenti\Assetto Corsa Competizione\results. Setup: Documenti\Assetto Corsa Competizione\Setups\<auto>\<pista>."
    >
      <div className="mb-3 inline-flex rounded-md border border-line bg-inset p-0.5">
        {(["risultati", "setup"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => {
              setTipo(t);
              setPartecipanti(null);
              setEsito(null);
            }}
            className={`rounded px-3 py-1.5 text-sm transition ${tipo === t ? "bg-accent text-white" : "text-subtle hover:text-white"}`}
          >
            {t === "risultati" ? "Risultati" : "Setup"}
          </button>
        ))}
      </div>
      <input
        type="file"
        accept=".json,application/json"
        onChange={(e) => {
          setFile(e.target.files?.[0] ?? null);
          setPartecipanti(null);
          setEsito(null);
        }}
        className="block w-full text-xs text-subtle file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line-strong file:bg-raised file:px-3 file:py-1.5 file:text-xs file:text-white hover:file:border-accent"
      />
      {tipo === "setup" && (
        <label className="mt-3 flex flex-col gap-1">
          <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">Pista (il file del setup non la scrive)</span>
          <select
            value={pista}
            onChange={(e) => setPista(e.target.value)}
            className="rounded-md border border-line bg-inset px-2 py-1.5 text-sm text-white focus:border-accent focus:outline-none"
          >
            <option value="">Non indicata</option>
            {(catalogo?.tracks ?? []).map((t) => (
              <option key={t.id} value={t.id}>
                {t.short_name || t.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <button
        type="button"
        disabled={!file || lavoro}
        onClick={() => importa()}
        className="mt-3 rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {lavoro ? "Import…" : "Importa"}
      </button>
      {partecipanti && (
        <div className="mt-3 flex flex-col gap-1.5">
          {partecipanti.map((p) => (
            <button
              key={p.car_id}
              type="button"
              onClick={() => importa(p.car_id)}
              className="flex items-center justify-between rounded-md border border-line bg-inset px-3 py-2 text-left text-sm transition hover:border-accent/60"
            >
              <span className="text-white">
                {p.numero !== null ? `#${p.numero} · ` : ""}
                {p.pilota ?? "Pilota sconosciuto"}
              </span>
              <span className="font-mono text-[0.62rem] text-muted">{giri(p.giri)}</span>
            </button>
          ))}
        </div>
      )}
      <Esito esito={esito} />
    </Blocco>
  );
}

function Registratore() {
  const { ricarica, demoId } = useSessione();
  const router = useRouter();
  const [stato, setStato] = useState<StatoRegistratore | null>(null);
  const [registrazioni, setRegistrazioni] = useState<Registrazione[]>([]);
  const [esito, setEsito] = useState<Esito>(null);

  useEffect(() => {
    let vivo = true;
    const aggiorna = () => {
      getStatoRegistratore()
        .then((s) => vivo && setStato(s))
        .catch(() => vivo && setStato(null));
      getRegistrazioni()
        // La registrazione della demo è già nell'archivio: non si propone di importarla.
        .then((r) => vivo && setRegistrazioni(r.sessioni.filter((s) => s.id !== demoId)))
        .catch(() => vivo && setRegistrazioni([]));
    };
    aggiorna();
    const timer = setInterval(aggiorna, 5000);
    return () => {
      vivo = false;
      clearInterval(timer);
    };
  }, [demoId]);

  async function importa(id: string) {
    setEsito(null);
    try {
      const r = await importaRegistrazione(id);
      await ricarica(r.id_sessione);
      router.push("/");
    } catch (e) {
      setEsito({ ok: false, testo: messaggio(e, "Import della registrazione non riuscito.") });
    }
  }

  return (
    <Blocco
      titolo="Telemetria registrata"
      sottotitolo="Il backend legge la shared memory di ACC mentre giri: nessun programma da installare, si avvia da solo."
    >
      {!stato ? (
        <p className="text-sm text-subtle">Stato del registratore non disponibile.</p>
      ) : !stato.abilitato ? (
        <p className="text-sm text-subtle">Registratore spento su questa installazione.</p>
      ) : (
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`h-2 w-2 rounded-full ${stato.in_registrazione ? "bg-accent" : stato.agganciato ? "bg-ok" : "bg-line-strong"}`}
          />
          <span className="text-white">
            {stato.in_registrazione
              ? `In registrazione · ${stato.sessione?.campioni ?? 0} campioni`
              : stato.agganciato
                ? "ACC agganciato, in attesa della sessione"
                : "In attesa di ACC"}
          </span>
        </div>
      )}
      <div className="mt-3 flex flex-col gap-1.5">
        {registrazioni.length === 0 ? (
          <p className="text-[0.78rem] text-muted">Nessuna registrazione da importare.</p>
        ) : (
          registrazioni.map((r) => (
            <div key={r.id} className="flex items-center justify-between gap-2 rounded-md border border-line bg-inset px-3 py-2">
              <span className="min-w-0">
                <span className="block truncate text-sm text-white">
                  {r.pista ?? "pista ?"} · {r.vettura ?? "vettura ?"}
                </span>
                <span className="font-mono text-[0.6rem] text-muted">
                  {data(r.inizio)} · {r.campioni} campioni{r.canali_rimossi ? " · canali rimossi" : ""}
                </span>
              </span>
              <button
                type="button"
                disabled={!r.ha_canali}
                onClick={() => importa(r.id)}
                className="shrink-0 rounded-md border border-line-strong px-2.5 py-1 font-mono text-[0.6rem] uppercase tracking-widest text-white transition hover:border-accent disabled:opacity-40"
              >
                Analizza
              </button>
            </div>
          ))
        )}
      </div>
      <Esito esito={esito} />
    </Blocco>
  );
}

// ─────────────────────────────────────────────
// Percorso console
// ─────────────────────────────────────────────
const TIPI = [
  { value: "FP", label: "Prove" },
  { value: "Q", label: "Qualifica" },
  { value: "R", label: "Gara" },
];

const FASI: { key: keyof Racconto; label: string; aiuto: string }[] = [
  { key: "andamento", label: "Com'è andata la sessione", aiuto: "Dall'inizio alla fine: gomme fredde, quando è arrivato il passo, quando ha iniziato a calare…" },
  { key: "frenata", label: "Frenata", aiuto: "Bloccaggi, instabilità, pedale lungo…" },
  { key: "ingresso", label: "Ingresso curva", aiuto: "Sottosterzo, retrotreno che si alleggerisce…" },
  { key: "centro", label: "Centro curva", aiuto: "Va larga, chiude la traiettoria…" },
  { key: "uscita", label: "Uscita curva", aiuto: "Trazione, pattinamento, sovrasterzo in accelerazione…" },
  { key: "gomme", label: "Gomme", aiuto: "Temperature e pressioni lette nel gioco, sensazioni di grip…" },
];

/** «1:47.820» o «107.82» → millisecondi. null se non si legge. */
function leggiTempo(testo: string): number | null {
  const t = testo.trim().replace(",", ".");
  const m = /^(?:(\d+):)?(\d{1,2}(?:\.\d{1,3})?)$/.exec(t);
  if (!m) return null;
  const ms = Math.round(((m[1] ? Number(m[1]) * 60 : 0) + Number(m[2])) * 1000);
  return ms > 0 ? ms : null;
}

function PercorsoConsole({ piattaforma }: { piattaforma: Piattaforma }) {
  const { ricarica, catalogo } = useSessione();
  const router = useRouter();
  const [car, setCar] = useState("");
  const [track, setTrack] = useState("");
  const [tipo, setTipo] = useState("FP");
  const [mescola, setMescola] = useState<Mescola | "">("");
  const [tempi, setTempi] = useState("");
  const [racconto, setRacconto] = useState<Racconto>({});
  const [curveCritiche, setCurveCritiche] = useState("");
  const [bozzaSetup, setBozzaSetup] = useState<Record<string, number> | null>(null);
  const [usaSetup, setUsaSetup] = useState(true);
  const [lavoro, setLavoro] = useState(false);
  const [esito, setEsito] = useState<Esito>(null);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(CHIAVE_BOZZA_SETUP);
      if (raw) setBozzaSetup(JSON.parse(raw) as Record<string, number>);
    } catch {
      /* nessuna bozza */
    }
  }, []);

  const righe = useMemo(() => tempi.split(/\n+/).map((r) => r.trim()).filter(Boolean), [tempi]);
  const illeggibili = righe.filter((r) => leggiTempo(r) === null);

  async function crea() {
    setLavoro(true);
    setEsito(null);
    const curve = curveCritiche.split(",").map((c) => c.trim()).filter(Boolean);
    try {
      const r = await creaSessioneManuale({
        piattaforma,
        car: car || null,
        track: track || null,
        tipo_sessione: tipo,
        mescola: mescola || null,
        giri: righe.map((riga, i) => ({ numero: i + 1, tempo_ms: leggiTempo(riga) })),
        setup: usaSetup && bozzaSetup ? bozzaSetup : undefined,
        racconto: { ...racconto, curve_critiche: curve },
      });
      try {
        sessionStorage.removeItem(CHIAVE_BOZZA_SETUP);
      } catch {
        /* no-op */
      }
      await ricarica(r.id);
      router.push("/console");
    } catch (e) {
      setEsito({ ok: false, testo: messaggio(e, "Sessione non creata.") });
    } finally {
      setLavoro(false);
    }
  }

  const campo = "rounded-md border border-line bg-inset px-2 py-1.5 text-sm text-white placeholder:text-muted focus:border-accent focus:outline-none";
  const etichetta = "font-mono text-[0.6rem] uppercase tracking-widest text-muted";

  return (
    <Blocco
      titolo={`Nuova sessione da ${ETICHETTA_PIATTAFORMA[piattaforma]}`}
      sottotitolo="Su console ACC non scrive file né telemetria: il motore analizza i tempi che inserisci, e Gigi ragiona sul tuo racconto. Più sei preciso, più la risposta è mirata."
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Vettura</span>
          <select value={car} onChange={(e) => setCar(e.target.value)} className={campo}>
            <option value="">Non indicata</option>
            {(catalogo?.cars ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Pista</span>
          <select value={track} onChange={(e) => setTrack(e.target.value)} className={campo}>
            <option value="">Non indicata</option>
            {(catalogo?.tracks ?? []).map((t) => (
              <option key={t.id} value={t.id}>
                {t.short_name || t.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Sessione</span>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)} className={campo}>
            {TIPI.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Gomme</span>
          <select value={mescola} onChange={(e) => setMescola(e.target.value as Mescola | "")} className={campo}>
            <option value="">Non indicate</option>
            <option value="asciutto">Da asciutto</option>
            <option value="bagnato">Da bagnato</option>
          </select>
        </label>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <label className="flex flex-col gap-1">
          <span className={etichetta}>Tempi sul giro · uno per riga</span>
          <textarea
            value={tempi}
            onChange={(e) => setTempi(e.target.value)}
            rows={8}
            placeholder={"1:49.412\n1:48.301\n1:47.945"}
            className={`${campo} font-mono`}
          />
          <span className="text-[0.68rem] text-muted">
            Facoltativi. Dalla classifica o dalla schermata dei tempi di fine sessione.
          </span>
          {illeggibili.length > 0 && (
            <span className="text-[0.7rem] text-warn">Non leggo: {illeggibili.slice(0, 3).join(", ")}</span>
          )}
        </label>
        <div className="flex flex-col gap-3 lg:col-span-2">
          {FASI.map((f) => (
            <label key={f.key} className="flex flex-col gap-1">
              <span className={etichetta}>{f.label}</span>
              <textarea
                value={(racconto[f.key] as string | undefined) ?? ""}
                onChange={(e) => setRacconto((r) => ({ ...r, [f.key]: e.target.value || null }))}
                rows={f.key === "andamento" ? 3 : 2}
                placeholder={f.aiuto}
                className={campo}
              />
            </label>
          ))}
          <label className="flex flex-col gap-1">
            <span className={etichetta}>Curve critiche · separate da virgola</span>
            <input value={curveCritiche} onChange={(e) => setCurveCritiche(e.target.value)} placeholder="Variante 1, Ascari" className={campo} />
          </label>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-line bg-inset p-3 text-[0.78rem] text-subtle">
        {bozzaSetup ? (
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={usaSetup} onChange={(e) => setUsaSetup(e.target.checked)} />
            Allega il setup preparato nella pagina Setup ({Object.keys(bozzaSetup).length} parametri)
          </label>
        ) : (
          <>
            Il setup si prepara nella pagina{" "}
            <Link href="/setup" className="text-white underline-offset-2 hover:underline">
              Setup
            </Link>{" "}
            (a mano o da screenshot) e da lì si porta qui con «Crea una sessione con questo setup».
          </>
        )}
      </div>

      <button
        type="button"
        disabled={lavoro || illeggibili.length > 0}
        onClick={crea}
        className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
      >
        {lavoro ? "Creazione…" : "Crea la sessione e chiedi a Gigi"}
      </button>
      <Esito esito={esito} />
    </Blocco>
  );
}

// ─────────────────────────────────────────────
// Archivio
// ─────────────────────────────────────────────
function Archivio() {
  const { elenco, idSessione, apri, ricarica, nomi } = useSessione();
  const [esito, setEsito] = useState<Esito>(null);
  // Cancellare è irreversibile: il primo click chiede conferma sul bottone stesso.
  const [daConfermare, setDaConfermare] = useState<string | null>(null);
  const router = useRouter();

  async function cancella(id: string) {
    setEsito(null);
    if (daConfermare !== id) {
      setDaConfermare(id);
      return;
    }
    setDaConfermare(null);
    try {
      await cancellaSessione(id);
      await ricarica(id === idSessione ? undefined : idSessione ?? undefined);
    } catch (e) {
      setEsito({ ok: false, testo: messaggio(e, "Sessione non cancellata.") });
    }
  }

  return (
    <Blocco titolo={`Archivio · ${elenco?.length ?? 0} sessioni`}>
      <div className="flex flex-col gap-1.5">
        {(elenco ?? []).map((s) => {
          const aperta = s.id === idSessione;
          return (
            <div
              key={s.id}
              className={`flex flex-wrap items-center gap-3 rounded-lg border px-3 py-2 ${aperta ? "border-accent/60 bg-accent/[0.05]" : "border-line bg-inset"}`}
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm text-white">
                    {nomi.pista(s.track)} · {nomi.vettura(s.car)}
                  </span>
                  <Etichetta testo={etichettaFonte(s.fonte, s.piattaforma)} accesa={s.demo} />
                  {s.riferimento && <Etichetta testo="riferimento" />}
                  {s.ritaglio_i2 && <Etichetta testo="ritaglio i2" />}
                  {s.ha_canali && <Etichetta testo="telemetria" />}
                  {s.ha_setup && <Etichetta testo="setup" />}
                  {s.ha_racconto && <Etichetta testo="racconto" />}
                </div>
                <div className="mt-0.5 font-mono text-[0.62rem] text-muted">
                  {ETICHETTA_TIPO[s.tipo_sessione] ?? "Sessione"} · {giri(s.giri)} · best {tempoGiro(s.miglior_giro_ms)}
                  {!s.demo ? ` · ${data(s.iniziata_il ?? s.importato_il)}` : ""}
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  apri(s.id);
                  router.push("/");
                }}
                className="rounded-md border border-line-strong px-2.5 py-1 font-mono text-[0.6rem] uppercase tracking-widest text-white transition hover:border-accent"
              >
                {aperta ? "Aperta" : "Apri"}
              </button>
              {s.ha_canali && (
                <a
                  href={urlEsportaMotec(s.id)}
                  download
                  className="rounded-md px-2 py-1 font-mono text-[0.6rem] uppercase tracking-widest text-subtle transition hover:text-white"
                  title="Scarica .ld + .ldx da aprire in MoTeC i2 (con carburante, temperature al core e posizione, se registrati)"
                >
                  MoTeC ↓
                </a>
              )}
              {!s.demo && (
                <button
                  type="button"
                  onClick={() => cancella(s.id)}
                  onBlur={() => setDaConfermare((d) => (d === s.id ? null : d))}
                  className={`rounded-md px-2 py-1 font-mono text-[0.6rem] uppercase tracking-widest transition ${
                    daConfermare === s.id ? "border border-accent text-accent" : "text-muted hover:text-accent"
                  }`}
                  title="Cancella la sessione dall'archivio"
                >
                  {daConfermare === s.id ? "Confermi?" : "Cancella"}
                </button>
              )}
            </div>
          );
        })}
      </div>
      <Esito esito={esito} />
    </Blocco>
  );
}

function Esito({ esito }: { esito: Esito }) {
  if (!esito) return null;
  return <p className={`mt-2 text-[0.78rem] ${esito.ok ? "text-ok" : "text-warn"}`}>{esito.testo}</p>;
}
