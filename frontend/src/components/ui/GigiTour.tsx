"use client";

// Tour schermate (megaprompt #9, FASE 6): dopo il wizard (o da "Rivedi
// tutorial" → wizard → "Fai il tour"), Gigi porta il pilota pagina per pagina
// con un fumetto. ROBUSTEZZA: callout in posizione FISSA basso-centro, mai
// ancorato a elementi della pagina → non si rompe se una pagina cambia.
// La navigazione è centralizzata nell'effect: quando lo step cambia si fa
// router.push della rotta dello step — "Avanti" incrementa e basta.
// Lo stato (tourStep) vive in ProfileProvider: sopravvive alla navigazione.
// L4 (16/09/2026): testi riscritti sulle schermate nuove, più il passo Sessioni.
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import GigiAvatar from "@/components/ui/GigiAvatar";
import { useProfile } from "@/lib/profile";

const TOUR_STEPS = [
  {
    href: "/",
    label: "Dashboard",
    text: "Qui hai il verdetto della sessione aperta: dove perdi tempo, in ordine di gravità, ognuna con la prova e cosa fare. Accanto, cosa regge davvero.",
  },
  {
    href: "/sessioni",
    label: "Sessioni",
    text: "Qui porti dentro le tue sessioni: su PC dai file e dalla telemetria di ACC, su console con il setup e il racconto di come è andata. La sessione aperta la scegli dalla barra a sinistra.",
  },
  {
    href: "/console",
    label: "Engineer Console",
    text: "Qui mi chiedi della sessione in parole tue — tipo «l'auto scivola dietro». Ti rispondo con diagnosi, causa, correzione del setup e correzione di guida, citando solo numeri misurati.",
  },
  {
    href: "/telemetry",
    label: "Telemetria",
    text: "Qui il dettaglio: giri e settori, le curve una per una con due giri sovrapposti, e gomme e freni contro la finestra ufficiale di Kunos.",
  },
  {
    href: "/setup",
    label: "Setup",
    text: "Qui regoli i parametri dell'auto. Quelli che il verdetto chiede di toccare te li evidenzio, con la variazione.",
  },
  {
    href: "/lezioni",
    label: "Lezioni",
    text: "E qui ti insegno i fondamentali — dalla frenata al lift & coast. Parti da quelli che ti ho consigliato.",
  },
];

export default function GigiTour() {
  const { tourStep, setTourStep } = useProfile();
  const router = useRouter();
  const path = usePathname();

  const step = tourStep !== null ? TOUR_STEPS[tourStep] : null;
  const last = tourStep === TOUR_STEPS.length - 1;

  // Navigazione centralizzata: lo step attivo porta sulla sua pagina.
  useEffect(() => {
    if (step && path !== step.href) router.push(step.href);
    // path deliberatamente fuori dalle dipendenze: naviga SOLO al cambio di
    // step — se il pilota gira altrove a metà tour, non lo strattoniamo.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tourStep]);

  return (
    <AnimatePresence>
      {step && (
        <motion.div
          key={tourStep}
          className="fixed bottom-6 left-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 24 }}
          transition={{ type: "spring", stiffness: 380, damping: 32 }}
          role="dialog"
          aria-label={`Tour: ${step.label}`}
        >
          <div className="rounded-2xl border border-line border-l-[3px] border-l-accent bg-surface p-4 shadow-2xl">
            <div className="flex items-start gap-3">
              <GigiAvatar size={36} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-display text-sm font-bold tracking-wide">Gigi</span>
                  <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">
                    Tour · {(tourStep ?? 0) + 1}/{TOUR_STEPS.length} — {step.label}
                  </span>
                </div>
                <p className="mt-1 text-sm leading-relaxed text-subtle">{step.text}</p>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setTourStep(null)}
                className="rounded-md px-2 py-1.5 font-mono text-xs uppercase tracking-wider text-muted transition hover:text-white"
              >
                Salta
              </button>
              <button
                type="button"
                onClick={() => setTourStep(last ? null : (tourStep ?? 0) + 1)}
                className="rounded-md border border-accent px-4 py-1.5 font-mono text-xs uppercase tracking-wider text-white transition hover:border-accent-hover hover:bg-raised"
              >
                {last ? "Fine" : "Avanti →"}
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
