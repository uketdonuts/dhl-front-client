/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dhl-yellow': '#FFCC00',
        'dhl-red': '#D40511',
      },
    },
  },
  plugins: [],
} 