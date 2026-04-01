/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        'default-border': 'var(--color-border)',
        input: 'var(--color-input)',
        ring: 'var(--color-ring)' /* blue-700 */,
        background: 'var(--color-background)' /* gray-50 */,
        foreground: 'var(--color-foreground)' /* gray-800 */,
        primary: {
          DEFAULT: 'var(--color-primary)' /* blue-700 */,
          foreground: 'var(--color-primary-foreground)' /* white */,
        },
        secondary: {
          DEFAULT: 'var(--color-secondary)' /* green-700 */,
          foreground: 'var(--color-secondary-foreground)' /* white */,
        },
        destructive: {
          DEFAULT: 'var(--color-destructive)' /* red-600 */,
          foreground: 'var(--color-destructive-foreground)' /* white */,
        },
        muted: {
          DEFAULT: 'var(--color-muted)' /* gray-100 */,
          foreground: 'var(--color-muted-foreground)' /* gray-500 */,
        },
        accent: {
          DEFAULT: 'var(--color-accent)' /* amber-600 */,
          foreground: 'var(--color-accent-foreground)' /* white */,
        },
        popover: {
          DEFAULT: 'var(--color-popover)' /* white */,
          foreground: 'var(--color-popover-foreground)' /* gray-700 */,
        },
        card: {
          DEFAULT: 'var(--color-card)' /* white */,
          foreground: 'var(--color-card-foreground)' /* gray-700 */,
        },
        success: {
          DEFAULT: 'var(--color-success)' /* emerald-600 */,
          foreground: 'var(--color-success-foreground)' /* white */,
        },
        warning: {
          DEFAULT: 'var(--color-warning)' /* amber-600 */,
          foreground: 'var(--color-warning-foreground)' /* white */,
        },
        error: {
          DEFAULT: 'var(--color-error)' /* red-600 */,
          foreground: 'var(--color-error-foreground)' /* white */,
        },
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      fontFamily: {
        heading: ['Outfit', 'sans-serif'],
        body: ['Source Sans 3', 'sans-serif'],
        caption: ['Inter', 'sans-serif'],
        data: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        18: '4.5rem',
        80: '20rem',
        96: '24rem',
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        smooth: '250ms',
      },
      keyframes: {
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
      animation: {
        'pulse-subtle': 'pulse-subtle 2s cubic-bezier(0.4, 0, 0.2, 1) infinite',
      },
    },
  },
  plugins: [],
};
