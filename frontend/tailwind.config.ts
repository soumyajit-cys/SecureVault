/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eafff7",
          100: "#ccfbf0",
          200: "#9af0dc",
          300: "#5fe3c4",
          400: "#2fd4ab",
          500: "#10b981",
          600: "#0d9668",
          700: "#0b7a55",
          800: "#0b5c43",
          900: "#0a4a38",
          950: "#042f22"
        },
        accent: {
          DEFAULT: "#22d3ee",
          light: "#67e8f9",
          soft: "#164e63"
        },
        ink: {
          DEFAULT: "#e2e8f0",
          soft: "#94a3b8",
          faint: "#64748b"
        },
        surface: {
          DEFAULT: "#0b1120",
          soft: "#060a14",
          muted: "#101a2e",
          elevated: "#0f172a"
        },
        cyber: {
          DEFAULT: "#05070d",
          grid: "#14203a",
          line: "#1e2b45",
          glow: "#22d3ee"
        }
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif"
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace"
        ]
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #10b981 0%, #0d9488 50%, #0e7490 100%)",
        "brand-gradient-soft":
          "linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(34,211,238,0.08) 100%)",
        "brand-gradient-warm":
          "linear-gradient(135deg, #10b981 0%, #22d3ee 100%)",
        "cyber-grid":
          "linear-gradient(rgba(34,211,238,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.05) 1px, transparent 1px)",
        "cyber-grid-bright":
          "linear-gradient(rgba(34,211,238,0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.09) 1px, transparent 1px)",
        "glass-gradient":
          "linear-gradient(160deg, rgba(148,163,184,0.10) 0%, rgba(15,23,42,0.55) 100%)",
        "radial-glow":
          "radial-gradient(ellipse at top, rgba(34,211,238,0.12) 0%, transparent 60%)"
      },
      boxShadow: {
        card: "0 1px 0 0 rgb(255 255 255 / 0.04) inset, 0 1px 2px 0 rgb(0 0 0 / 0.5)",
        "card-hover":
          "0 0 0 1px rgb(34 211 238 / 0.22), 0 16px 40px -12px rgb(13 148 136 / 0.35), 0 1px 0 0 rgb(255 255 255 / 0.05) inset",
        modal:
          "0 0 0 1px rgb(255 255 255 / 0.08), 0 24px 64px -16px rgb(0 0 0 / 0.8), 0 0 64px -24px rgb(34 211 238 / 0.25)",
        glow: "0 0 0 1px rgb(16 185 129 / 0.35), 0 0 24px -4px rgb(16 185 129 / 0.45), 0 8px 32px -8px rgb(13 148 136 / 0.5)",
        "glow-sm":
          "0 0 0 1px rgb(16 185 129 / 0.25), 0 0 16px -4px rgb(16 185 129 / 0.35)",
        "glow-cyan":
          "0 0 0 1px rgb(34 211 238 / 0.3), 0 0 24px -4px rgb(34 211 238 / 0.4)",
        inset: "inset 0 1px 0 0 rgb(255 255 255 / 0.06)"
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" }
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" }
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" }
        },
        "scan-line": {
          "0%": { top: "0%", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { top: "100%", opacity: "0" }
        },
        "grid-drift": {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 48px" }
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.8)", opacity: "0.6" },
          "100%": { transform: "scale(1.6)", opacity: "0" }
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" }
        }
      },
      animation: {
        "fade-in": "fade-in 0.35s ease-out both",
        "fade-up": "fade-up 0.45s cubic-bezier(0.22, 1, 0.36, 1) both",
        "scale-in": "scale-in 0.25s cubic-bezier(0.22, 1, 0.36, 1) both",
        "slide-in-right":
          "slide-in-right 0.3s cubic-bezier(0.22, 1, 0.36, 1) both",
        shimmer: "shimmer 2s linear infinite",
        "float-slow": "float 5s ease-in-out infinite",
        "scan-line": "scan-line 4s linear infinite",
        "grid-drift": "grid-drift 8s linear infinite",
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.22, 1, 0.36, 1) infinite",
        blink: "blink 1.1s step-end infinite"
      },
      transitionTimingFunction: {
        "in-out-soft": "cubic-bezier(0.22, 1, 0.36, 1)"
      }
    }
  },
  plugins: []
};
