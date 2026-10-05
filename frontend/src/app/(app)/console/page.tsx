"use client";

// Engineer Console (#060, 30/09/2026): Gigi alla radio del muretto. Il debrief della
// sessione fase per fase (motore: analisi/debrief.py), la striscia dei giri con le fasi
// da ascoltare e da ritagliare, la pista della fase in onda, la prima cosa da fare
// fissata in cima, le domande preparate e il rapporto completo a 5 sezioni.
// Una cosa alla volta: in onda c'è un solo messaggio, quello della fase ascoltata; le
// domande e le risposte si accodano sotto, come una conversazione.
// Scelta di Edoardo fra tre concetti: la radio (B) + il tavolo del debrief (C) + una
// cosa alla volta (A).
// Gigi dal vivo (#061): con PITWALL_CHAT_LIVE acceso la casella della radio scrive al
// modello, che risponde in streaming sulla sessione aperta (12 domande a conversazione).
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import MappaFase from "@/components/console/MappaFase";
import Radio from "@/components/console/Radio";
import RapportoCompleto from "@/components/console/RapportoCompleto";
import StrisciaGiri from "@/components/console/StrisciaGiri";
import ServizioFermo from "@/components/ui/ServizioFermo";
import {
  ApiError,
  chatConGigi,
  getConfronto,
  getDebrief,
  getSetupParams,
  getStatoBackend,
  salvaTagli,
  type Confronto,
  type Debrief,
} from "@/lib/api";
import {
  alternaTaglio,
  DOMANDE,
  domandePer,
  MAX_DOMANDE_DAL_VIVO,
  messaggiIniziali,
  rispondi,
  rispondiConfronto,
  titoloPrimaCosa,
  type Domanda,
  type Messaggio,
} from "@/lib/debrief";
import { SERVIZIO_FERMO } from "@/lib/errori";
import { tempoGiro } from "@/lib/formato";
import { fadeInUp } from "@/lib/motion";
import { profileContextLine, useProfile } from "@/lib/profile";
import { useSessione } from "@/lib/sessione";
import type { SetupParams } from "@/lib/setup";

const PASSO_RIPRODUZIONE_MS = 4500;

// All'apertura va in onda la fase dove c'è più in ballo (scarto medio più alto).
function faseIniziale(d: Debrief): number {
  let scelta = -1;
  d.fasi.forEach((f, i) => {
    if (f.tipo === "giro") return;
    if (scelta < 0 || (f.delta_medio_ms ?? 0) > (d.fasi[scelta].delta_medio_ms ?? 0)) scelta = i;
  });
  return Math.max(scelta, 0);
}

