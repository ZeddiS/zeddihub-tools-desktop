<script lang="ts">
  /**
   * Form row: label + select dropdown + hint.
   * Mirrors `_dropdown_row`.
   */

  let {
    label = "",
    hint = "",
    value = $bindable<string>(""),
    options = [] as Array<string | { value: string; label: string }>,
  }: {
    label?: string;
    hint?: string;
    value?: string;
    options?: Array<string | { value: string; label: string }>;
  } = $props();

  function getValue(o: string | { value: string; label: string }): string {
    return typeof o === "string" ? o : o.value;
  }
  function getLabel(o: string | { value: string; label: string }): string {
    return typeof o === "string" ? o : o.label;
  }
</script>

<label class="grid grid-cols-[180px_1fr] items-center gap-3 py-1.5 text-sm">
  <div class="text-zh-text-muted">
    {label}
    {#if hint}
      <span class="text-[10px] text-zh-text-muted/60 block leading-tight">{hint}</span>
    {/if}
  </div>
  <select
    bind:value
    class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-8 text-sm font-mono focus:outline-none focus:border-zh-primary"
  >
    {#each options as opt}
      <option value={getValue(opt)}>{getLabel(opt)}</option>
    {/each}
  </select>
</label>
