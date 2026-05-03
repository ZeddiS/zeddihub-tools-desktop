<script lang="ts">
  import { Gauge, Sliders, Keyboard, BookOpen, Puzzle, Scan } from "lucide-svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import SensitivityTab    from "$components/panels/rust/SensitivityTab.svelte";
  import ClientCfgTab      from "$components/panels/rust/ClientCfgTab.svelte";
  import BindsTab          from "$components/panels/rust/BindsTab.svelte";
  import TipsTab           from "$components/panels/rust/TipsTab.svelte";
  import PluginInfoTab     from "$components/panels/rust/PluginInfoTab.svelte";
  import PluginAnalyzerTab from "$components/panels/rust/PluginAnalyzerTab.svelte";

  type Tab = "sens" | "cfg" | "binds" | "tips" | "plugin-info" | "plugin-analyzer";
  let active = $state<Tab>("sens");
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">Rust — Hráčské nástroje</h1>
  <p class="text-zh-text-muted text-sm mb-5">
    Sensitivity / Client CFG / Bindy / Tipy / Plugin info / Plugin Analyzer.
  </p>

  <Tabs
    bind:active
    tabs={[
      { id: "sens",            label: "Sensitivity",     icon: Gauge },
      { id: "cfg",             label: "Client CFG",      icon: Sliders },
      { id: "binds",           label: "Bindy",           icon: Keyboard },
      { id: "tips",            label: "Tipy & Info",     icon: BookOpen },
      { id: "plugin-info",     label: "Plugin Info",     icon: Puzzle },
      { id: "plugin-analyzer", label: "Plugin Analyzer", icon: Scan },
    ]}
  />

  <div class="mt-6">
    {#if active === "sens"}<SensitivityTab />
    {:else if active === "cfg"}<ClientCfgTab />
    {:else if active === "binds"}<BindsTab />
    {:else if active === "tips"}<TipsTab />
    {:else if active === "plugin-info"}<PluginInfoTab />
    {:else if active === "plugin-analyzer"}<PluginAnalyzerTab />
    {/if}
  </div>
</div>
