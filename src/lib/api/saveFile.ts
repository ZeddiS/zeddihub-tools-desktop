/**
 * Helper: prompt user for save path via Tauri dialog plugin, write text via fs plugin.
 * Returns saved path on success, null on cancel/failure.
 *
 * Used by all generator panels (CS2/CSGO/Rust player tools, server tools, autoexec…).
 */

import { save } from "@tauri-apps/plugin-dialog";
import { writeTextFile, BaseDirectory } from "@tauri-apps/plugin-fs";

export interface SaveOptions {
  defaultName?: string;
  defaultExtension?: string;
  filters?: { name: string; extensions: string[] }[];
  title?: string;
}

export async function saveCfgFile(
  content: string,
  opts: SaveOptions = {},
): Promise<string | null> {
  const path = await save({
    defaultPath: opts.defaultName ?? "config.cfg",
    title: opts.title ?? "Uložit cfg soubor",
    filters: opts.filters ?? [
      { name: "Config", extensions: ["cfg"] },
      { name: "All",    extensions: ["*"] },
    ],
  });

  if (!path) return null;

  // Write at absolute path — no BaseDirectory.
  await writeTextFile(path, content);
  return path;
}
