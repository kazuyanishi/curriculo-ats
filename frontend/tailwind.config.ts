import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        brand: "#5b5bd6",
      },
      boxShadow: {
        soft: "0 12px 40px rgba(30, 41, 59, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
