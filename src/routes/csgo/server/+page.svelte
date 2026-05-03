<script lang="ts">
  import { FileCog, Database, Terminal } from "lucide-svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import ServerCfgTab from "$components/panels/csgo/ServerCfgTab.svelte";
  import DbEditorTab from "$components/panels/csgo/DbEditorTab.svelte";
  // CS:GO uses identical Source RCON protocol as CS2 — reuse the tab.
  import RconClientTab from "$components/panels/cs2/RconClientTab.svelte";

  type Tab = "servercfg" | "db" | "rcon";
  let active = $state<Tab>("servercfg");
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">CS:GO — Serverové nástroje</h1>
  <p class="text-zh-text-muted text-sm mb-5">Server.cfg / DB Editor / RCON klient.</p>

  <Tabs
    bind:active
    tabs={[
      { id: "servercfg", label: "Server.cfg",   icon: FileCog },
      { id: "db",        label: "DB Editor",    icon: Database },
      { id: "rcon",      label: "RCON Klient",  icon: Terminal },
    ]}
  />

  <div class="mt-6">
    {#if active === "servercfg"}<ServerCfgTab />
    {:else if active === "db"}<DbEditorTab />
    {:else if active === "rcon"}<RconClientTab />
    {/if}
  </div>
</div>
