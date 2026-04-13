/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Instrument Sans"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        canvas: {
          DEFAULT: "hsl(222 28% 11%)",
          elevated: "hsl(222 24% 15%)",
          subtle: "hsl(222 20% 19%)",
        },
        accent: {
          DEFAULT: "hsl(210 95% 58%)",
          muted: "hsl(210 85% 48%)",
          glow: "hsl(200 100% 78%)",
        },
        ink: {
          DEFAULT: "hsl(210 30% 96%)",
          muted: "hsl(215 18% 72%)",
          faint: "hsl(215 14% 52%)",
        },
      },
      backgroundImage: {
        "mesh-gradient":
          "radial-gradient(ellipse 90% 55% at 50% -15%, rgba(59, 130, 246, 0.14), transparent), radial-gradient(ellipse 50% 45% at 100% 0%, rgba(124, 58, 237, 0.1), transparent)",
        "sidebar-shine":
          "linear-gradient(180deg, rgb(30 41 59) 0%, rgb(23 30 42) 100%)",
      },
      boxShadow: {
        card: "0 0 0 1px hsl(215 20% 28% / 0.55), 0 20px 50px -15px hsl(0 0% 0% / 0.55)",
        glow: "0 0 60px -15px hsl(210 95% 55% / 0.35)",
      },
    },
  },
  plugins: [],
};
