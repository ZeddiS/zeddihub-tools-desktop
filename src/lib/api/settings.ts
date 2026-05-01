/**
 * Typed wrappers around Tauri settings_* commands.
 */

import { invoke } from "@tauri-apps/api/core";

export interface AppSettings {
  lang: string;
  appearance: string;
  close_behavior: "minimize" | "quit";
  telemetry_enabled: boolean;
  auto_update_enabled: boolean;
  first_launch_done: boolean;
  sidebar_sections: Record<string, boolean>;
  data_dir_override?: string | null;
}

export const settingsApi = {
  load:                   () => invoke<AppSettings>("settings_load"),
  save:    (s: AppSettings) => invoke<void>("settings_save", { settings: s }),
  dataDir:                () => invoke<string>("settings_data_dir"),
  factoryReset:           () => invoke<number>("settings_factory_reset"),
  markFirstLaunchDone:    () => invoke<void>("settings_mark_first_launch_done"),
};
