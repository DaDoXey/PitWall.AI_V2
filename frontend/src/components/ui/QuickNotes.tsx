"use client";

// Note rapide / promemoria personale (megaprompt #5, FASE 6): un blocco note della
// sessione persistito in localStorage (solo sul dispositivo, nessun backend). Sostituisce
// uno dei due shortcut-icona in fondo alla Sidebar.
import { useEffect, useState } from "react";

const KEY = "pw_quick_notes";

export default function QuickNotes() {
  const [text, setText] = useState("");

  useEffect(() => {
    try {
      const v = localStorage.getItem(KEY);
      if (v !== null) setText(v);
    } catch {
      /* localStorage non disponibile */
    }
  }, []);

  function onChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const v = e.target.value;
    setText(v);
    try {
      localStorage.setItem(KEY, v);
    } catch {
      /* no-op */
    }
  }

  return (
    <div className="rounded-lg border border-line bg-inset p-2">
      <textarea
        value={text}
        onChange={onChange}
        rows={3}
        placeholder="Promemoria di sessione…"
        className="w-full resize-none bg-transparent font-mono text-[0.62rem] leading-snug text-white placeholder:text-muted focus:outline-none"
      />
      <div className="mt-0.5 font-mono text-[0.5rem] text-muted">Salvato in locale sul dispositivo</div>
    </div>
  );
}
