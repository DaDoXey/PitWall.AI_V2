// Identità di Gigi (Race Engineer) — megaprompt #2 FASE 6: cuffia da muretto box
// stilizzata, mono-linea bianca (archetto + 2 padiglioni), tratto pulito, nessun
// dettaglio extra. Componente condiviso — unica fonte dell'icona di Gigi.
// Leggibile in piccolo (badge 24–28px) e in grande (header Console 44px).
export default function GigiAvatar({ size = 44 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      stroke="#ffffff"
      strokeWidth={3}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {/* Archetto: semicerchio che congiunge i centri dei due padiglioni (x=11 e x=37) */}
      <path d="M11 25 A13 13 0 0 1 37 25" />
      {/* Padiglioni auricolari: simmetrici attorno al centro (24), stessi bordi */}
      <rect x="7" y="25" width="8" height="13" rx="4" />
      <rect x="33" y="25" width="8" height="13" rx="4" />
    </svg>
  );
}
