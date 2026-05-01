<script lang="ts">
  type Variant = "primary" | "secondary" | "ghost";

  let {
    variant = "primary" as Variant,
    type = "button" as "button" | "submit" | "reset",
    disabled = false,
    onclick = undefined as undefined | ((e: MouseEvent) => void),
    class: cls = "",
    children,
  }: {
    variant?: Variant;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    onclick?: (e: MouseEvent) => void;
    class?: string;
    children?: any;
  } = $props();

  const variantClass: Record<Variant, string> = {
    primary:
      "bg-zh-primary text-black hover:bg-zh-primary-hover font-semibold",
    secondary:
      "bg-zh-card-bg text-zh-text hover:bg-zh-card-hover border border-zh-border",
    ghost:
      "bg-transparent text-zh-text hover:bg-zh-card-hover",
  };
</script>

<button
  {type}
  {disabled}
  {onclick}
  class={`px-4 h-9 rounded-button text-sm transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${variantClass[variant]} ${cls}`}
>
  {@render children?.()}
</button>
