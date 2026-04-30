<script lang="ts">
  let {
    /** Padding in `p-N` (Tailwind units, default `p-5` = 20 px). */
    padding = 5,
    /** Optional accent color strip on top (CSS color value). */
    strip = "",
    /** If `true`, card has 1px border. */
    bordered = false,
    /** Pass-through class extension. */
    class: cls = "",
    children,
    ...rest
  }: {
    padding?: number;
    strip?: string;
    bordered?: boolean;
    class?: string;
    children?: any;
    [key: string]: any;
  } = $props();
</script>

<div
  class={`relative bg-zh-card-bg rounded-card overflow-hidden ${bordered ? "border border-zh-border" : ""} ${cls}`}
  {...rest}
>
  {#if strip}
    <div class="absolute inset-x-0 top-0 h-0.5" style:background-color={strip}></div>
  {/if}
  <div class={`p-${padding}`}>
    {@render children?.()}
  </div>
</div>
