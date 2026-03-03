import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B1020",
        signal: "#1AA3FF",
        neon: "#00D084",
        pulse: "#FF6B00"
      }
    }
  },
  plugins: []
};

export default config;
