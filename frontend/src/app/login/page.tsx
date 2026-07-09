"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");

  // Demo: nessuna auth reale lato server ancora (arriverà con NextAuth/OAuth).
  // Il quick-login entra direttamente nella dashboard.
  function enterDemo(e?: React.FormEvent) {
    e?.preventDefault();
    router.push("/");
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl border border-line bg-surface p-8">
        {/* Brand */}
        <div className="mb-6 text-center">
          <div className="font-display text-2xl font-bold tracking-wide">
            PITWALL<span className="text-accent">.AI</span>
          </div>
          <div className="mt-1 font-mono text-[0.6rem] uppercase tracking-[0.22em] text-muted">
            Virtual Race Engineer · ACC GT3
          </div>
        </div>

        {/* Form demo (presentazionale) */}
        <form onSubmit={enterDemo} className="flex flex-col gap-3">
          <label className="flex flex-col gap-1">
            <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="pilota@pitwall.ai"
              className="rounded-md border border-line bg-inset px-3 py-2 text-sm text-white placeholder:text-muted focus:border-accent focus:outline-none"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="font-mono text-[0.6rem] uppercase tracking-widest text-muted">Password</span>
            <input
              type="password"
              placeholder="••••••••"
              className="rounded-md border border-line bg-inset px-3 py-2 text-sm text-white placeholder:text-muted focus:border-accent focus:outline-none"
            />
          </label>

          <button
            type="submit"
            className="mt-2 rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-hover"
          >
            Entra
          </button>
        </form>

        {/* Divider */}
        <div className="my-5 flex items-center gap-3 font-mono text-[0.6rem] uppercase tracking-widest text-muted">
          <span className="h-px flex-1 bg-line" />
          oppure
          <span className="h-px flex-1 bg-line" />
        </div>

        {/* Quick-login demo + OAuth placeholder */}
        <button
          onClick={() => enterDemo()}
          className="w-full rounded-md border border-line-strong bg-raised px-4 py-2.5 text-sm text-white transition hover:border-accent"
        >
          🏁 Entra in modalità demo
        </button>
        <button
          disabled
          title="Prossimamente"
          className="mt-2 w-full cursor-not-allowed rounded-md border border-line bg-inset px-4 py-2.5 text-sm text-muted opacity-70"
        >
          Continua con Google — 🔒 prossimamente
        </button>

        <p className="mt-5 text-center text-[0.7rem] text-muted">
          Progetto d&apos;esame · Edoardo Ferlito
        </p>
      </div>
    </div>
  );
}
