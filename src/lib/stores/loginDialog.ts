/**
 * Global login dialog store. Components anywhere can call `loginDialog.open()`
 * to trigger the modal, which is mounted once in +layout.svelte.
 */

import { writable } from "svelte/store";

interface State {
  open: boolean;
  /** Callback fired after successful login. */
  onSuccess?: () => void;
}

function createStore() {
  const { subscribe, set, update } = writable<State>({ open: false });

  return {
    subscribe,
    open(onSuccess?: () => void) {
      set({ open: true, onSuccess });
    },
    close() {
      update((s) => ({ ...s, open: false }));
    },
    setOpen(value: boolean) {
      update((s) => ({ ...s, open: value }));
    },
  };
}

export const loginDialog = createStore();
