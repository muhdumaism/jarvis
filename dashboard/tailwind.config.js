/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Neomorphic custom palette
        bg: {
          light: '#f5f2eb', // Warm Neo-brutalist cream paper
          dark: '#0a0a0c'   // Solid high-contrast deep dark grey
        }
      },
      boxShadow: {
        // Raised (outset) shadows
        'neo-raised-light': '9px 9px 16px #a3b1c6, -9px -9px 16px #ffffff',
        'neo-raised-dark': '9px 9px 16px #12161f, -9px -9px 16px #283041',
        
        // Inset shadows
        'neo-inset-light': 'inset 9px 9px 16px #a3b1c6, inset -9px -9px 16px #ffffff',
        'neo-inset-dark': 'inset 9px 9px 16px #12161f, inset -9px -9px 16px #283041',
        
        // Small raised shadows
        'neo-sm-light': '4px 4px 8px #a3b1c6, -4px -4px 8px #ffffff',
        'neo-sm-dark': '4px 4px 8px #12161f, -4px -4px 8px #283041',

        // Small inset shadows
        'neo-sm-inset-light': 'inset 4px 4px 8px #a3b1c6, inset -4px -4px 8px #ffffff',
        'neo-sm-inset-dark': 'inset 4px 4px 8px #12161f, inset -4px -4px 8px #283041'
      }
    },
  },
  plugins: [],
}
