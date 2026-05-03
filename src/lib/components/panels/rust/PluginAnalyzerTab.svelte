<script lang="ts">
  /**
   * Bulk Oxide plugin folder analyzer.
   * Mirrors legacy/gui/panels/rust.py:_pick_plugin_folder + _export_report.
   */

  import { Folder, FileText, Save } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";
  import { readDir, readTextFile } from "@tauri-apps/plugin-fs";
  import { saveCfgFile } from "$api/saveFile";

  const PAT = {
    deps:    /\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)/g,
    chat:    /\[ChatCommand\s*\(\s*"([^"]+)"/g,
    console: /\[ConsoleCommand\s*\(\s*"([^"]+)"/g,
    hooks:   /(?:void|object|bool|string)\s+(On\w+|Can\w+)\s*\(/g,
    perms:   /permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"/g,
  };

  interface PluginInfo {
    file: string;
    deps: string[];
    chat: string[];
    console: string[];
    hooks: string[];
    perms: string[];
    features: string[];
  }

  let folder = $state<string | null>(null);
  let results = $state<PluginInfo[]>([]);
  let error = $state("");
  let busy = $state(false);
  let saveStatus = $state("");

  function uniq(matches: IterableIterator<RegExpMatchArray>): string[] {
    const set = new Set<string>();
    for (const m of matches) if (m[1]) set.add(m[1]);
    return Array.from(set);
  }

  async function pick() {
    error = "";
    try {
      const sel = await openDialog({ directory: true, multiple: false, title: "Zvolit složku s pluginy" });
      if (!sel || typeof sel !== "string") return;
      folder = sel;
      busy = true;
      results = [];
      const entries = await readDir(sel);
      const csFiles = entries.filter((e) => !e.isDirectory && e.name.endsWith(".cs"));
      const out: PluginInfo[] = [];
      for (const f of csFiles) {
        try {
          const content = await readTextFile(`${sel}\\${f.name}`).catch(async () => readTextFile(`${sel}/${f.name}`));
          const features: string[] = [];
          if (content.includes("LoadConfig"))   features.push("Config");
          if (content.includes("lang.Register")) features.push("Lang");
          if (content.includes("DataFileSystem")) features.push("Data");
          out.push({
            file: f.name,
            deps:    uniq(content.matchAll(PAT.deps)),
            chat:    uniq(content.matchAll(PAT.chat)),
            console: uniq(content.matchAll(PAT.console)),
            hooks:   uniq(content.matchAll(PAT.hooks)),
            perms:   uniq(content.matchAll(PAT.perms)),
            features,
          });
        } catch (_) { /* skip unreadable */ }
      }
      results = out;
    } catch (e: any) {
      error = `✗ ${e?.message ?? e}`;
    }
    busy = false;
  }

  async function exportReport() {
    saveStatus = "";
    if (results.length === 0) {
      saveStatus = "✗ Nejprve zvolte složku s pluginy";
      return;
    }
    let content = "ZeddiHub Plugin Dependency Report\n" + "=".repeat(60) + "\n\n";
    for (const r of results) {
      content += `Plugin: ${r.file}\n`;
      content += `  Dependencies: ${r.deps.join(", ") || "None"}\n`;
      content += `  Hooks (${r.hooks.length}): ${r.hooks.slice(0, 10).join(", ")}\n`;
      content += `  Commands: ${[...r.chat, ...r.console].join(", ") || "None"}\n`;
      content += `  Features: ${r.features.join(", ") || "None"}\n\n`;
    }
    try {
      const path = await saveCfgFile(content, {
        defaultName: "plugin_report.txt",
        title: "Uložit report",
        filters: [{ name: "Text", extensions: ["txt"] }, { name: "All", extensions: ["*"] }],
      });
      if (path) saveStatus = `✓ Uloženo: ${path}`;
    } catch (e: any) {
      saveStatus = `✗ ${e?.message ?? e}`;
    }
  }
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">Rust — Hromadná Analýza Pluginů</h3>
  <p class="text-xs text-zh-text-muted mb-4">Zvolte složku se .cs pluginy a zobrazte souhrn závislostí.</p>

  <Card class="mb-3">
    <div class="flex items-center gap-2">
      <div class="flex-1 bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all min-h-[36px] flex items-center">
        {folder ?? "Nezvolená složka…"}
      </div>
      <Button variant="primary" onclick={pick} disabled={busy}>
        <Folder size={14} />
        {busy ? "…" : "Zvolit složku"}
      </Button>
    </div>
    {#if error}<div class="mt-2 text-xs text-zh-error">{error}</div>{/if}
  </Card>

  {#if results.length > 0}
    <Card padding={3} class="mb-3">
      <div class="flex items-center justify-between mb-2 text-xs">
        <span class="text-zh-text-muted">=== Analýza {results.length} pluginů ===</span>
      </div>
      <pre class="bg-black/40 rounded-entry p-3 font-mono text-[11px] leading-snug text-zh-text overflow-auto max-h-96">{
        results.map((r) =>
          `\n${r.file}\n` +
          `  Deps: ${r.deps.join(", ") || "žádné"}\n` +
          `  Hooks: ${r.hooks.length}  Chat cmds: ${r.chat.length}  Console cmds: ${r.console.length}\n` +
          `  Funkce: ${r.features.join(", ") || "žádné"}`
        ).join("\n")
      }</pre>
    </Card>

    <Button variant="primary" onclick={exportReport}>
      <Save size={14} />
      Exportovat report .txt
    </Button>

    {#if saveStatus}<div class="mt-2 text-xs text-zh-text-muted">{saveStatus}</div>{/if}
  {/if}
</div>
