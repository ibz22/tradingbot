/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B1929',
        card: '#1A2332',
        border: '#2A3441',
        primary: '#5B8DFF',
        success: '#10B981',
        error: '#EF4444',
        'text-primary': '#FFFFFF',
        'text-secondary': '#94A3B8',
        'hover': '#1E293B'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}