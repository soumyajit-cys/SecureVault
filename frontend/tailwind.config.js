/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        vault: {
          950: "#060b16",
          900: "#0a1122",
          850: "#0d1526",
          800: "#111c33",
          700: "#16233f",
          600: "#1d2f55",
          500: "#28406f",
          400: "#3b5b94",
          300: "#5b86c4",
          200: "#8fb3e0",
          100: "#c6d9f2",
          50: "#e8f0fb"
        },
        neon: {
          cyan: "#22d3ee",
          green: "#4ade80",
          purple: "#a78bfa",
          red: "#f87171",
          amber: "#fbbf24"
        }
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      boxShadow: {
        glow: "0 0 24px rgba(34, 211, 238, 0.25)",
        "glow-green": "0 0 24px rgba(74, 222, 128, 0.2)"
      }
    }
  },
  plugins: []
};