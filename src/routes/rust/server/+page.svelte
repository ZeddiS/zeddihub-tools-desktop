<script lang="ts">
  import { Server, Puzzle, Terminal } from "lucide-svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import ServerConfigTab    from "$components/panels/rust/ServerConfigTab.svelte";
  import PluginManagerTab   from "$components/panels/rust/PluginManagerTab.svelte";
  import RustRconTab        from "$components/panels/rust/RustRconTab.svelte";

  type Tab = "config" | "plugins" | "rcon";
  let active = $state<Tab>("config");
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">Rust — Serverové nástroje</h1>
  <p class="text-zh-text-muted text-sm mb-5">Server Config / Plugin Manager / RCON klient (WebSocket).</p>

  <Tabs
    bind:active
    tabs={[
      { id: "config",  label: "Server Config", icon: Server },
      { id: "plugins", label: "Plugin Manager", icon: Puzzle },
      { id: "rcon",    label: "RCON Klient",    icon: Terminal },
    ]}
  />

  <div class="mt-6">
    {#if active === "config"}<ServerConfigTab />
    {:else if active === "plugins"}<PluginManagerTab />
    {:else if active === "rcon"}<RustRconTab />
    {/if}
  </div>
</div>
