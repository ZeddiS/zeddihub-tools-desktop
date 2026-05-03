/**
 * Typed wrappers around Tauri system_* commands (PCSysInfoPanel + Utility/processes).
 */

import { invoke } from "@tauri-apps/api/core";

export interface DiskInfo {
  mount: string;
  kind: string;
  total_mb: number;
  free_mb: number;
  used_mb: number;
  usage_pct: number;
}

export interface SystemInfo {
  os: string;
  arch: string;
  cpu_name: string;
  cpu_cores: number;
  cpu_usage_pct: number;
  total_memory_mb: number;
  used_memory_mb: number;
  mem_usage_pct: number;
  hostname: string;
  uptime_secs: number;
  disks: DiskInfo[];
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu_pct: number;
  memory_mb: number;
}

export const systemApi = {
  info: () => invoke<SystemInfo>("system_info"),
  processList: () => invoke<ProcessInfo[]>("process_list"),
  processKill: (pid: number) => invoke<boolean>("process_kill", { pid }),
};
