import type { Config } from "tailwindcss";

// Token "cockpit dark" portati dal design system della v1 (assets/design_system.css).
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a0a",
        surface: "#111111",
        raised: "#1a1a1a",
        inset: "#141414",
        accent: { DEFAULT: "#E8002D", hover: "#CC0028" },
        ok: "#00C853",
        warn: "#FFB300",
        line: { DEFAULT: "#222222", strong: "#333333" },
        subtle: "#999999",
        muted: "#666666",
      },
      fontFamily: {
        display: ["var(--font-orbitron)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
