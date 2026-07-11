"use client";

// Sezione comprimibile della Sidebar (megaprompt #5, FASE 5): header cliccabile con
// titolo + chevron + eventuale badge (visibile anche da chiusa), corpo che si mostra/
// nasconde. Stato persistito in localStorage per sezione (sopravvive al refresh).
// Gestione densità visiva senza toccare i moduli di contenuto.
import { useEffect, useState } from "react";

export default function SidebarSection({
  id,
  title,
  badge,
  defaultOpen = true,
  children,
}: {
  id: string;
  title: string;
  badge?: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const storeKey = `pw_sb_${id}`;
  const [open, setOpen] = useState(defaultOpen);

  useEffect(() => {
    try {
      const v = localStorage.getItem(storeKey);
      if (v !== null) setOpen(v === "1");
    } catch {
      /* localStorage non disponibile: si resta sul default */
    }
  }, [storeKey]);

  function toggle() {
    setOpen((o) => {
      const n = !o;
      try {
        localStorage.setItem(storeKey, n ? "1" : "0");
      } catch {
        /* no-op */
      }
      return n;
    });
  }

  return (
    <div>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="group flex w-full items-center justify-between gap-2 py-0.5 text-left"
      >
        <span className="font-mono text-[0.55rem] uppercase tracking-widest text-muted transition group-hover:text-subtle">
          {title}
        </span>
        <span className="flex items-center gap-1.5">
          {badge}
          <svg
            width="9"
            height="9"
            viewBox="0 0 10 10"
            aria-hidden
            className={`text-muted transition-transform duration-200 ${open ? "" : "-rotate-90"}`}
          >
            <path d="M2 3.5 L5 6.5 L8 3.5" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      </button>
      {open && <div className="mt-1.5">{children}</div>}
    </div>
  );
}
