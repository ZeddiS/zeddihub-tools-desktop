<script lang="ts">
  import { Minus, Plus } from "lucide-svelte";

  /**
   * Numeric stepper — label + −/+ buttons + numeric input + hint.
   * Mirrors `_stepper_row`.
   */

  let {
    label = "",
    hint = "",
    value = $bindable<string>("0"),
    min = -Infinity,
    max = Infinity,
    step = 1,
  }: {
    label?: string;
    hint?: string;
    value?: string;
    min?: number;
    max?: number;
    step?: number;
  } = $props();

  function clamp(n: number): number {
    return Math.max(min, Math.min(max, n));
  }

  function dec() {
    const cur = parseFloat(value) || 0;
    const next = clamp(cur - step);
    value = formatNum(next);
  }
  function inc() {
    const cur = parseFloat(value) || 0;
    const next = clamp(cur + step);
    value = formatNum(next);
  }

  /** Avoid trailing zeros where step is integer; preserve decimals otherwise. */
  function formatNum(n: number): string {
    if (Number.isInteger(step) && Number.isInteger(n)) return String(n);
    // Drop trailing zeros after decimal
    return n.toFixed(2).replace(/\.?0+$/, "");
  }
</script>

<label class="grid grid-cols-[180px_1fr] items-center gap-3 py-1.5 text-sm">
  <div class="text-zh-text-muted">
    {label}
    {#if hint}
      <span class="text-[10px] text-zh-text-muted/60 block leading-tight">{hint}</span>
    {/if}
  </div>
  <div class="flex items-stretch gap-1">
    <button type="button" onclick={dec} class="w-8 h-8 bg-zh-card-hover hover:bg-zh-border rounded-entry flex items-center justify-center transition">
      <Minus size={12} />
    </button>
    <input
      type="text"
      bind:value
      class="flex-1 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-8 text-sm font-mono text-center focus:outline-none focus:border-zh-primary"
    />
    <button type="button" onclick={inc} class="w-8 h-8 bg-zh-card-hover hover:bg-zh-border rounded-entry flex items-center justify-center transition">
      <Plus size={12} />
    </button>
  </div>
</label>
