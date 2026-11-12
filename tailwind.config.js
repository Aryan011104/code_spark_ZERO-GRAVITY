/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        agri: {
          50: '#f2fbf5',
          100: '#e1f7e8',
          200: '#c5eed2',
          300: '#98dfb0',
          400: '#63c788',
          500: '#3ba966',
          600: '#2b8950',
          700: '#246d41',
          800: '#1b4332',
          900: '#17442a',
          950: '#0b2616',
        },
        earth: {
          50: '#faf6f0',
          100: '#f4ece0',
          200: '#ebd7c0',
          300: '#debca0',
          400: '#cfa07e',
          500: '#b87d55',
          600: '#9d6342',
          700: '#7e4d36',
          800: '#5a3828',
          900: '#403d39',
        }
      }
    },
  },
  plugins: [],
}
