"use client";

// Onboarding "Conosci il pilota" (megaprompt #9). FASE 1: host + trigger primo
// accesso + guscio modal (placeholder — il wizard a 4 step arriva in FASE 2).
// Montato SOLO nel layout (app): su /login non esiste, quindi il wizard parte
// dopo il login, mai sopra la schermata d'accesso. Idioma modal di StintCompare
// (overlay, Esc, click-fuori) MA senza chiusura accidentale sul primo accesso:
// il wizard si chiude solo dai suoi bottoni ("Salta" / fine), non da Esc/overlay
// — a metà wizard un click fuori non deve buttare via le risposte.
import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useProfile } from "@/lib/profile";

export default function OnboardingFlow() {
  const { ready, profile, onboardingOpen, startOnboarding, closeOnboarding } = useProfile();

  // Trigger primo accesso: nessun profilo completato → wizard (anche in demo).
  useEffect(() => {
    if (ready && !profile) startOnboarding();
    // startOnboarding è stabile (setState); il trigger deve valutare solo ready/profile.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, profile]);

  return (
    <AnimatePresence>
      {onboardingOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          role="dialog"
          aria-modal="true"
          aria-label="Conosci il pilota"
        >
          <motion.div
            className="w-full max-w-lg rounded-2xl border border-line border-t-2 border-t-accent bg-surface p-6"
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
          >
            <div className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">
              Conosci il pilota
            </div>
            <h2 className="mt-1 font-display text-lg font-bold">Ciao, sono Gigi.</h2>
            <p className="mt-2 text-sm leading-relaxed text-subtle">
              Quattro domande veloci per capire come guidi: così ti consiglio le
              lezioni giuste e taro i miei consigli su di te.
            </p>
            {/* FASE 2: qui entra il wizard a 4 step (livello · obiettivo · punti deboli · setup) */}
            <div className="mt-4 rounded-xl border border-dashed border-line bg-inset p-4 font-mono text-xs text-muted">
              Wizard in costruzione (FASE 2)
            </div>
            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={closeOnboarding}
                className="rounded-md border border-line px-4 py-2 font-mono text-xs uppercase tracking-wider text-subtle transition hover:border-accent hover:text-white"
              >
                Salta per ora
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
