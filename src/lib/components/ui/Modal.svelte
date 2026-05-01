<script lang="ts">
  /**
   * Modal dialog with backdrop + Esc-to-close + click-outside-to-close.
   *
   * Use:
   *   <Modal bind:open onClose={...} title="Login">
   *     <p>content</p>
   *   </Modal>
   */

  import { onMount } from "svelte";
  import { X } from "lucide-svelte";

  let {
    open = $bindable(false),
    title = "",
    width = "max-w-md" as string,
    onClose = undefined as undefined | (() => void),
    closeOnBackdrop = true,
    children,
  }: {
    open?: boolean;
    title?: string;
    width?: string;
    onClose?: () => void;
    closeOnBackdrop?: boolean;
    children?: any;
  } = $props();

  function close() {
    open = false;
    onClose?.();
  }

  onMount(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && open) {
        close();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  function handleBackdropClick(e: MouseEvent) {
    if (closeOnBackdrop && e.target === e.currentTarget) {
      close();
    }
  }
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
    onclick={handleBackdropClick}
    role="presentation"
  >
    <div
      class={`bg-zh-card-bg border border-zh-border rounded-card shadow-2xl w-full ${width} max-h-[90vh] overflow-auto`}
      role="dialog"
      aria-modal="true"
    >
      {#if title}
        <div class="flex items-center justify-between px-5 py-3 border-b border-zh-divider">
          <h2 class="text-base font-semibold">{title}</h2>
          <button
            type="button"
            class="w-7 h-7 rounded-button flex items-center justify-center text-zh-text-muted hover:text-zh-text hover:bg-zh-card-hover transition"
            onclick={close}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>
      {/if}
      <div class="px-5 py-4">
        {@render children?.()}
      </div>
    </div>
  </div>
{/if}
