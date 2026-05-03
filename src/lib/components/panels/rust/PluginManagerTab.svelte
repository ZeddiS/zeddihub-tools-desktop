<script lang="ts">
  /**
   * Rust Plugin Manager — Oxide/uMod ops on .cs source folders.
   *
   * Mirrors legacy rust.py:_build_plugin_manager (5 ops). Implemented:
   *   - Folder picker
   *   - Detection summary (deps + chat/console cmds + perms count)
   *   - Note: bulk regex patcher / chat translator are heavy ops scheduled
   *     for week 11+ when full Oxide migration tooling lands.
   */

  import { Folder, Wrench, Languages, Tag, BarChart3, Wand2 } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";
  import { readDir, readTextFile } from "@tauri-apps/plugin-fs";

  let folder = $state<string | null>(null);
  let summary = $state("");
  let busy = $state(false);
  let error = $state("");

  const PAT = {
    deps:    /\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)/g,
    chat:    /\[ChatCommand\s*\(\s*"([^"]+)"/g,
    console: /\[ConsoleCommand\s*\(\s*"([^"]+)"/g,
    perms:   /permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"/g,
  };

  function uniqMatches(content: string, pattern: RegExp): string[] {
    const set = new Set<string>();
    for (const m of content.matchAll(pattern)) if (m[1]) set.add(m[1]);
    return Array.from(set);
  }

  async function pickFolder() {
    error = "";
    try {
      const sel = await openDialog({ directory: true, multiple: false, title: "Zvolit složku se .cs pluginy" });
      if (!sel || typeof sel !== "string") return;
      folder = sel;
    } catch (e: any) {
      error = `✗ ${e?.message ?? e}`;
    }
  }

  async function runAnalyzeDeps() {
    if (!folder) {
      error = "✗ Nejprve zvolte složku";
      return;
    }
    busy = true;
    summary = "";
    error = "";
    try {
      const entries = await readDir(folder);
      const csFiles = entries.filter((e) => !e.isDirectory && e.name.endsWith(".cs"));
      if (csFiles.length === 0) {
        summary = "Žádné .cs soubory v této složce.";
        busy = false;
        return;
      }
      const allDeps = new Map<string, number>();
      const allPerms = new Map<string, number>();
      let totalChat = 0, totalConsole = 0;
      for (const f of csFiles) {
        try {
          const content = await readTextFile(`${folder}\\${f.name}`).catch(() => readTextFile(`${folder}/${f.name}`));
          for (const d of uniqMatches(content, PAT.deps))    allDeps.set(d, (allDeps.get(d) ?? 0) + 1);
          for (const p of uniqMatches(content, PAT.perms))   allPerms.set(p, (allPerms.get(p) ?? 0) + 1);
          totalChat    += uniqMatches(content, PAT.chat).length;
          totalConsole += uniqMatches(content, PAT.console).length;
        } catch (_) { /* skip */ }
      }
      const lines: string[] = [];
      lines.push(`=== Analýza závislostí ${csFiles.length} pluginů ===\n`);
      lines.push(`Chat příkazy:    ${totalChat}`);
      lines.push(`Console příkazy: ${totalConsole}`);
      lines.push(`Unikátní závislosti (PluginReference): ${allDeps.size}`);
      lines.push(`Unikátní oprávnění:                    ${allPerms.size}\n`);
      if (allDeps.size > 0) {
        lines.push("Top závislosti (počet pluginů):");
        const sorted = Array.from(allDeps.entries()).sort((a, b) => b[1] - a[1]).slice(0, 15);
        for (const [n, c] of sorted) lines.push(`  • ${n.padEnd(30, ".")} ${c}×`);
      }
      summary = lines.join("\n");
    } catch (e: any) {
      error = `✗ ${e?.message ?? e}`;
    }
    busy = false;
  }

  function notImplemented() {
    error = "Tato operace bude implementována v týdnu 11+ (Oxide bulk regex patcher).";
  }

  const OPS: { name: string; icon: any; handler: () => any | void; title: string }[] = [
    { name: "Hromadná oprava (záplaty)", icon: Wrench,    handler: notImplemented,   title: "Bulk regex fixer" },
    { name: "Úprava příkazů v kódu",     icon: Wand2,     handler: notImplemented,   title: "Edit commands" },
    { name: "Přeložit zprávy v kódu",    icon: Languages, handler: notImplemented,   title: "Translate messages" },
    { name: "Detekce prefixů",            icon: Tag,       handler: notImplemented,   title: "Detect prefixes" },
    { name: "Analýza závislostí",        icon: BarChart3, handler: runAnalyzeDeps,   title: "Dependency summary" },
  ];
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">Rust — Plugin Manager (Oxide/uMod)</h3>
  <p class="text-xs text-zh-text-muted mb-4">Správa, opravy a překlad Oxide pluginů ze zdrojových souborů.</p>

  <Card class="mb-3">
    <div class="flex items-center gap-2">
      <div class="flex-1 bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all min-h-[36px] flex items-center">
        {folder ?? "Nezvolená složka se soubory .cs…"}
      </div>
      <Button variant="primary" onclick={pickFolder}>
        <Folder size={14} />
        Zvolit složku
      </Button>
    </div>
  </Card>

  <Card class="mb-3">
    <h4 class="text-sm font-bold text-zh-primary mb-3">Dostupné operace</h4>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
      {#each OPS as op}
        <Button variant="secondary" onclick={op.handler} disabled={busy}>
          <svelte:component this={op.icon} size={14} />
          {op.name}
        </Button>
      {/each}
    </div>
  </Card>

  {#if summary}
    <Card padding={3}>
      <pre class="bg-black/40 rounded-entry p-3 font-mono text-[11px] leading-snug text-zh-text overflow-auto max-h-96 whitespace-pre-wrap">{summary}</pre>
    </Card>
  {/if}
  {#if error}<div class="mt-2 text-xs text-zh-warning">{error}</div>{/if}
</div>
