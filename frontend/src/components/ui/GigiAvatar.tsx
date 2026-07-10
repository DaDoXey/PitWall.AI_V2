// Identità di Gigi (Race Engineer): casco GT3 con visiera accent + headset/mic
// da muretto box. SVG inline, leggibile sia in grande (header Console) sia in
// piccolo (badge sidebar). Componente condiviso — unica fonte dell'icona di Gigi.
export default function GigiAvatar({ size = 44 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="23" fill="#1a1a1a" stroke="#333333" />
      {/* Headset: earcup sinistro + archetto + mic boom fino al labbro */}
      <rect x="7" y="22" width="4.5" height="9" rx="2.25" fill="#141414" stroke="#333333" />
      <path d="M11 32c-2.5 1-3.5 3.5-3 6" stroke="#333333" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      <circle cx="16" cy="38.5" r="1.8" fill="#E8002D" />
      {/* Earcup destro */}
      <rect x="36.5" y="22" width="4.5" height="9" rx="2.25" fill="#141414" stroke="#333333" />
      {/* Calotta casco: guscio scuro + fascia superiore accent */}
      <path d="M12 28a12 12 0 0 1 24 0v4a2 2 0 0 1-2 2H14a2 2 0 0 1-2-2v-4Z" fill="#0e0e0e" stroke="#333333" />
      <path d="M24 15a12 12 0 0 1 11.4 8.4H12.6A12 12 0 0 1 24 15Z" fill="#E8002D" />
      {/* Visiera scura + fessura luminosa accent */}
      <path d="M13 25h22v3.5a2.5 2.5 0 0 1-2.5 2.5h-17A2.5 2.5 0 0 1 13 28.5V25Z" fill="#0a0a0a" stroke="#333333" />
      <rect x="15.5" y="26.2" width="17" height="2.4" rx="1.2" fill="#E8002D" opacity="0.9" />
    </svg>
  );
}
