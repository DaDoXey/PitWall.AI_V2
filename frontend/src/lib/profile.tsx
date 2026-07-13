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

export type DriverProfile = {
  level: "principiante" | "intermedio" | "esperto";
  goal: "divertimento" | "tempi" | "competere" | "endurance";
  weakAreas: WeakArea[]; // selezione multipla
  setupFamiliarity: "poco" | "abbastanza" | "molto";
  completedAt: string; // ISO — flag "onboarding fatto"
};

type ProfileCtx = {
  profile: DriverProfile | null;
  ready: boolean; // true dopo la lettura iniziale di localStorage (evita flash)
  // Wizard: aperto al primo accesso (nessun completedAt) o da "Rivedi tutorial".
  onboardingOpen: boolean;
  startOnboarding: () => void; // replay: riparte dallo step 1 (il profilo resta finché non salvi)
  closeOnboarding: () => void;
  saveProfile: (p: Omit<DriverProfile, "completedAt">) => void;
};

const Ctx = createContext<ProfileCtx | null>(null);
const KEY = "pw_driver_profile";

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

  useEffect(() => {
    setProfile(readStored());
    setReady(true);
  }, []);

  const saveProfile = (p: Omit<DriverProfile, "completedAt">) => {
    const full: DriverProfile = { ...p, completedAt: new Date().toISOString() };
    setProfile(full);
    try {
      localStorage.setItem(KEY, JSON.stringify(full));
    } catch {
      /* no-op: il profilo vive comunque in memoria per questa visita */
    }
  };

  return (
    <Ctx.Provider
      value={{
        profile,
        ready,
        onboardingOpen,
        startOnboarding: () => setOnboardingOpen(true),
        closeOnboarding: () => setOnboardingOpen(false),
        saveProfile,
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
