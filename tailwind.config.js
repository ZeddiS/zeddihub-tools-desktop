/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  darkMode: "class", // toggled by adding/removing 'dark' class on <html>
  theme: {
    extend: {
      colors: {
        // Dark theme tokens — same as PoC, slightly more refined
        zh: {
          bg:           "rgb(var(--zh-bg) / <alpha-value>)",
          "sidebar-bg": "rgb(var(--zh-sidebar-bg) / <alpha-value>)",
          "header-bg":  "rgb(var(--zh-header-bg) / <alpha-value>)",
          "content-bg": "rgb(var(--zh-content-bg) / <alpha-value>)",
          "card-bg":    "rgb(var(--zh-card-bg) / <alpha-value>)",
          "card-hover": "rgb(var(--zh-card-hover) / <alpha-value>)",
          border:       "rgb(var(--zh-border) / <alpha-value>)",
          primary:      "rgb(var(--zh-primary) / <alpha-value>)",
          "primary-hover": "rgb(var(--zh-primary-hover) / <alpha-value>)",
          text:         "rgb(var(--zh-text) / <alpha-value>)",
          "text-muted": "rgb(var(--zh-text-muted) / <alpha-value>)",
          accent:       "rgb(var(--zh-accent) / <alpha-value>)",
          success:      "rgb(var(--zh-success) / <alpha-value>)",
          warning:      "rgb(var(--zh-warning) / <alpha-value>)",
          error:        "rgb(var(--zh-error) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ["Segoe UI", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        card: "12px",
        button: "8px",
        entry: "6px",
      },
    },
  },
  plugins: [],
};
