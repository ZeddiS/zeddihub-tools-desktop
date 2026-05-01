import { writable, derived, get } from "svelte/store";
import { browser } from "$app/environment";
import cs from "$i18n/cs";
import en from "$i18n/en";

export type Lang = "cs" | "en";
type Dict = typeof cs;
type Key = keyof Dict;

const STORAGE_KEY = "zh.lang";
const STRINGS: Record<Lang, Dict> = { cs, en };

function readInitial(): Lang {
  if (!browser) return "cs";
  const saved = localStorage.getItem(STORAGE_KEY);
  return saved === "en" ? "en" : "cs";
}

export const lang = writable<Lang>(readInitial());

lang.subscribe((value) => {
  if (!browser) return;
  localStorage.setItem(STORAGE_KEY, value);
  document.documentElement.lang = value;
});

/**
 * Reactive translator store. Use as `$t("nav_home")` in components.
 */
export const t = derived(lang, ($lang) => {
  return (key: Key | string, fallback?: string): string => {
    const dict = STRINGS[$lang] as Record<string, string>;
    return dict[key] ?? fallback ?? key;
  };
});

export function setLang(value: Lang) {
  lang.set(value);
}

export function toggleLang() {
  lang.update((cur) => (cur === "cs" ? "en" : "cs"));
}

export function getLang(): Lang {
  return get(lang);
}
