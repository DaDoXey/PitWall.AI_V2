"use client";

// La dettatura alla radio di Gigi (#075): il riconoscimento vocale del browser scrive nella
// casella, e basta. Non invia: il pilota legge, corregge e preme Invio, così una parola
// capita male non consuma una domanda a Gigi dal vivo.
// È la Web Speech API: c'è in Chrome e in Edge, non in Firefox (lì il microfono non compare).
// In Chrome l'audio viene riconosciuto dai server di Google, non da PitWall.
import { useCallback, useEffect, useRef, useState } from "react";

// Il minimo che serve della Web Speech API: TypeScript non la porta fra i suoi tipi.
type Risultato = { isFinal: boolean; 0: { transcript: string } };
type EventoRisultato = { results: ArrayLike<Risultato> };
type Riconoscimento = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: EventoRisultato) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type Costruttore = new () => Riconoscimento;

function costruttore(): Costruttore | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: Costruttore; webkitSpeechRecognition?: Costruttore };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

const AVVISI: Record<string, string> = {
  "not-allowed": "Microfono non autorizzato: controlla i permessi del browser",
  "service-not-allowed": "Microfono non autorizzato: controlla i permessi del browser",
  "audio-capture": "Nessun microfono trovato",
  network: "Riconoscimento vocale non raggiungibile: serve la rete",
};

/** Il testo dettato accodato a quello già scritto, con uno spazio solo in mezzo. */
export function accoda(prima: string, dettato: string, massimo: number): string {
  const pezzo = dettato.trim();
  if (!pezzo) return prima;
  const base = prima.trimEnd();
  return (base ? `${base} ${pezzo}` : pezzo).slice(0, massimo);
}

/**
 * `alterna()` accende e spegne l'ascolto; mentre si parla `onTesto` riceve la frase
 * (anche a metà, per vederla comparire). L'ascolto si chiude da solo al silenzio.
 */
export function useDettatura(onTesto: (dettato: string) => void) {
  const [disponibile, setDisponibile] = useState(false);
  const [inAscolto, setInAscolto] = useState(false);
  const [avviso, setAvviso] = useState<string | null>(null);
  const riconoscimento = useRef<Riconoscimento | null>(null);
  const consegna = useRef(onTesto);
  consegna.current = onTesto;

  // Dopo il primo disegno: sul server il browser non c'è, e il pulsante non deve lampeggiare.
  useEffect(() => setDisponibile(costruttore() !== null), []);
  useEffect(() => () => riconoscimento.current?.abort(), []);

  const ferma = useCallback(() => riconoscimento.current?.stop(), []);

  const alterna = useCallback(() => {
    if (riconoscimento.current) {
      riconoscimento.current.stop();
      return;
    }
    const Tipo = costruttore();
    if (!Tipo) return;
    const r = new Tipo();
    r.lang = "it-IT";
    r.continuous = false;
    r.interimResults = true;
    r.onresult = (e) => consegna.current(Array.from(e.results, (x) => x[0].transcript).join(" "));
    r.onerror = (e) => setAvviso(AVVISI[e.error] ?? null); // «no-speech» e «aborted» non sono guasti
    r.onend = () => {
      riconoscimento.current = null;
      setInAscolto(false);
    };
    riconoscimento.current = r;
    setAvviso(null);
    setInAscolto(true);
    try {
      r.start();
    } catch {
      riconoscimento.current = null;
      setInAscolto(false);
    }
  }, []);

  return { disponibile, inAscolto, avviso, alterna, ferma };
}
