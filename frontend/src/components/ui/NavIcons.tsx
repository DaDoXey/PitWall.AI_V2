// Icone nav line-style (megaprompt #7, FASE 4): stessa famiglia dell'headset di
// Gigi (GigiAvatar) — mono-linea, stroke sottile, cap/join arrotondati, nessun
// riempimento pieno. `currentColor`: il colore lo decide il contesto (accent
// sull'attiva, subtle/white altrove). Sostituiscono le emoji miste della nav.
type IconProps = { size?: number };

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

// Dashboard: griglia di card (le KPI della pagina)
export function IconDashboard({ size = 17 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <rect x="4" y="4" width="7" height="7" rx="1.5" />
      <rect x="13" y="4" width="7" height="7" rx="1.5" />
      <rect x="4" y="13" width="7" height="7" rx="1.5" />
      <rect x="13" y="13" width="7" height="7" rx="1.5" />
    </svg>
  );
}

// Engineer Console: eco dell'headset di GigiAvatar sulla griglia 24
export function IconConsole({ size = 17 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M5.5 13 A6.5 6.5 0 0 1 18.5 13" />
      <rect x="4" y="13" width="4" height="6.5" rx="2" />
      <rect x="16" y="13" width="4" height="6.5" rx="2" />
    </svg>
  );
}

// Telemetria: traccia canale su assi (line chart minimale)
export function IconTelemetry({ size = 17 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M4 4 V20 H20" />
      <path d="M7 15 L11 10 L14 13 L19 6" />
    </svg>
  );
}

// Lezioni: lampadina (i fondamentali che "accendono" il pilota)
export function IconLessons({ size = 17 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M9.5 18 v-1.8 C7.6 15 6.5 13.1 6.5 11 a5.5 5.5 0 0 1 11 0 c0 2.1-1.1 4-3 5.2 V18" />
      <path d="M9.5 18 H14.5" />
      <path d="M10.5 21 H13.5" />
    </svg>
  );
}

// Setup: slider verticali (i parametri ACC della pagina)
export function IconSetup({ size = 17 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base}>
      <path d="M7 4 V20" />
      <path d="M5 9 H9" />
      <path d="M12 4 V20" />
      <path d="M10 15 H14" />
      <path d="M17 4 V20" />
      <path d="M15 7 H19" />
    </svg>
  );
}
