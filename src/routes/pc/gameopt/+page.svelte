<script lang="ts">
  import { Gamepad2, Construction } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Gamepad2 size={26} class="text-zh-primary" />
    Herní optimalizace
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">
    Hardware tuning pro herní výkon — High Performance power plan, Game Mode toggle,
    Network throttling, Mouse precision off, atd.
  </p>

  <Card>
    <div class="flex items-center gap-3 mb-3">
      <Construction size={20} class="text-zh-warning" />
      <h3 class="text-base font-semibold">Plánováno na Phase 4 (po dokončení mainline migrace)</h3>
    </div>
    <ul class="text-sm text-zh-text-muted space-y-1.5 list-disc pl-5">
      <li>Power plan toggle (High Performance / Balanced)</li>
      <li>Game Mode + Game Bar enable/disable přes registry</li>
      <li>Network: TCP Ack frequency, Nagle's algorithm</li>
      <li>Mouse: precision-pointer off, "Enhance pointer precision"</li>
      <li>Visual effects: best performance preset</li>
      <li>NVIDIA / AMD control panel deep links</li>
    </ul>
  </Card>
</div>
