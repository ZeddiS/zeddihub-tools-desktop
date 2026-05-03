/**
 * Typed wrappers around Tauri a2s_* command (Steam A2S_INFO over UDP).
 *
 * Backend: src-tauri/src/services/a2s.rs (UDP probe + TCP fallback).
 */

import { invoke } from "@tauri-apps/api/core";

export interface ServerInfo {
  online: boolean;
  ping_ms: number;
  name: string | null;
  map: string | null;
  players: number | null;
  max_players: number | null;
}

export const a2sApi = {
  query: (host: string, port: number, timeoutMs: number = 3000) =>
    invoke<ServerInfo>("a2s_query", { host, port, timeoutMs }),
};
