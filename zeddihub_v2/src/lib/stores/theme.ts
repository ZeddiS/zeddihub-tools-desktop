import { writable, get } from "svelte/store";
import { browser } from "$app/environment";

export type Theme = "dark" | "light";

const STORAGE_KEY = "zh.theme";

function readInitial(): Theme {
  if (!browser) return "dark";
  const saved = localStorage.getItem(STORAGE_KEY);
  return saved === "light" ? "light" : "dark";
}

export const theme = writable<Theme>(readInitial());

theme.subscribe((value) => {
  if (!browser) return;
  localStorage.setItem(STORAGE_KEY, value);
  // Toggle Tailwind's `dark` class strategy on <html>.
  const html = document.documentElement;
  html.classList.toggle("dark", value === "dark");
  html.classList.toggle("light", value === "light");
});

export function toggleTheme() {
  theme.update((cur) => (cur === "dark" ? "light" : "dark"));
}

export function getTheme(): Theme {
  return get(theme);
}
