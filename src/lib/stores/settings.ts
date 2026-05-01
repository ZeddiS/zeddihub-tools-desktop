/**
 * Reactive settings store. Loads from Rust on first access, write-through
 * persists to settings.json via Tauri command.
 *
 * UI components subscribe via `$settings` and call `settings.update(...)` to
 * mutate. Local stores `theme` and `locale` already manage their own
 * localStorage; this store is for everything else (close_behavior,
 * telemetry, auto_update, first_launch_done, sidebar_sections).
 */

import { writable, get } from "svelte/store";
import { settingsApi, type AppSettings } from "$api/settings";

const initial: AppSettings = {
  lang: "cs",
  appearance: "dark",
  close_behavior: "minimize",
  telemetry_enabled: true,
  auto_update_enabled: true,
  first_launch_done: false,
  sidebar_sections: {},
  data_dir_override: null,
};

function createSettingsStore() {
  const { subscribe, set, update } = writable<AppSettings>(initial);
  let loaded = false;

  return {
    subscribe,

    /** Lazy-load from disk on first call. Subsequent calls return cached. */
    async ensureLoaded(): Promise<AppSettings> {
      if (loaded) return get({ subscribe });
      try {
        const data = await settingsApi.load();
        set(data);
        loaded = true;
        return data;
      } catch (e) {
        console.warn("settings.load failed:", e);
        loaded = true;
        return get({ subscribe });
      }
    },

    /** Patch a subset of fields and persist. */
    async patch(patch: Partial<AppSettings>): Promise<void> {
      let next: AppSettings = { ...get({ subscribe }), ...patch };
      set(next);
      try {
        await settingsApi.save(next);
      } catch (e) {
        console.warn("settings.save failed:", e);
      }
    },

    async factoryReset(): Promise<number> {
      const removed = await settingsApi.factoryReset();
      set(initial);
      loaded = false;
      return removed;
    },
  };
}

export const settings = createSettingsStore();
