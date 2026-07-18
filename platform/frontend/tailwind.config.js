/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0a0a0e",
          900: "#131318",
          800: "#1b1b22",
          700: "#26262f",
        },
        accent: {
          400: "#c4b5fd",
          500: "#8b5cf6",
          600: "#7c3aed",
          900: "#4c1d95",
        },
        tier: {
          low: "#22c55e",
          medium: "#eab308",
          high: "#f97316",
          critical: "#ef4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgb(139 92 246 / 0.15), 0 8px 24px -8px rgb(139 92 246 / 0.35)",
      },
    },
  },
  plugins: [],
};
