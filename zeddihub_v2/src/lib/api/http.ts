/**
 * Typed wrappers around Tauri http_* commands.
 *
 * Backend: src-tauri/src/commands/http.rs (TTL cache).
 */

import { invoke } from "@tauri-apps/api/core";

export const httpApi = {
  /**
   * Fetch JSON from URL with TTL cache. If `forceRefresh` is true,
   * bypasses cache. Returns cached payload on network failure if available.
   */
  fetchJson: <T = unknown>(url: string, ttlSeconds = 1800, forceRefresh = false) =>
    invoke<T>("http_fetch_json", { url, ttlSeconds, forceRefresh }),

  /** Returns last-fetched age in seconds, or null if never fetched. */
  cacheAge: (url: string) => invoke<number | null>("http_cache_age", { url }),

  /** Drop a single URL from cache (force re-fetch next time). */
  invalidate: (url: string) => invoke<void>("http_invalidate", { url }),
};
