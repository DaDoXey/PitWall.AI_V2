"use client";

// Profilo pilota "Conosci il pilota" (megaprompt #9, FASE 1). Persistenza SOLO
// frontend in localStorage (nessun backend): il profilo sopravvive alle sessioni
// del browser — a differenza del login (sessionStorage), le risposte al wizard
// non vanno rifatte a ogni visita. Nessun dato personale: solo preferenze di
// guida (livello, obiettivo, punti deboli, confidenza setup).
import { createContext, useContext, useEffect, useState } from "react";

export type WeakArea =
  | "frenata"
  | "trail-braking"
  | "trazione"
  | "costanza"
  | "gomme"
  | "carburante"
  | "linea";

export type Platform = "pc" | "playstation" | "xbox";

export type DriverProfile = {
  // Dove gioca (L4, 16/09/2026): decide da dove arrivano i dati. PC = file e telemetria
  // di ACC; console = setup e racconto del pilota. Opzionale per i profili salvati
  // prima: la pagina Sessioni la chiede se manca.
  platform?: Platform;
  level: "principiante" | "intermedio" | "esperto";
  goal: "divertimento" | "tempi" | "competere" | "endurance";
  weakAreas: WeakArea[]; // selezione multipla
  setupFamiliarity: "poco" | "abbastanza" | "molto";
  completedAt: string; // ISO — flag "onboarding fatto"
};

type ProfileCtx = {
  profile: DriverProfile | null;
  ready: boolean; // true dopo la lettura iniziale di localStorage (evita flash)
  // Wizard: aperto al primo accesso (nessun completedAt e non "saltato") o da
  // "Rivedi tutorial".
  onboardingOpen: boolean;
  // true se l'utente ha già scelto "Salta per ora" in questa installazione:
  // sopprime l'apertura automatica del wizard (ma non "Rivedi tutorial").
  onboardingSkipped: boolean;
  startOnboarding: () => void; // replay: riparte dallo step 1 (il profilo resta finché non salvi)
  closeOnboarding: () => void;
  // "Salta per ora": chiude il wizard E persiste un flag così l'apertura
  // automatica al primo accesso non si ripresenta a ogni navigazione (fix UX).
  // Il flag `pw_onboarding_skipped` è ripulito dall'ingresso demo (tester fresco)
  // e da resetProfile ("Riparti da zero").
  dismissOnboarding: () => void;
  saveProfile: (p: Omit<DriverProfile, "completedAt">) => void;
  // Solo la piattaforma, senza rifare il wizard (pagina Sessioni).
  setPlatform: (p: Platform) => void;
  // La piattaforma nota: dal profilo o, se il wizard non è stato fatto, dalla bozza.
  platform: Platform | null;
  // Azzera profilo salvato + stato in memoria (e tour). Usato dall'ingresso in
  // modalità demo (postazione condivisa: ogni tester riparte da zero) e da
  // "Riparti da zero" nel wizard. Il provider è globale e sopravvive alla
  // navigazione login→app: pulire solo localStorage non basterebbe.
  resetProfile: () => void;
  // Tour schermate (FASE 6): indice step attivo o null. Vive QUI e non nel
  // componente perché deve sopravvivere alla navigazione tra le pagine.
  tourStep: number | null;
  startTour: () => void;
  setTourStep: (s: number | null) => void;
};

const Ctx = createContext<ProfileCtx | null>(null);
const KEY = "pw_driver_profile";
const SKIP_KEY = "pw_onboarding_skipped";
const DRAFT_KEY = "pw_driver_platform_draft";

function readStoredDraft(): Partial<DriverProfile> | null {
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    return raw ? (JSON.parse(raw) as Partial<DriverProfile>) : null;
  } catch {
    return null;
  }
}

