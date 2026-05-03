<script lang="ts">
  import { Crosshair, Camera, FileCode, Activity, ShoppingCart } from "lucide-svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import CrosshairTab from "$components/panels/csgo/CrosshairTab.svelte";
  import ViewmodelTab from "$components/panels/csgo/ViewmodelTab.svelte";
  import AutoexecTab  from "$components/panels/csgo/AutoexecTab.svelte";
  import PracticeTab  from "$components/panels/csgo/PracticeTab.svelte";
  import BuyBindsTab  from "$components/panels/csgo/BuyBindsTab.svelte";

  type Tab = "crosshair" | "viewmodel" | "autoexec" | "practice" | "buybinds";
  let active = $state<Tab>("crosshair");
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">CS:GO — Hráčské nástroje</h1>
  <p class="text-zh-text-muted text-sm mb-5">Crosshair / Viewmodel / Autoexec / Practice / Buy Binds — generátory cfg souborů.</p>

  <Tabs
    bind:active
    tabs={[
      { id: "crosshair", label: "Crosshair", icon: Crosshair },
      { id: "viewmodel", label: "Viewmodel", icon: Camera },
      { id: "autoexec",  label: "Autoexec",  icon: FileCode },
      { id: "practice",  label: "Practice",  icon: Activity },
      { id: "buybinds",  label: "Buy Binds", icon: ShoppingCart },
    ]}
  />

  <div class="mt-6">
    {#if active === "crosshair"}<CrosshairTab />
    {:else if active === "viewmodel"}<ViewmodelTab />
    {:else if active === "autoexec"}<AutoexecTab />
    {:else if active === "practice"}<PracticeTab />
    {:else if active === "buybinds"}<BuyBindsTab />
    {/if}
  </div>
</div>
