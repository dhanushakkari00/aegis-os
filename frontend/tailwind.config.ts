import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#07111b",
        panel: "rgba(12, 23, 35, 0.68)",
        line: "rgba(135, 167, 189, 0.18)",
        cyan: "#4ee8ff",
        ember: "#ff8961",
        signal: "#f4c75b",
        surge: "#6cf2b4",
        critical: "#ff6b6b",
        elevated: "#ffaf4d",
        moderate: "#f3d565",
        calm: "#6cf2b4"
      },
      fontFamily: {
        display: ["var(--font-space-grotesk)"],
        body: ["var(--font-ibm-plex-sans)"],
        mono: ["var(--font-ibm-plex-mono)"]
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(78, 232, 255, 0.16), 0 24px 80px rgba(7, 17, 27, 0.48)",
        urgent: "0 0 0 1px rgba(255, 107, 107, 0.3), 0 20px 60px rgba(255, 107, 107, 0.16)"
      },
      backgroundImage: {
        "command-grid":
          "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;

