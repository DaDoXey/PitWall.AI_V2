"use client";

// L'onda della radio (#060): le barre sono sempre le stesse per lo stesso messaggio
// (barreOnda), e si muovono solo quando il messaggio è «in onda».
import { useMemo } from "react";
import { barreOnda } from "@/lib/debrief";

export default function Onda({
  seme,
  barre = 24,
  altezza = 16,
  colore,
  viva = false,
}: {
  seme: string;
  barre?: number;
  altezza?: number;
  colore: string;
  viva?: boolean;
}) {
  const valori = useMemo(() => barreOnda(seme, barre), [seme, barre]);
  const larghezza = barre * 5 - 2;
  return (
    <svg
      className={viva ? "pw-onda-viva" : undefined}
      width={larghezza}
      height={altezza}
      viewBox={`0 0 ${larghezza} ${altezza}`}
      aria-hidden="true"
    >
      <g fill={colore}>
        {valori.map((v, i) => {
          const h = Math.max(2, Math.round(altezza * v));
          return (
            <rect
              key={i}
              x={i * 5}
              y={(altezza - h) / 2}
              width={3}
              height={h}
              rx={1}
              style={viva ? { animationDelay: `-${((i * 137) % 800) / 1000}s` } : undefined}
            />
          );
        })}
      </g>
    </svg>
  );
}
