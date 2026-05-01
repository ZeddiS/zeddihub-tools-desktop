/**
 * Typed wrappers around Tauri net_tools_* commands.
 */

import { invoke } from "@tauri-apps/api/core";

export const netToolsApi = {
  /** DNS lookup (A/AAAA via OS resolver). recordType is currently informational. */
  dnsLookup: (domain: string, recordType: string = "A") =>
    invoke<string[]>("net_dns_lookup", { domain, recordType }),

  /** TCP port check. Returns true if connect within timeout succeeds. */
  portCheck: (host: string, port: number, timeoutMs: number = 3000) =>
    invoke<boolean>("net_port_check", { host, port, timeoutMs }),
};
