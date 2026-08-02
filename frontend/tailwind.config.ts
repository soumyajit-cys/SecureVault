/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
          950: "#1e1b4b"
        },
        accent: {
          DEFAULT: "#6366f1",
          light: "#818cf8",
          soft: "#eef2ff"
        },
        ink: {
          DEFAULT: "#0f172a",
          soft: "#475569",
          faint: "#94a3b8"
        },
        surface: {
          DEFAULT: "#ffffff",
          soft: "#f8fafc",
          muted: "#eef1f7"
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
          "linear-gradient(135deg, #6366f1 0%, #4338ca 60%, #312e81 100%)",
        "brand-gradient-soft":
          "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)",
        "brand-gradient-warm":
          "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
        "radial-glow":
          "radial-gradient(ellipse at top, #e0e7ff 0%, transparent 60%)"
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)",
        "card-hover":
          "0 8px 24px -6px rgb(79 70 229 / 0.14), 0 4px 8px -2px rgb(15 23 42 / 0.06)",
        modal: "0 20px 40px -12px rgb(15 23 42 / 0.25)",
        glow: "0 0 0 1px rgb(99 102 241 / 0.16), 0 8px 32px -8px rgb(79 70 229 / 0.35)",
        "glow-sm":
          "0 0 0 1px rgb(99 102 241 / 0.12), 0 4px 16px -4px rgb(79 70 229 / 0.3)",
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
        }
      },
      animation: {
        "fade-in": "fade-in 0.35s ease-out both",
        "fade-up": "fade-up 0.45s cubic-bezier(0.22, 1, 0.36, 1) both",
        "scale-in": "scale-in 0.25s cubic-bezier(0.22, 1, 0.36, 1) both",
        "slide-in-right":
          "slide-in-right 0.3s cubic-bezier(0.22, 1, 0.36, 1) both",
        shimmer: "shimmer 2s linear infinite",
        "float-slow": "float 4s ease-in-out infinite"
      },
      transitionTimingFunction: {
        "in-out-soft": "cubic-bezier(0.22, 1, 0.36, 1)"
      }
    }
  },
  plugins: []
};