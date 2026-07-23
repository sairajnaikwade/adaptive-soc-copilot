/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SOC CoPilot brand palette
        soc: {
          bg:       '#0a0e1a',  // Deep navy background
          surface:  '#111827',  // Card/panel surface
          border:   '#1f2937',  // Subtle borders
          accent:   '#3b82f6',  // Primary blue accent
          success:  '#10b981',  // Green — safe/normal
          warning:  '#f59e0b',  // Amber — medium risk
          danger:   '#ef4444',  // Red — high risk
          muted:    '#6b7280',  // Muted text
          text:     '#f9fafb',  // Primary text
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          from: { boxShadow: '0 0 5px #3b82f6, 0 0 10px #3b82f6' },
          to:   { boxShadow: '0 0 10px #3b82f6, 0 0 20px #3b82f6, 0 0 40px #3b82f6' },
        },
      },
    },
  },
  plugins: [],
}
