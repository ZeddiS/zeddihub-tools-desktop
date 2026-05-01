<script lang="ts">
  import { Construction } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";

  let { title, week = "?" }: { title: string; week?: string | number } = $props();
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">{title}</h1>
  <p class="text-zh-text-muted text-sm mb-6">Tento panel ještě není migrován z Python verze.</p>

  <Card>
    <div class="flex items-center gap-3 mb-3">
      <Construction size={20} class="text-zh-warning" />
      <h3 class="text-base font-semibold">Plánováno na Týden {week}</h3>
    </div>
    <p class="text-sm text-zh-text-muted">
      Aktuální v1.7.12 verze (Python + customtkinter) tento panel obsahuje. Při dalším
      session ho přepíšu do Svelte/Tauri 1:1 s feature parity. Detail v
      <a href="https://github.com/ZeddiS/zeddihub-tools-desktop/blob/master/MIGRATION.md"
         target="_blank" rel="noopener" class="text-zh-primary hover:underline">
        MIGRATION.md
      </a>.
    </p>
  </Card>
</div>
