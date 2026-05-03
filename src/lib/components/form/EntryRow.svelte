<script lang="ts">
  /**
   * Form row: label + text input + optional inline hint.
   * Mirrors `_entry_row` from legacy/gui/panels/cs2.py.
   */

  let {
    label = "",
    hint = "",
    value = $bindable<string>(""),
    placeholder = "",
    type = "text" as "text" | "number" | "password",
    readonly = false,
  }: {
    label?: string;
    hint?: string;
    value?: string;
    placeholder?: string;
    type?: "text" | "number" | "password";
    readonly?: boolean;
  } = $props();
</script>

<label class="grid grid-cols-[180px_1fr] items-center gap-3 py-1.5 text-sm">
  <div class="text-zh-text-muted">
    {label}
    {#if hint}
      <span class="text-[10px] text-zh-text-muted/60 block leading-tight">{hint}</span>
    {/if}
  </div>
  <input
    {type}
    bind:value
    {placeholder}
    {readonly}
    class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-8 text-sm font-mono focus:outline-none focus:border-zh-primary"
  />
</label>
