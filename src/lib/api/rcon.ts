/**
 * Typed wrappers around Tauri rcon_* commands.
 *
 * Backend: src-tauri/src/services/rcon.rs (Source RCON over TCP).
 * State (HashMap<key, Connection>) lives in Rust until disconnect or app exit.
 */

import { invoke } from "@tauri-apps/api/core";

export const rconApi = {
  /** Connect + authenticate. Returns session key (host:port) used by send/disconnect. */
  connect: (host: string, port: number, password: string) =>
    invoke<string>("rcon_connect", { host, port, password }),

  /** Send a command and wait for response (2 s timeout). */
  send: (key: string, cmd: string) =>
    invoke<string>("rcon_send", { key, cmd }),

  /** Tear down active connection. Idempotent. */
  disconnect: (key: string) =>
    invoke<void>("rcon_disconnect", { key }),
};
