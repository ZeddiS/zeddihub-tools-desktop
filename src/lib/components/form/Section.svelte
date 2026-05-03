<script lang="ts">
  import Card from "$components/ui/Card.svelte";

  let {
    title,
    children,
  }: {
    title: string;
    children?: any;
  } = $props();
</script>

<Card class="mb-3">
  <h3 class="text-sm font-bold text-zh-primary mb-2">{title}</h3>
  {@render children?.()}
</Card>
