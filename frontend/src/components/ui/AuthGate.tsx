"use client";

// Gate client-side del gruppo (app) (megaprompt #6, FASE 9): senza accesso
// (Google o demo) si torna a /login — il login è SEMPRE la prima schermata di
// una nuova visita (richiesta di Edoardo; lo stato vive in sessionStorage e
// muore con la tab). NON è un confine di sicurezza server: è UX dimostrativa,
// per scelta di progetto (megaprompt #6 §1).
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) router.replace("/login");
  }, [ready, user, router]);

  // Prima della lettura di sessionStorage (o senza utente) niente UI protetta:
  // evita il flash della dashboard prima del redirect.
  if (!ready || !user) return null;
  return <>{children}</>;
}
