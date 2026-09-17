"use client";

// La sessione aperta, condivisa da tutte le schermate (L4 del rework dati).
//
// Prima ogni pagina chiamava `/api/session` e riceveva gli stessi numeri scritti a
// mano. Ora c'è un archivio di sessioni: il pilota ne sceglie una (selettore nella
// Sidebar), e Dashboard, Telemetria, Console e Setup leggono **lo stesso report** del
// motore di analisi. La corrispondenza fra schermate non si mantiene più a mano: è la
// stessa risposta del backend.
//
// Scelte:
// * di default si apre la sessione più recente; chi entra in modalità demo vede la DEMO;
// * la scelta si ricorda (localStorage `pw_sessione`), perché la sessione è una
//   preferenza di lavoro, non un dato personale;
// * i nomi di vetture e piste arrivano dal catalogo, una volta sola.
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  getAnalisi,
  getCatalog,
  getSessioni,
  type Catalog,
  type Report,
  type Riassunto,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { slugLeggibile, type NomiCatalogo } from "@/lib/formato";

const KEY = "pw_sessione";
// In modalità demo la scelta vale per la visita (sessionStorage): la postazione è
// condivisa e ogni ingresso riparte dalla DEMO, ma una ricarica non deve perdere la
// sessione aperta.
const KEY_DEMO = "pw_sessione_visita";

type Stato = {
  elenco: Riassunto[] | null;
  demoId: string | null;
  idSessione: string | null;
  sessione: Riassunto | null;
  report: Report | null;
  caricamento: boolean;
  errore: string | null;
  nomi: NomiCatalogo;
  catalogo: Catalog | null;
  apri: (id: string) => void;
  ricarica: (apriId?: string) => Promise<void>;
};

const Ctx = createContext<Stato | null>(null);

function leggiScelta(demo: boolean): string | null {
  try {
    return demo ? sessionStorage.getItem(KEY_DEMO) : localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function salvaScelta(id: string, demo: boolean) {
  try {
    if (demo) sessionStorage.setItem(KEY_DEMO, id);
    else localStorage.setItem(KEY, id);
  } catch {
    /* no-op: la scelta vive comunque in memoria */
  }
}

export function SessioneProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const demo = user?.kind === "demo";
  const [elenco, setElenco] = useState<Riassunto[] | null>(null);
  const [demoId, setDemoId] = useState<string | null>(null);
  const [idSessione, setIdSessione] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [caricamento, setCaricamento] = useState(true);
  const [errore, setErrore] = useState<string | null>(null);
  const [catalogo, setCatalogo] = useState<Catalog | null>(null);

  const ricarica = useCallback(
    async (apriId?: string) => {
      try {
        const r = await getSessioni();
        setElenco(r.sessioni);
        setDemoId(r.demo_id);
        setErrore(null);
        const esiste = (id: string | null) => !!id && r.sessioni.some((s) => s.id === id);
        const scelta = apriId ?? leggiScelta(demo);
        // In modalità demo si parte dalla DEMO: la postazione è condivisa e l'archivio
        // del PC non è la demo di nessuno.
        const predefinita = demo ? r.demo_id : (r.sessioni[0]?.id ?? r.demo_id);
        const id = esiste(scelta) ? (scelta as string) : predefinita;
        setIdSessione(id);
        if (id) salvaScelta(id, demo);
      } catch {
        setErrore("Backend non raggiungibile — avvia FastAPI su :8000 (vedi README).");
        setCaricamento(false);
      }
    },
    [demo],
  );

  useEffect(() => {
    ricarica();
  }, [ricarica]);

  useEffect(() => {
    getCatalog()
      .then(setCatalogo)
      .catch(() => setCatalogo(null));
  }, []);

  // Il report segue la sessione scelta.
  useEffect(() => {
    if (!idSessione) return;
    let vivo = true;
    setCaricamento(true);
    // Mai il report di una sessione sotto l'intestazione di un'altra.
    setReport(null);
    getAnalisi(idSessione)
      .then((r) => {
        if (!vivo) return;
        setReport(r);
        setErrore(null);
      })
      .catch(() => vivo && setErrore("Analisi della sessione non disponibile."))
      .finally(() => vivo && setCaricamento(false));
    return () => {
      vivo = false;
    };
  }, [idSessione]);

  const apri = useCallback(
    (id: string) => {
      setIdSessione(id);
      salvaScelta(id, demo);
    },
    [demo],
  );

  const nomi = useMemo<NomiCatalogo>(() => {
    const vetture = new Map((catalogo?.cars ?? []).map((c) => [c.id, c.display_name]));
    const piste = new Map((catalogo?.tracks ?? []).map((t) => [t.id, t.short_name || t.name]));
    return {
      vettura: (slug) => (slug ? vetture.get(slug) ?? slugLeggibile(slug) : "Vettura non indicata"),
      pista: (slug) => (slug ? piste.get(slug) ?? slugLeggibile(slug) : "Pista non indicata"),
    };
  }, [catalogo]);

  const sessione = elenco?.find((s) => s.id === idSessione) ?? null;

  return (
    <Ctx.Provider
      value={{ elenco, demoId, idSessione, sessione, report, caricamento, errore, nomi, catalogo, apri, ricarica }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useSessione(): Stato {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSessione va usato dentro <SessioneProvider>");
  return v;
}
