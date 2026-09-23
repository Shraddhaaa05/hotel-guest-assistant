import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17221F",
        teal: {
          DEFAULT: "#123C39",
          light: "#1B504B",
          dark: "#0C2826",
        },
        ivory: "#FBF9F5",
        brass: {
          DEFAULT: "#C69749",
          light: "#DDB876",
          dark: "#A47A34",
        },
        rust: "#A9503B",
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      keyframes: {
        "rise-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "rise-in": "rise-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
