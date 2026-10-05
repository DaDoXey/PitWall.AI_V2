"use client";

// Chi è collegato (megaprompt #6, FASE 9): foto/nome/email reali dopo il Google Sign-In,
// o "Pilota demo" in modalità demo. Nessun placeholder "N": creato da zero (F0: quello
// nelle immagini era l'indicatore dev di Next.js).
//
// Riordino della colonna (Entry #048): è un'icona in testa alla colonna, accanto al
// marchio, e il menu contiene tutto quello che non serve a ogni giro — chi sei, rifare
// il tutorial, i crediti delle immagini, la versione, uscire. Prima era un riquadro in
// fondo alla colonna, e occupava lo spazio che ora va alla mappa della pista.
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "@/lib/auth";
import { useProfile } from "@/lib/profile";

const VERSIONE = "v0.9.0 · © 2026 Edoardo Ferlito · MIT";

export default function UserChip() {
  const { user, signOut } = useAuth();
  const { startOnboarding } = useProfile();
  const router = useRouter();
  const [aperto, setAperto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!aperto) return;
    const fuori = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAperto(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setAperto(false);
    document.addEventListener("mousedown", fuori);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", fuori);
      document.removeEventListener("keydown", esc);
    };
  }, [aperto]);

  if (!user) return null;

  const logout = () => {
    signOut();
    router.replace("/login");
  };

  const voce =
    "flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left font-mono text-[0.62rem] text-subtle transition hover:bg-surface hover:text-white";

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setAperto((a) => !a)}
        aria-expanded={aperto}
        aria-haspopup="menu"
        aria-label={`${user.name}: menu`}
        title={user.name}
        className={`flex h-8 w-8 items-center justify-center overflow-hidden rounded-full border transition ${
          aperto ? "border-accent" : "border-line hover:border-line-strong"
        }`}
      >
        {user.kind === "google" && user.picture ? (
          // Foto profilo Google: <img> semplice (dominio esterno lh3.googleusercontent.com,
          // niente next/image per non toccare la config); no-referrer per igiene privacy.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.picture} alt="" referrerPolicy="no-referrer" className="h-full w-full object-cover" />
        ) : (
          <span className="text-sm" aria-hidden>
            🏁
          </span>
        )}
      </button>

      <AnimatePresence>
        {aperto && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.12 }}
            role="menu"
            className="absolute right-0 top-full z-40 mt-2 w-52 rounded-lg border border-line bg-raised p-1 shadow-xl"
          >
            <div className="border-b border-line px-2.5 pb-2 pt-1.5">
              <div className="truncate text-xs text-white">{user.name}</div>
              <div className="truncate font-mono text-[0.55rem] text-muted">
                {user.kind === "google" ? user.email : "modalità demo"}
              </div>
            </div>
            {/* Replay onboarding (megaprompt #9): rilancia wizard "Conosci il pilota" → tour. */}
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setAperto(false);
                startOnboarding();
              }}
              className={`${voce} mt-1`}
            >
              ↻ Rifai il tutorial
            </button>
            {/* Attribuzione asset: le licenze CC BY/BY-SA la vogliono raggiungibile
                dall'utente, non solo nel repo. */}
            <Link href="/crediti" role="menuitem" onClick={() => setAperto(false)} className={voce}>
              © Crediti immagini
            </Link>
            <button type="button" role="menuitem" onClick={logout} className={voce}>
              ⏻ Esci
            </button>
            <div className="mt-1 border-t border-line px-2.5 pb-1 pt-2 font-mono text-[0.52rem] text-muted">{VERSIONE}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
