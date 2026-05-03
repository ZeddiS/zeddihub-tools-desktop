/**
 * Typed wrappers around Tauri auth_* commands.
 *
 * Backend: src-tauri/src/commands/auth.rs (REST client + encrypted token storage).
 */

import { invoke } from "@tauri-apps/api/core";

export interface UserDto {
  id: number;
  username: string;
  email: string;
  role: string;          // "admin" | "premium" | "user"
  isAdmin: boolean;
  /** Computed server-side from `username.toLowerCase() === "zeddis"`. */
  isOwner: boolean;
}

export interface UserSession {
  user: UserDto;
  token: string;
  expiresAt: number;  // unix seconds
}

export const authApi = {
  login: (identifier: string, password: string) =>
    invoke<UserSession>("auth_login", { identifier, password }),

  register: (username: string, email: string, password: string) =>
    invoke<UserSession>("auth_register", { username, email, password }),

  me: () => invoke<UserDto>("auth_me"),

  logout: () => invoke<void>("auth_logout"),
};
