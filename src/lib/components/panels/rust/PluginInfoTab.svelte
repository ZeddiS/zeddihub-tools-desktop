<script lang="ts">
  /**
   * Single Oxide plugin (.cs) analyzer.
   * Mirrors legacy/gui/panels/rust.py:_analyze_plugin_file (regex parser).
   */

  import { File, Search } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";
  import { readTextFile } from "@tauri-apps/plugin-fs";

  const PATTERNS = {
    "Závislosti (PluginReference)": /\[PluginReference\]\s*(?:private\s+)?Plugin\s+(\w+)/g,
    "Requires":                     /\[Requires\("([^"]+)"\)\]/g,
    "Chat příkazy":                 /\[ChatCommand\s*\(\s*"([^"]+)"/g,
    "Console příkazy":              /\[ConsoleCommand\s*\(\s*"([^"]+)"/g,
    "Hooks":                        /(?:void|object|bool|string)\s+(On\w+|Can\w+)\s*\(/g,
    "Oprávnění":                    /permission\.Register(?:Permission)?\s*\(\s*"([^"]+)"/g,
  } as const;

  let path = $state<string | null>(null);
  let report = $state("");
  let error = $state("");

  async function pick() {
    error = "";
    try {
      const sel = await openDialog({
        multiple: false,
        filters: [{ name: "C# Soubor", extensions: ["cs"] }],
        title: "Zvolit .cs plugin",
      });
      if (!sel || typeof sel !== "string") return;
      path = sel;
      const content = await readTextFile(sel);
      analyze(content, sel);
    } catch (e: any) {
      error = `✗ ${e?.message ?? e}`;
    }
  }

  function analyze(content: string, filepath: string) {
    const filename = filepath.split(/[\\/]/).pop() || filepath;
    const lines: string[] = [`=== Analýza: ${filename} ===\n`];

    for (const [name, pat] of Object.entries(PATTERNS)) {
      const matches = new Set<string>();
      for (const m of content.matchAll(pat)) {
        if (m[1]) matches.add(m[1]);
      }
      if (matches.size > 0) {
        lines.push(`\n${name} (${matches.size}):`);
        for (const m of Array.from(matches).sort()) {
          lines.push(`  • ${m}`);
        }
      }
    }

    const feat: string[] = [];
    if (content.includes("LoadConfig") || content.includes("SaveConfig")) feat.push("Config");
    if (content.includes("lang.Register") || content.includes("lang.GetMessage")) feat.push("Lang");
    if (content.includes("DataFileSystem")) feat.push("DataFile");
    lines.push(`\nFunkce: ${feat.length ? feat.join(", ") : "Žádné"}`);

    report = lines.join("\n");
  }
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">Rust — Informace o pluginech</h3>
  <p class="text-xs text-zh-text-muted mb-4">Zvolte .cs plugin soubor pro detailní analýzu.</p>

  <Card class="mb-3">
    <div class="flex items-center gap-2">
      <div class="flex-1 bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all min-h-[36px] flex items-center">
        {path ?? "Nezvolený soubor…"}
      </div>
      <Button variant="primary" onclick={pick}>
        <File size={14} />
        Zvolit .cs plugin
      </Button>
    </div>
    {#if error}<div class="mt-2 text-xs text-zh-error">{error}</div>{/if}
  </Card>

  <Card padding={3}>
    <div class="flex items-center gap-2 mb-2 text-xs text-zh-text-muted">
      <Search size={12} />
      <span>Výstup analýzy</span>
    </div>
    <pre class="bg-black/40 rounded-entry p-3 font-mono text-[11px] leading-relaxed text-zh-text overflow-auto max-h-96 whitespace-pre-wrap break-words">{report || "Vyber plugin pro zobrazení analýzy."}</pre>
  </Card>
</div>
