<script lang="ts">
  /**
   * Form row: label + binary toggle (stores "0" / "1" as string for cfg compat).
   * Mirrors `_bool_row`.
   */

  let {
    label = "",
    hint = "",
    value = $bindable<string>("0"),
  }: {
    label?: string;
    hint?: string;
    value?: string;
  } = $props();

  let on = $derived(value === "1");

  function toggle() {
    value = on ? "0" : "1";
  }
</script>

<label class="grid grid-cols-[180px_1fr] items-center gap-3 py-1.5 text-sm cursor-pointer">
  <div class="text-zh-text-muted">
    {label}
    {#if hint}
      <span class="text-[10px] text-zh-text-muted/60 block leading-tight">{hint}</span>
    {/if}
  </div>
  <button
    type="button"
    onclick={toggle}
    class="relative w-12 h-6 rounded-full transition-colors"
    class:bg-zh-primary={on}
    class:bg-zh-border={!on}
  >
    <span
      class="absolute top-0.5 w-5 h-5 bg-white rounded-full transition-all"
      class:left-0.5={!on}
      class:left-[calc(100%-1.375rem)]={on}
    ></span>
  </button>
</label>
