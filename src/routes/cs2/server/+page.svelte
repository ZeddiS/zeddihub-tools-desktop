<script lang="ts">
  import { FileCog, Layers, Map as MapIcon, Terminal } from "lucide-svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import ServerCfgTab        from "$components/panels/cs2/ServerCfgTab.svelte";
  import GamemodePresetsTab  from "$components/panels/cs2/GamemodePresetsTab.svelte";
  import MapGroupTab         from "$components/panels/cs2/MapGroupTab.svelte";
  import RconClientTab       from "$components/panels/cs2/RconClientTab.svelte";

  type Tab = "servercfg" | "gamemode" | "mapgroup" | "rcon";
  let active = $state<Tab>("servercfg");
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">CS2 — Serverové nástroje</h1>
  <p class="text-zh-text-muted text-sm mb-5">Server.cfg / Gamemode presety / Map Group / RCON klient.</p>

  <Tabs
    bind:active
    tabs={[
      { id: "servercfg", label: "Server.cfg",       icon: FileCog },
      { id: "gamemode",  label: "Gamemode Presety", icon: Layers },
      { id: "mapgroup",  label: "Map Group",        icon: MapIcon },
      { id: "rcon",      label: "RCON Klient",      icon: Terminal },
    ]}
  />

  <div class="mt-6">
    {#if active === "servercfg"}
      <ServerCfgTab />
    {:else if active === "gamemode"}
      <GamemodePresetsTab />
    {:else if active === "mapgroup"}
      <MapGroupTab />
    {:else if active === "rcon"}
      <RconClientTab />
    {/if}
  </div>
</div>
