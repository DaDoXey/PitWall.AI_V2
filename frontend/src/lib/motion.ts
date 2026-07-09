// Vocabolario motion condiviso della v2 (fondamenta): variants + preset di
// transizione, un unico punto di tuning. Riusato da Dashboard e — nel prompt
// successivo — da Console/Telemetria/Setup.
//
// Reduced-motion: il layout avvolge l'app in <MotionConfig reducedMotion="user">
// (framer riduce da solo i transform/layout); per i casi non-transform (CountUp,
// pulse) si usa useReducedMotion() nel componente, che degrada a stato finale.
import type { Transition, Variants } from "framer-motion";

// Curva e durate condivise. EASE ~ easeOutExpo: entra deciso, si posa morbido.
export const EASE = [0.22, 1, 0.36, 1] as const;
export const DUR = { fast: 0.2, base: 0.4, slow: 0.9 } as const;

// Ingresso elemento: sale e sfuma in dentro.
export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: DUR.base, ease: EASE } },
};

// Orchestratore: i figli (con variants fadeInUp) entrano a cascata.
export const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

// Preset per whileHover delle card: lift sobrio + transizione morbida.
export const cardHover = { y: -4, transition: { duration: DUR.fast, ease: EASE } };

// Transizione base riutilizzabile (per animate()/whileHover puntuali).
export const baseTransition: Transition = { duration: DUR.base, ease: EASE };

// Comodità: un solo import per il reduced-motion nei componenti.
export { useReducedMotion } from "framer-motion";
