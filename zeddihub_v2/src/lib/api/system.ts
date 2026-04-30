/**
 * Typed wrappers around Tauri system_* commands (PCSysInfoPanel etc.).
 */

import { invoke } from "@tauri-apps/api/core";

export interface SystemInfo {
  os: string;
  arch: string;
  cpuName: string;
  cpuCores: number;
  totalMemoryMb: number;
  hostname: string;
}

export const systemApi = {
  info: () => invoke<SystemInfo>("system_info"),
};
