"use client";

// Login (megaprompt #6, FASE 8 restyling + FASE 9 Google Sign-In reale).
// Sign-In con popup Google vero (@react-oauth/google): al successo il profilo
// (nome/email/foto) vive SOLO client-side in sessionStorage (vedi lib/auth.tsx)
// — nessuna sessione server, nessun logging di dati personali (GDPR).
// Il form email/password finto è stato rimosso: con un Sign-In reale accanto,
// un form presentazionale che non autentica stonava (decisione F9, reversibile).
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { GoogleLogin } from "@react-oauth/google";
import { fadeInUp, staggerContainer } from "@/lib/motion";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { user, ready, signInWithGoogle, enterDemo } = useAuth();

  // Già dentro (Google o demo, stessa tab)? Niente doppio login: si va all'app.
  useEffect(() => {
    if (ready && user) router.replace("/");
  }, [ready, user, router]);

  function handleDemo() {
    enterDemo();
    router.push("/");
  }

  return (
    <div className="w-full max-w-sm">
      {/* Card: entra con lift + micro-scale; i blocchi interni a cascata (stagger).
          Centering a schermo pieno demandato al layout (auth) — niente Sidebar
          (fix INC-V2-004). Filetto accent in testa, stesso linguaggio del PageHeader. */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="w-full rounded-2xl border border-line border-t-2 border-t-accent bg-surface p-8"
        style={{ transformOrigin: "center" }}
      >
        {/* Brand */}
        <motion.div variants={fadeInUp} className="mb-7 text-center">
          <div className="font-display text-2xl font-bold tracking-wide">
            PITWALL<span className="text-accent">.AI</span>
          </div>
          <div className="mt-1 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted">
            Virtual Race Engineer · ACC GT3
          </div>
        </motion.div>

        {/* Google Sign-In reale (popup). Tema scuro per coerenza col design system. */}
        <motion.div variants={fadeInUp} className="flex justify-center">
          <GoogleLogin
            onSuccess={(res) => {
              if (res.credential) {
                signInWithGoogle(res.credential);
                router.push("/");
              }
            }}
            theme="filled_black"
            size="large"
            text="continue_with"
            shape="rectangular"
          />
        </motion.div>

        {/* Divider */}
        <motion.div variants={fadeInUp} className="my-5 flex items-center gap-3 font-mono text-[0.6rem] uppercase tracking-widest text-muted">
          <span className="h-px flex-1 bg-line" />
          oppure
          <span className="h-px flex-1 bg-line" />
        </motion.div>

        {/* Quick-login demo (percorso d'esame: nessuna rete/account richiesti) */}
        <motion.button
          variants={fadeInUp}
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleDemo}
          className="w-full rounded-md border border-line-strong bg-raised px-4 py-2.5 text-sm text-white transition hover:border-accent"
        >
          🏁 Entra in modalità demo
        </motion.button>

        {/* Nota privacy: il profilo Google resta nel browser, sessione di tab */}
        <motion.p variants={fadeInUp} className="mt-4 text-center font-mono text-[0.55rem] leading-relaxed text-muted">
          Il profilo Google (nome, email, foto) resta solo in questo browser
          <br />
          e viene eliminato alla chiusura della scheda. Nessun invio a server.
        </motion.p>

        <motion.p variants={fadeInUp} className="mt-5 text-center text-[0.7rem] text-muted">
          Progetto d&apos;esame · © 2026 Edoardo Ferlito · Licenza MIT
        </motion.p>
      </motion.div>
    </div>
  );
}