function readStored(): DriverProfile | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const p = JSON.parse(raw) as DriverProfile;
    // Sanity minima: senza flag il profilo non vale come "onboarding fatto".
    return p && typeof p.completedAt === "string" ? p : null;
  } catch {
    return null; // localStorage non disponibile o JSON corrotto: come primo accesso
  }
}

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [ready, setReady] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [onboardingSkipped, setOnboardingSkipped] = useState(false);
  const [tourStep, setTourStep] = useState<number | null>(null);
  // Piattaforma scelta fuori dal wizard (pagina Sessioni) quando un profilo non c'è.
  const [draftPlatform, setDraftPlatform] = useState<Platform | null>(null);

  useEffect(() => {
    setProfile(readStored());
    setDraftPlatform(readStoredDraft()?.platform ?? null);
    try {
      setOnboardingSkipped(localStorage.getItem(SKIP_KEY) === "1");
    } catch {
      /* no-op: localStorage non disponibile → wizard mostrato (comportamento primo accesso) */
    }
    setReady(true);
  }, []);

  const dismissOnboarding = () => {
    setOnboardingOpen(false);
    setOnboardingSkipped(true);
    try {
      localStorage.setItem(SKIP_KEY, "1");
    } catch {
      /* no-op */
    }
  };

  const saveProfile = (p: Omit<DriverProfile, "completedAt">) => {
    const full: DriverProfile = { ...p, completedAt: new Date().toISOString() };
    setProfile(full);
    try {
      localStorage.setItem(KEY, JSON.stringify(full));
    } catch {
      /* no-op: il profilo vive comunque in memoria per questa visita */
    }
  };

  const setPlatform = (platform: Platform) => {
    // Senza un profilo completo si salva una bozza minima: il wizard, se rifatto, la
    // completerà. `completedAt` resta vuoto, quindi non vale come onboarding fatto.
    const base = profile ?? readStoredDraft();
    const next = { ...(base ?? {}), platform } as DriverProfile;
    if (profile) setProfile(next);
    try {
      localStorage.setItem(profile ? KEY : DRAFT_KEY, JSON.stringify(next));
    } catch {
      /* no-op */
    }
    setDraftPlatform(platform);
  };

  const resetProfile = () => {
    setProfile(null);
    setOnboardingSkipped(false); // "Riparti da zero"/demo: il wizard torna a mostrarsi
    setTourStep(null); // un tour a metà del tester precedente non deve riprendere
    setDraftPlatform(null);
    try {
      localStorage.removeItem(KEY);
      localStorage.removeItem(SKIP_KEY);
      localStorage.removeItem(DRAFT_KEY);
    } catch {
      /* no-op */
    }
  };

  return (
    <Ctx.Provider
      value={{
        profile,
        ready,
        onboardingOpen,
        onboardingSkipped,
        startOnboarding: () => setOnboardingOpen(true),
        closeOnboarding: () => setOnboardingOpen(false),
        dismissOnboarding,
        saveProfile,
        setPlatform,
        platform: profile?.platform ?? draftPlatform,
        resetProfile,
        tourStep,
        startTour: () => setTourStep(0),
        setTourStep,
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useProfile(): ProfileCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useProfile va usato dentro <ProfileProvider>");
  return v;
}

// Riga "Profilo pilota: …" per il contesto di Gigi (megaprompt #9, FASE 5).
// Frasi in italiano piano: la legge un LLM, non una UI.
const GOAL_PHRASE: Record<DriverProfile["goal"], string> = {
  divertimento: "divertirmi",
  tempi: "migliorare i tempi",
  competere: "competere online",
  endurance: "endurance e gestione",
};

const PLATFORM_PHRASE: Record<Platform, string> = {
  pc: "PC",
  playstation: "PlayStation",
  xbox: "Xbox",
};

export function profileContextLine(p: DriverProfile): string {
  const weak =
    p.weakAreas.length > 0
      ? p.weakAreas.map((w) => w.replace("-", " ")).join(", ").replace(/, ([^,]*)$/, " e $1")
      : "nessuno indicato";
  const platform = p.platform ? `gioca su ${PLATFORM_PHRASE[p.platform]}, ` : "";
  return (
    `Profilo pilota: ${platform}livello ${p.level}, obiettivo ${GOAL_PHRASE[p.goal]}, ` +
    `punti deboli ${weak}, setup: ${p.setupFamiliarity}.`
  );
}
