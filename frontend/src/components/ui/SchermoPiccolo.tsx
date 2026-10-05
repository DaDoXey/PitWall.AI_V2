"use client";

// PitWall è fatto per lo schermo di un computer: telemetria, mappa e radio stanno fianco a
// fianco. Sotto i 900 px di larghezza le pagine si accavallano, quindi invece di una pagina
// rotta si dice come stanno le cose (pacchetto 1.2). Chi vuole guardare lo stesso può farlo:
// la scelta vale per la scheda del browser.
// Con il telefono in orizzontale si vede, anche se scomodo (provato da Edoardo il 05/10/2026
// su più telefoni): lì l'avviso sparisce da solo, e in verticale lo suggerisce.
import { useEffect, useState } from "react";

const CHIAVE = "pw_schermo_piccolo_ok";

export default function SchermoPiccolo() {
  const [chiuso, setChiuso] = useState(false);

  useEffect(() => {
    try {
      setChiuso(sessionStorage.getItem(CHIAVE) === "1");
    } catch {
      /* senza memoria del browser l'avviso resta: è il caso prudente */
    }
  }, []);

  if (chiuso) return null;
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Schermo troppo stretto"
      className="fixed inset-0 z-[60] flex flex-col items-center justify-center gap-5 bg-bg px-8 text-center min-[900px]:hidden [@media(orientation:landscape)_and_(min-width:640px)]:hidden"
    >
      <span className="font-display text-xl font-bold tracking-[0.14em]">
        PITWALL<span className="text-accent">.AI</span>
      </span>
      <p className="max-w-sm text-[1.05rem] font-medium leading-snug text-white">Aprilo da computer.</p>
      <p className="max-w-sm text-sm leading-relaxed text-subtle">
        Telemetria, mappa del circuito e radio di Gigi stanno una accanto all&apos;altra: su uno schermo stretto non ci
        stanno.
      </p>
      <p className="max-w-sm text-sm leading-relaxed text-subtle">
        In alternativa gira il telefono in orizzontale: si vede tutto, anche se un po&apos; scomodo.
      </p>
      <button
        type="button"
        onClick={() => {
          try {
            sessionStorage.setItem(CHIAVE, "1");
          } catch {
            /* vale solo per questa visita */
          }
          setChiuso(true);
        }}
        className="rounded-full border border-line-strong px-5 py-2 text-[0.82rem] text-subtle transition hover:border-accent hover:text-white"
      >
        Guarda lo stesso
      </button>
    </div>
  );
}
