/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12263A",
        sea: "#1B6B93",
        mist: "#E8F1F5",
        sand: "#F3EDE4",
        ember: "#C45C26",
      },
      fontFamily: {
        display: ["\"Fraunces\"", "Georgia", "serif"],
        body: ["\"Source Sans 3\"", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
