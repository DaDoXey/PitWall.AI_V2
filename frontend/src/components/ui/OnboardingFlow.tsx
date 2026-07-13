"use client";

// Onboarding "Conosci il pilota" (megaprompt #9). FASE 1: host + trigger primo
// accesso. FASE 2: wizard a 4 step a tap (livello · obiettivo · punti deboli ·
// setup) con progress e avanti/indietro; al termine salva il profilo
// (completedAt = adesso). FASE 3: schermata finale con riepilogo + lezioni
// consigliate (recommendLessons) + CTA tour/salta. Montato SOLO nel layout
// (app): su /login non esiste. Il modal NON si chiude con Esc/click-fuori
// (a differenza di StintCompare): a metà wizard un click accidentale non deve
// buttare via le risposte — si esce solo dai bottoni.
import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import {
  useProfile,
  type DriverProfile,
  type WeakArea,
} from "@/lib/profile";
import { recommendLessons } from "@/lib/lessons";

// ---- Opzioni dei 4 step (label UI → valore del profilo) ---------------------

const LEVELS: { value: DriverProfile["level"]; label: string }[] = [
  { value: "principiante", label: "Principiante" },
  { value: "intermedio", label: "Intermedio" },
  { value: "esperto", label: "Esperto" },
];

const GOALS: { value: DriverProfile["goal"]; label: string }[] = [
  { value: "divertimento", label: "Divertirmi" },
  { value: "tempi", label: "Migliorare i tempi" },
  { value: "competere", label: "Competere online" },
  { value: "endurance", label: "Endurance & gestione" },
];

const WEAK_AREAS: { value: WeakArea; label: string }[] = [
  { value: "frenata", label: "Frenata" },
  { value: "trail-braking", label: "Trail braking" },
  { value: "trazione", label: "Trazione" },
  { value: "costanza", label: "Costanza" },
  { value: "gomme", label: "Gomme" },
  { value: "carburante", label: "Carburante" },
  { value: "linea", label: "Linea" },
];

const SETUP_LEVELS: { value: DriverProfile["setupFamiliarity"]; label: string }[] = [
  { value: "poco", label: "Poco" },
  { value: "abbastanza", label: "Abbastanza" },
  { value: "molto", label: "Molto" },
];

const STEP_TITLES = [
  "Che pilota sei?",
  "Cosa cerchi in pista?",
  "Dove senti di perdere di più?",
  "Quanto mastichi i setup?",
];

// Label UI di un valore del profilo (riepilogo FASE 3).
function labelOf<T extends string>(options: { value: T; label: string }[], value: T): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

// Chip a tap: selezionata = bordo+testo accesi (colore = stato, niente glow).
function Chip({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`rounded-md border px-4 py-2.5 text-left text-sm transition ${
        selected
          ? "border-accent bg-raised text-white"
          : "border-line bg-inset text-subtle hover:border-accent/50 hover:text-white"
      }`}
    >
      {label}
    </button>
  );
}

