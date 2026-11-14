/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#05080F",
        deep: "#0A1020",
        surface: "#0F1729",
        raised: "#152036",
        line: "rgba(148, 163, 184, 0.12)",
        fg: "#E6EDF7",
        muted: "#8A9AB5",
        cyan: { DEFAULT: "#22D3EE", soft: "#67E8F9" },
        violet: { DEFAULT: "#8B5CF6", soft: "#A78BFA" },
        ok: "#34D399",
        warn: "#FBBF24",
        risk: "#F87171",
      },
      fontFamily: {
        display: ["\"Space Grotesk\"", "Inter", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ["\"JetBrains Mono\"", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(34,211,238,.25), 0 8px 40px -8px rgba(34,211,238,.35)",
      },
      keyframes: {
        shimmer: { "100%": { transform: "translateX(100%)" } },
        "grid-pan": { "0%": { backgroundPosition: "0 0" }, "100%": { backgroundPosition: "48px 48px" } },
        pulseRing: {
          "0%": { transform: "scale(.8)", opacity: ".8" },
          "100%": { transform: "scale(2.4)", opacity: "0" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s infinite",
        "grid-pan": "grid-pan 6s linear infinite",
        "pulse-ring": "pulseRing 2s cubic-bezier(.2,.6,.4,1) infinite",
      },
    },
  },
  plugins: [],
};
