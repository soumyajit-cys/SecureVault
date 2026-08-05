/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554"
        },
        accent: {
          DEFAULT: "#2563eb",
          light: "#3b82f6",
          soft: "#dbeafe"
        },
        ink: {
          DEFAULT: "#0f172a",
          soft: "#475569",
          faint: "#94a3b8"
        },
        surface: {
          DEFAULT: "#ffffff",
          soft: "#f8fafc",
          muted: "#f1f5f9",
          elevated: "#ffffff"
        },
        cyber: {
          DEFAULT: "#0f172a",
          grid: "#e2e8f0",
          line: "#e2e8f0",
          glow: "#2563eb"
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
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace"
        ]
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(180deg, #3b82f6 0%, #2563eb 100%)",
        "brand-gradient-soft":
          "linear-gradient(180deg, rgba(59,130,246,0.08) 0%, rgba(37,99,235,0.05) 100%)",
        "brand-gradient-warm":
          "linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)",
        "cyber-grid":
          "linear-gradient(rgba(148,163,184,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.08) 1px, transparent 1px)",
        "cyber-grid-bright":
          "linear-gradient(rgba(148,163,184,0.14) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.14) 1px, transparent 1px)",
        "glass-gradient":
          "linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%)",
        "radial-glow":
          "radial-gradient(ellipse at top, rgba(37,99,235,0.06) 0%, transparent 60%)"
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.05)",
        "card-hover":
          "0 1px 2px 0 rgb(15 23 42 / 0.05), 0 8px 24px -12px rgb(15 23 42 / 0.12)",
        modal:
          "0 24px 64px -16px rgb(15 23 42 / 0.25)",
        glow: "0 0 0 1px rgb(37 99 235 / 0.12), 0 4px 12px -2px rgb(37 99 235 / 0.2)",
        "glow-sm":
          "0 0 0 1px rgb(37 99 235 / 0.1), 0 2px 6px -2px rgb(37 99 235 / 0.15)",
        "glow-cyan":
          "0 0 0 1px rgb(37 99 235 / 0.14), 0 4px 12px -2px rgb(37 99 235 / 0.22)",
        inset: "inset 0 1px 0 0 rgb(255 255 255 / 0.6)"
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.97)" },
          "100%": { opacity: "1", transform: "scale(1)" }
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(12px)" },
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
          "50%": { transform: "translateY(-6px)" }
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
        "fade-in": "fade-in 0.3s ease-out both",
        "fade-up": "fade-up 0.4s cubic-bezier(0.22, 1, 0.36, 1) both",
        "scale-in": "scale-in 0.2s cubic-bezier(0.22, 1, 0.36, 1) both",
        "slide-in-right":
          "slide-in-right 0.25s cubic-bezier(0.22, 1, 0.36, 1) both",
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
