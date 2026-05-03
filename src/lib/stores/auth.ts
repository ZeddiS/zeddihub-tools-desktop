import { writable, derived, get } from "svelte/store";
import { authApi, type UserDto, type UserSession } from "$api/auth";

interface AuthState {
  user: UserDto | null;
  token: string | null;
  expiresAt: number;       // unix seconds; 0 = not authenticated
  loading: boolean;        // resume_session in progress
  error: string | null;
}

const initial: AuthState = {
  user: null,
  token: null,
  expiresAt: 0,
  loading: false,
  error: null,
};

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>(initial);

  return {
    subscribe,

    async resume() {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const user = await authApi.me();
        update((s) => ({ ...s, user, loading: false }));
      } catch (e) {
        // No saved session or token expired — silent.
        update((s) => ({ ...s, loading: false }));
      }
    },

    async login(identifier: string, password: string): Promise<boolean> {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const session: UserSession = await authApi.login(identifier, password);
        set({
          user: session.user,
          token: session.token,
          expiresAt: session.expiresAt,
          loading: false,
          error: null,
        });
        return true;
      } catch (e: any) {
        update((s) => ({ ...s, loading: false, error: String(e?.message ?? e) }));
        return false;
      }
    },

    async register(username: string, email: string, password: string): Promise<boolean> {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const session = await authApi.register(username, email, password);
        set({
          user: session.user,
          token: session.token,
          expiresAt: session.expiresAt,
          loading: false,
          error: null,
        });
        return true;
      } catch (e: any) {
        update((s) => ({ ...s, loading: false, error: String(e?.message ?? e) }));
        return false;
      }
    },

    async logout() {
      try {
        await authApi.logout();
      } catch (e) { /* ignore — local cleanup proceeds */ }
      set({ ...initial });
    },

    clearError() {
      update((s) => ({ ...s, error: null }));
    },
  };
}

export const auth = createAuthStore();

export const isAuthenticated = derived(auth, ($a) => $a.user !== null);
export const isAdmin = derived(auth, ($a) => $a.user?.isAdmin === true);
/** Hardcoded special role — true only for username "zeddis" (case-insensitive). */
export const isOwner = derived(auth, ($a) => $a.user?.isOwner === true);
export const currentUser = derived(auth, ($a) => $a.user);
