<script lang="ts">
  import { ShieldHalf, Construction } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <ShieldHalf size={26} class="text-zh-primary" />
    Pokročilé
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">
    Advanced administrative tools — registry editor, services, scheduled tasks, GPO viewer.
  </p>

  <Card>
    <div class="flex items-center gap-3 mb-3">
      <Construction size={20} class="text-zh-warning" />
      <h3 class="text-base font-semibold">Plánováno na Phase 4</h3>
    </div>
    <ul class="text-sm text-zh-text-muted space-y-1.5 list-disc pl-5">
      <li>Registry: zh-specific keys quick-access (Mouse, Game Mode, …)</li>
      <li>Services: list + start/stop/disable</li>
      <li>Scheduled tasks: list + run/disable</li>
      <li>Windows Defender exclusions for game folders</li>
      <li>Firewall rules: allow/block per-app</li>
    </ul>
  </Card>
</div>
