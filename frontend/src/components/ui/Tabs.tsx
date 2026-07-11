"use client";

// Tab switcher generico (megaprompt #6, FASE 4): barra tab in stile strumentale
// (mono uppercase, underline accent sull'attiva — niente glow) + pannello contenuto.
// Il dettaglio si mostra su richiesta invece di impilare tutto (principio sezione 0).
import { useState } from "react";

export default function Tabs({
  tabs,
  initial,
}: {
  tabs: { id: string; label: string; content: React.ReactNode }[];
  initial?: string;
}) {
  const [active, setActive] = useState(initial ?? tabs[0]?.id);
  const current = tabs.find((t) => t.id === active) ?? tabs[0];

  return (
    <div>
      <div role="tablist" className="flex gap-1 border-b border-line">
        {tabs.map((t) => {
          const is = t.id === active;
          return (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={is}
              onClick={() => setActive(t.id)}
              className={`-mb-px border-b-2 px-4 py-2 font-mono text-[0.65rem] uppercase tracking-widest transition ${
                is
                  ? "border-accent text-white"
                  : "border-transparent text-subtle hover:text-white"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      <div role="tabpanel" className="pt-4">
        {current?.content}
      </div>
    </div>
  );
}
