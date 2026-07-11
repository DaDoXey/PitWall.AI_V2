"use client";

// Stato di accesso client-side (megaprompt #6, FASE 9). DELIBERATAMENTE leggero:
// NESSUNA sessione server, nessun token inviato al backend. Il profilo Google
// (nome/email/foto) vive SOLO in sessionStorage — sparisce alla chiusura della
// tab, così il login è sempre la prima schermata di una nuova visita (richiesta
// di Edoardo) e nessun dato personale resta persistito (GDPR: niente logging,
// niente storage oltre la sessione del browser).
import { createContext, useContext, useEffect, useState } from "react";

export type PwUser =
  | { kind: "google"; name: string; email: string; picture: string }
  | { kind: "demo"; name: string };

type AuthCtx = {
  user: PwUser | null;
  ready: boolean; // true dopo la lettura iniziale di sessionStorage (evita flash)
  signInWithGoogle: (credential: string) => void;
  enterDemo: () => void;
  signOut: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);
const KEY = "pw_user";

// Decodifica il payload del JWT credential di Google (base64url → JSON, UTF-8
// corretto per nomi accentati). Solo lettura client-side: niente verifica firma
// perché il token NON autorizza nulla lato server (login dimostrativo).
function decodeJwtPayload(token: string): Record<string, unknown> {
  const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<PwUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(KEY);
      if (raw) setUser(JSON.parse(raw) as PwUser);
    } catch {
      /* sessionStorage non disponibile: si resta sloggati */
    }
    setReady(true);
  }, []);

  const persist = (u: PwUser | null) => {
    setUser(u);
    try {
      if (u) sessionStorage.setItem(KEY, JSON.stringify(u));
      else sessionStorage.removeItem(KEY);
    } catch {
      /* no-op */
    }
  };

  const signInWithGoogle = (credential: string) => {
    const p = decodeJwtPayload(credential);
    persist({
      kind: "google",
      name: String(p.name ?? "Pilota"),
      email: String(p.email ?? ""),
      picture: String(p.picture ?? ""),
    });
  };

  const enterDemo = () => persist({ kind: "demo", name: "Pilota demo" });
  const signOut = () => persist(null);

  return (
    <Ctx.Provider value={{ user, ready, signInWithGoogle, enterDemo, signOut }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth(): AuthCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth va usato dentro <AuthProvider>");
  return v;
}
