/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          light: '#e1e0ff',
          DEFAULT: '#c0c1ff', // Primary
          container: '#8083ff',
          dark: '#494bd6',
          50: '#f0f9ff',
          100: '#e1e0ff',
          400: '#c0c1ff',
          500: '#6366f1', // Overridden primary color from metadata
          600: '#494bd6',
          700: '#2f2ebe',
          900: '#0d0096',
        },
        surface: {
          lowest: '#060e20',
          low: '#131b2e',
          DEFAULT: '#0b1326', // Surface Level 0
          container: '#171f33',
          high: '#222a3d',
          highest: '#2d3449',
          bright: '#31394d',
          900: '#0b1326',
          800: '#131b2e',
          700: '#171f33',
          600: '#222a3d',
          500: '#2d3449',
          400: '#31394d',
        },
        tertiary: {
          DEFAULT: '#ffb783',
          container: '#d97721',
        },
        accent: {
          purple: '#8b5cf6',
          cyan: '#06b6d4',
          green: '#10b981',
          amber: '#f59e0b',
          red: '#ffb4ab', // From Stitch error color
        }
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem', // Matches Stitch roundedness advice
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(20px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        glow: { '0%': { boxShadow: '0 0 5px #0ea5e9' }, '100%': { boxShadow: '0 0 20px #0ea5e9, 0 0 40px #0ea5e9' } },
      },
      backdropBlur: { xs: '2px' },
    },
  },
  plugins: [],
}
