/**
 * Typed wrappers around Tauri rust_rcon_* commands (Facepunch RCON / WebSocket).
 *
 * Backend: src-tauri/src/services/rust_rcon.rs (tokio-tungstenite WebSocket).
 */

import { invoke } from "@tauri-apps/api/core";

export const rustRconApi = {
  /** Connect ws://host:port/password and authenticate. Returns session key. */
  connect: (host: string, port: number, password: string) =>
    invoke<string>("rust_rcon_connect", { host, port, password }),

  /** Send a console command. Response arrives via `recv()`. */
  send: (key: string, cmd: string) =>
    invoke<void>("rust_rcon_send", { key, cmd }),

  /** Drain any messages buffered since last call. Polled from UI. */
  recv: (key: string) =>
    invoke<string[]>("rust_rcon_recv", { key }),

  disconnect: (key: string) =>
    invoke<void>("rust_rcon_disconnect", { key }),
};
