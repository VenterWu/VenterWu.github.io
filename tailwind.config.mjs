import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./src/**/*.{astro,html,js,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'rgb(var(--color-canvas) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        ink: 'rgb(var(--color-ink) / <alpha-value>)',
        soft: 'rgb(var(--color-soft) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        highlight: 'rgb(var(--color-highlight) / <alpha-value>)',
        line: 'rgb(var(--color-line) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Newsreader', 'Literata', 'ui-serif', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      boxShadow: {
        hard: '0 10px 30px rgb(var(--color-shadow) / 0.08)',
        soft: '0 18px 60px rgb(var(--color-shadow) / 0.10)',
      },
    },
  },
  plugins: [typography],
};