export default function OnboardingFlow() {
  const { ready, profile, onboardingOpen, startOnboarding, closeOnboarding, saveProfile } =
    useProfile();

  // Trigger primo accesso: nessun profilo completato → wizard (anche in demo).
  useEffect(() => {
    if (ready && !profile) startOnboarding();
    // startOnboarding è stabile (setState); il trigger deve valutare solo ready/profile.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, profile]);

  // Bozza risposte: prefill dal profilo esistente nel replay ("Rivedi tutorial").
  const [step, setStep] = useState(0);
  const [level, setLevel] = useState<DriverProfile["level"] | null>(null);
  const [goal, setGoal] = useState<DriverProfile["goal"] | null>(null);
  const [weakAreas, setWeakAreas] = useState<WeakArea[]>([]);
  const [setupFam, setSetupFam] = useState<DriverProfile["setupFamiliarity"] | null>(null);

  // A ogni apertura il wizard riparte dallo step 1 con la bozza allineata al
  // profilo salvato (vuota al primo accesso).
  useEffect(() => {
    if (!onboardingOpen) return;
    setStep(0);
    setLevel(profile?.level ?? null);
    setGoal(profile?.goal ?? null);
    setWeakAreas(profile?.weakAreas ?? []);
    setSetupFam(profile?.setupFamiliarity ?? null);
    // Snapshot del profilo alla sola apertura: la bozza poi vive locale.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onboardingOpen]);

  const toggleWeak = (w: WeakArea) =>
    setWeakAreas((prev) => (prev.includes(w) ? prev.filter((x) => x !== w) : [...prev, w]));

  // Avanti abilitato: step 1/2/4 vogliono una scelta; i punti deboli possono
  // restare vuoti (la FASE 3 ha un default di lezioni consigliate).
  const canProceed =
    step === 0 ? level !== null : step === 1 ? goal !== null : step === 2 ? true : setupFam !== null;

  const finish = () => {
    if (!level || !goal || !setupFam) return; // guardia: non dovrebbe accadere (bottone disabilitato)
    saveProfile({ level, goal, weakAreas, setupFamiliarity: setupFam });
    setStep(4); // schermata finale (FASE 3): riepilogo + lezioni consigliate
  };

  const startTour = () => {
    // FASE 6: qui parte il tour pagina per pagina. Per ora chiude soltanto.
    closeOnboarding();
  };

  const summary = step === 4;
  const recommended = summary ? recommendLessons(weakAreas) : [];

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
            <div className="flex items-baseline justify-between">
              <div className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">
                Conosci il pilota
              </div>
              <div className="font-mono text-[0.62rem] uppercase tracking-widest text-muted">
                {summary ? "Il tuo profilo" : `Passo ${step + 1} di 4`}
              </div>
            </div>

            {/* Progress: barra sottile, riempimento accent proporzionale allo step */}
            <div className="mt-2 h-0.5 w-full rounded-full bg-inset">
              <motion.div
                className="h-full rounded-full bg-accent"
                animate={{ width: summary ? "100%" : `${((step + 1) / 4) * 100}%` }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              />
            </div>

            {!summary && (
              <>
                <h2 className="mt-4 font-display text-lg font-bold">{STEP_TITLES[step]}</h2>
                {step === 2 && (
                  <p className="mt-1 text-xs text-muted">
                    Puoi sceglierne più d&apos;una (o nessuna).
                  </p>
                )}

                <div className={`mt-4 grid gap-2 ${step === 2 ? "grid-cols-2" : "grid-cols-1"}`}>
                  {step === 0 &&
                    LEVELS.map((o) => (
                      <Chip key={o.value} label={o.label} selected={level === o.value} onClick={() => setLevel(o.value)} />
                    ))}
                  {step === 1 &&
                    GOALS.map((o) => (
                      <Chip key={o.value} label={o.label} selected={goal === o.value} onClick={() => setGoal(o.value)} />
                    ))}
                  {step === 2 &&
                    WEAK_AREAS.map((o) => (
                      <Chip key={o.value} label={o.label} selected={weakAreas.includes(o.value)} onClick={() => toggleWeak(o.value)} />
                    ))}
                  {step === 3 &&
                    SETUP_LEVELS.map((o) => (
                      <Chip key={o.value} label={o.label} selected={setupFam === o.value} onClick={() => setSetupFam(o.value)} />
                    ))}
                </div>

                <div className="mt-6 flex items-center justify-between">
                  {/* "Salta per ora" solo sul primo step; dopo, "Indietro". */}
                  {step === 0 ? (
                    <button
                      type="button"
                      onClick={closeOnboarding}
                      className="rounded-md px-3 py-2 font-mono text-xs uppercase tracking-wider text-muted transition hover:text-white"
                    >
                      Salta per ora
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setStep((s) => s - 1)}
                      className="rounded-md px-3 py-2 font-mono text-xs uppercase tracking-wider text-muted transition hover:text-white"
                    >
                      ← Indietro
                    </button>
                  )}

                  {step < 3 ? (
                    <button
                      type="button"
                      disabled={!canProceed}
                      onClick={() => setStep((s) => s + 1)}
                      className="rounded-md border border-accent px-4 py-2 font-mono text-xs uppercase tracking-wider text-white transition hover:border-accent-hover hover:bg-raised disabled:cursor-not-allowed disabled:border-line disabled:text-muted"
                    >
                      Avanti →
                    </button>
                  ) : (
                    <button
                      type="button"
                      disabled={!canProceed}
                      onClick={finish}
                      className="rounded-md border border-accent px-4 py-2 font-mono text-xs uppercase tracking-wider text-white transition hover:border-accent-hover hover:bg-raised disabled:cursor-not-allowed disabled:border-line disabled:text-muted"
                    >
                      Fine
                    </button>
                  )}
                </div>
              </>
            )}

            {summary && level && goal && setupFam && (
              <>
                <h2 className="mt-4 font-display text-lg font-bold">Ecco come guidi.</h2>

                {/* Riepilogo: le 4 risposte, idioma etichetta mono + valore */}
                <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 rounded-xl border border-line bg-inset p-4">
                  {[
                    ["Livello", labelOf(LEVELS, level)],
                    ["Obiettivo", labelOf(GOALS, goal)],
                    [
                      "Punti deboli",
                      weakAreas.length > 0
                        ? weakAreas.map((w) => labelOf(WEAK_AREAS, w)).join(" · ")
                        : "Nessuno indicato",
                    ],
                    ["Setup", labelOf(SETUP_LEVELS, setupFam)],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <div className="font-mono text-[0.55rem] uppercase tracking-widest text-muted">{k}</div>
                      <div className="mt-0.5 text-sm text-white">{v}</div>
                    </div>
                  ))}
                </div>

                {/* Lezioni consigliate dai punti deboli (default: linea + frenata) */}
                <div className="mt-4 font-mono text-[0.62rem] uppercase tracking-widest text-muted">
                  Lezioni che ti consiglio
                </div>
                <div className="mt-2 flex flex-col gap-2">
                  {recommended.map((l) => (
                    <Link
                      key={l.slug}
                      href={`/lezioni/${l.slug}`}
                      onClick={closeOnboarding}
                      className="group rounded-lg border border-line bg-inset p-3 transition hover:border-accent/50"
                    >
                      <div className="flex items-baseline gap-2">
                        <span className="font-mono text-xs text-muted">
                          {String(l.number).padStart(2, "0")}
                        </span>
                        <span className="text-sm font-semibold transition-colors group-hover:text-accent">
                          {l.title}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-1 text-xs text-subtle">{l.summary}</p>
                    </Link>
                  ))}
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <button
                    type="button"
                    onClick={closeOnboarding}
                    className="rounded-md px-3 py-2 font-mono text-xs uppercase tracking-wider text-muted transition hover:text-white"
                  >
                    Salta
                  </button>
                  <button
                    type="button"
                    onClick={startTour}
                    className="rounded-md border border-accent px-4 py-2 font-mono text-xs uppercase tracking-wider text-white transition hover:border-accent-hover hover:bg-raised"
                  >
                    Fai il tour →
                  </button>
                </div>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