export default function ConsolePage() {
  const { idSessione, sessione, report, nomi, ricarica, errore: erroreSessione } = useSessione();
  const { profile } = useProfile();
  const [debrief, setDebrief] = useState<Debrief | null>(null);
  const [confronto, setConfronto] = useState<Confronto | null>(null);
  const [errore, setErrore] = useState<string | null>(null);
  const [tentativo, setTentativo] = useState(0); // «Riprova»: rifà le richieste senza ricaricare la pagina
  const [attiva, setAttiva] = useState(0);
  const [inRiproduzione, setInRiproduzione] = useState(false);
  const [occupato, setOccupato] = useState(false);
  const [conversazione, setConversazione] = useState<Messaggio[]>([]);
  const [params, setParams] = useState<SetupParams | null>(null);
  const [rapporto, setRapporto] = useState(false);
  const [dalVivo, setDalVivo] = useState(false);
  const [inRisposta, setInRisposta] = useState(false);
  const interrompi = useRef<AbortController | null>(null);

  const riparti = useCallback((d: Debrief) => {
    interrompi.current?.abort();
    interrompi.current = null;
    setInRisposta(false);
    setDebrief(d);
    setConversazione([]);
    setAttiva(faseIniziale(d));
    setInRiproduzione(false);
  }, []);

  useEffect(() => {
    if (!idSessione) return;
    let vivo = true;
    setDebrief(null);
    setErrore(null);
    getDebrief(idSessione)
      .then((d) => vivo && riparti(d))
      .catch(() => vivo && setErrore(SERVIZIO_FERMO));
    return () => {
      vivo = false;
    };
  }, [idSessione, riparti, tentativo]);

  // La sessione precedente sulla stessa pista e vettura: se c'è, compare «Sono migliorato?».
  useEffect(() => {
    if (!idSessione) return;
    let vivo = true;
    setConfronto(null);
    getConfronto(idSessione)
      .then((c) => vivo && setConfronto(c))
      .catch(() => vivo && setConfronto(null));
    return () => {
      vivo = false;
    };
  }, [idSessione]);

  // Gigi dal vivo c'è solo se il backend ha la chat accesa (interruttore suo e chiave).
  useEffect(() => {
    getStatoBackend()
      .then((s) => setDalVivo(Boolean(s.chat_live)))
      .catch(() => setDalVivo(false));
  }, []);

  // Si cambia sessione (o pagina) mentre Gigi risponde: la risposta si interrompe.
  useEffect(() => () => interrompi.current?.abort(), [idSessione]);

  // Le regole della vettura: la prima cosa da fare si dice in click, quando si può.
  useEffect(() => {
    if (!report?.car) return;
    getSetupParams(report.car)
      .then((d) => setParams(d as SetupParams))
      .catch(() => setParams(null));
  }, [report?.car]);

  // Il replay: una fase dopo l'altra, finché non si mette in pausa o si sceglie una fase.
  useEffect(() => {
    if (!inRiproduzione || !debrief) return;
    const t = setInterval(() => setAttiva((a) => (a + 1) % debrief.fasi.length), PASSO_RIPRODUZIONE_MS);
    return () => clearInterval(t);
  }, [inRiproduzione, debrief]);

  const vaiAFase = (i: number) => {
    if (!debrief || !debrief.fasi.length) return;
    setInRiproduzione(false);
    setAttiva(Math.min(Math.max(i, 0), debrief.fasi.length - 1));
  };

  const chiedi = (d: Domanda) => {
    if (!debrief) return;
    setInRiproduzione(false);
    const n = Date.now();
    const tu: Messaggio = { id: `tu-${n}`, da: "tu", testo: DOMANDE.find((x) => x.id === d)?.testo ?? "" };
    // «Perché?» subito dopo «Sono migliorato?» chiede le prove del confronto, non della fase.
    const ultimaDiGigi = [...conversazione].reverse().find((m) => m.da === "gigi");
    if (confronto && (d === "migliorato" || (d === "perche" && ultimaDiGigi?.confronto))) {
      const r = rispondiConfronto(confronto, d === "perche");
      setConversazione((c) => [...c, tu, { id: `gigi-${n}`, da: "gigi", testo: r.testo, prova: r.prova, confronto: d === "migliorato" }]);
      return;
    }
    if (d === "migliorato") return;
    const r = rispondi(debrief, d, attiva);
    setConversazione((c) => [
      ...c,
      tu,
      // La prova, numero per numero, esce solo quando la si chiede.
      { id: `gigi-${n}`, da: "gigi", testo: r.testo, prova: d === "perche" ? r.prova : undefined, fase: r.fase },
    ]);
    if (r.fase !== undefined) setAttiva(r.fase);
  };

  // Una domanda scritta a Gigi dal vivo: al modello va solo la conversazione dal vivo
  // (le risposte preparate vengono dal debrief, che il modello ha già nel contesto).
  const scrivi = async (testo: string) => {
    if (!idSessione || inRisposta) return;
    const n = Date.now();
    const tu: Messaggio = { id: `tu-${n}`, da: "tu", testo, dalVivo: true };
    const idRisposta = `gigi-${n}`;
    const storia = [...conversazione.filter((m) => m.dalVivo && !m.errore && m.testo), tu];
    const segna = (cambia: (m: Messaggio) => Messaggio, anche?: string) =>
      setConversazione((c) => c.map((m) => (m.id === idRisposta || m.id === anche ? cambia(m) : m)));
    setConversazione((c) => [...c, tu, { id: idRisposta, da: "gigi", testo: "", dalVivo: true }]);
    setInRisposta(true);
    setInRiproduzione(false);
    const controllo = new AbortController();
    interrompi.current = controllo;
    let ricevuto = "";
    try {
      await chatConGigi(
        idSessione,
        {
          messages: storia.map((m) => ({ role: m.da === "tu" ? ("user" as const) : ("assistant" as const), content: m.testo })),
          fase: attiva,
          profile: profile ? profileContextLine(profile) : undefined,
        },
        (pezzo) => {
          ricevuto += pezzo;
          segna((m) => ({ ...m, testo: m.testo + pezzo }));
        },
        controllo.signal,
      );
      // Risposta vuota, o il messaggio di guasto di agent.py: non è una risposta di Gigi.
      if (!ricevuto.trim()) throw new Error("Gigi non ha risposto: riprova.");
      if (ricevuto.startsWith("⚠️")) segna((m) => ({ ...m, errore: true }), tu.id);
    } catch (e) {
      if (controllo.signal.aborted) return;
      const motivo =
        e instanceof ApiError || (e instanceof Error && e.message.startsWith("Gigi non ha risposto"))
          ? e.message
          : "Collegamento con Gigi caduto: riprova.";
      segna((m) => (m.id === idRisposta ? { ...m, testo: motivo, errore: true } : { ...m, errore: true }), tu.id);
      if (e instanceof ApiError && e.status === 503) setDalVivo(false);
    } finally {
      if (interrompi.current === controllo) {
        interrompi.current = null;
        setInRisposta(false);
      }
    }
  };

  const taglia = async (tagli: number[] | null) => {
    if (!idSessione || occupato) return;
    setOccupato(true);
    setErrore(null);
    try {
      riparti(await salvaTagli(idSessione, tagli));
    } catch (e) {
      setErrore(e instanceof ApiError ? e.message : "Fasi non salvate.");
    } finally {
      setOccupato(false);
    }
  };

  const titoloPrima = useMemo(
    () => (debrief?.prima_cosa ? titoloPrimaCosa(debrief.prima_cosa, params) : null),
    [debrief, params],
  );
  const faseInOnda = debrief?.fasi[attiva];
  const messaggioDiFase = useMemo(() => {
    const m = debrief ? messaggiIniziali(debrief)[attiva] : undefined;
    return m && { ...m, prova: undefined };
  }, [debrief, attiva]);

  const intestazione = (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-full border border-[#5a0f1d] bg-[#1a0509]">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#E8002D" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M4 14v-2a8 8 0 0 1 16 0v2" />
            <rect x="3" y="14" width="4" height="6" rx="1.5" />
            <rect x="17" y="14" width="4" height="6" rx="1.5" />
            <path d="M19 20a4 4 0 0 1-4 2h-2" />
          </svg>
        </span>
        <div>
          <h1 className="font-display text-[0.95rem] font-bold tracking-[0.14em]">
            GIGI <span className="text-accent">· RADIO</span>
          </h1>
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.16em] text-muted">
            Debrief{sessione ? ` · ${nomi.pista(sessione.track)} · ${nomi.vettura(sessione.car)}` : ""}
            {debrief ? ` · ${debrief.giri.length} giri di ritmo` : ""}
          </p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-5">
        {debrief?.in_ballo_ms != null && report?.ritmo.miglior_giro_ms != null && (
          <div
            className="flex items-center gap-3 rounded-xl border border-[#4a3a12] bg-[#17130a] px-3.5 py-1.5"
            title={`La distanza fra la tua media (${tempoGiro(report.ritmo.media_ms)}) e il tuo giro migliore (${tempoGiro(report.ritmo.miglior_giro_ms)})`}
          >
            <div className="flex flex-col">
              <span className="font-mono text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-warn">Distacco</span>
              <span className="font-mono text-[0.54rem] tracking-[0.06em] text-muted">media · giro migliore</span>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-display text-2xl font-bold leading-none text-warn">+{(debrief.in_ballo_ms / 1000).toFixed(3)} s</span>
              <span className="font-mono text-[0.62rem] text-muted">a giro</span>
            </div>
          </div>
        )}
        <button
          type="button"
          onClick={() => setRapporto(true)}
          disabled={!idSessione}
          className="rounded-md border border-line-strong px-3 py-1.5 font-mono text-[0.58rem] uppercase tracking-widest text-subtle transition hover:border-accent hover:text-white"
        >
          Rapporto completo
        </button>
      </div>
    </div>
  );

  // Servizio fermo all'apertura: non c'è una sessione perché l'elenco non è arrivato, non
  // perché il pilota non ne ha (prima qui si leggeva «Nessuna sessione aperta»).
  if (!idSessione && erroreSessione === SERVIZIO_FERMO)
    return (
      <div>
        {intestazione}
        <ServizioFermo onRiprova={() => ricarica()} />
      </div>
    );
  if (!idSessione)
    return (
      <div>
        {intestazione}
        <p className="text-sm text-subtle">
          Nessuna sessione aperta: aprine una da{" "}
          <Link href="/sessioni" className="text-white underline-offset-2 hover:underline">
            Sessioni
          </Link>
          .
        </p>
      </div>
    );

  return (
    <div className="flex h-[calc(100vh-4rem)] min-h-[520px] flex-col">
      {intestazione}
      {errore === SERVIZIO_FERMO ? (
        <ServizioFermo
          className="mb-3"
          onRiprova={() => {
            ricarica();
            setTentativo((t) => t + 1);
          }}
        />
      ) : (
        errore && <p className="mb-3 text-sm text-warn">{errore}</p>
      )}

      {!debrief ? (
        !errore && <p className="text-sm text-subtle">Gigi sta riascoltando la sessione…</p>
      ) : (
        <motion.div variants={fadeInUp} initial="hidden" animate="visible" className="flex min-h-0 flex-1 gap-5">
          <div className="flex min-h-0 min-w-0 flex-[1.1] flex-col gap-3">
            {debrief.fasi.length > 0 ? (
              <StrisciaGiri
                debrief={debrief}
                attiva={attiva}
                inRiproduzione={inRiproduzione}
                occupato={occupato}
                onFase={vaiAFase}
                onPlay={() => setInRiproduzione((p) => !p)}
                onTaglio={(giro) => taglia(alternaTaglio(debrief.tagli, giro))}
                onFasiDiGigi={() => taglia(null)}
              />
            ) : null}
            {debrief.nota && <p className="-mt-1 font-mono text-[0.6rem] text-muted">{debrief.nota}</p>}
            <MappaFase fase={faseInOnda} />
          </div>

          <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-3">
            {debrief.prima_cosa && titoloPrima && (
              <div className="flex items-center gap-4 rounded-2xl border border-[#5a0f1d] bg-[#140609] py-3 pl-4 pr-3">
                <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                  <span className="font-mono text-[0.56rem] uppercase tracking-[0.18em] text-accent">La prima cosa da fare</span>
                  <span className="text-[1.05rem] font-bold leading-snug tracking-tight" title={debrief.prima_cosa.titolo}>
                    {titoloPrima}
                  </span>
                </div>
                {Object.keys(debrief.prima_cosa.parametri).length > 0 && (
                  <Link
                    href="/setup"
                    className="shrink-0 rounded-full bg-accent px-4 py-2 text-[0.8rem] font-semibold text-white transition hover:bg-accent-hover"
                  >
                    Nel setup →
                  </Link>
                )}
              </div>
            )}
            <Radio
              messaggio={messaggioDiFase}
              conversazione={conversazione}
              domande={domandePer(confronto)}
              nomeFase={faseInOnda?.nome}
              dalVivo={dalVivo}
              inRisposta={inRisposta}
              domandeDalVivo={conversazione.filter((m) => m.da === "tu" && m.dalVivo && !m.errore).length}
              maxDomande={MAX_DOMANDE_DAL_VIVO}
              onScrivi={scrivi}
              onNuova={() => setConversazione([])}
              onProssima={() => debrief.fasi.length > 0 && vaiAFase((attiva + 1) % debrief.fasi.length)}
              onDomanda={chiedi}
            />
          </div>
        </motion.div>
      )}

      <RapportoCompleto aperto={rapporto} onChiudi={() => setRapporto(false)} />
    </div>
  );
}
