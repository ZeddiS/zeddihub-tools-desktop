<script lang="ts">
  /**
   * CS:GO DB / Admins editor (light scope) — pick a folder, list .ini/.cfg/.db/.sql files.
   * Mirrors legacy/gui/panels/csgo.py:_build_db_editor (browsing-only stub).
   */

  import { Folder, FileText, Database } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";
  import { readDir } from "@tauri-apps/plugin-fs";

  let folder = $state<string | null>(null);
  let files = $state<string[]>([]);
  let error = $state("");

  const RELEVANT = /\.(ini|cfg|db|sql)$/i;

  async function pickFolder() {
    error = "";
    try {
      const sel = await openDialog({
        directory: true,
        multiple: false,
        title: "Zvolit složku s DB soubory",
      });
      if (!sel || typeof sel !== "string") return;
      folder = sel;
      const entries = await readDir(sel);
      files = entries
        .filter((e) => !e.isDirectory && RELEVANT.test(e.name))
        .map((e) => e.name)
        .sort();
    } catch (e: any) {
      error = `✗ ${e?.message ?? e}`;
    }
  }
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1 flex items-center gap-2">
    <Database size={18} />
    CS:GO — Database / Admini Editor
  </h3>
  <p class="text-xs text-zh-text-muted mb-4">
    Procházení adresáře s konfigurací adminů (SourceMod, sourcebans). Plný editor
    bude přidán v týdnu 9.
  </p>

  <Card class="mb-3">
    <div class="text-sm font-semibold mb-2 flex items-center gap-2">
      <Folder size={14} />
      Zvolte složku s CS:GO DB soubory (.ini, .cfg, .db, .sql)
    </div>
    <div class="flex items-center gap-2">
      <div class="flex-1 bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all min-h-[36px] flex items-center">
        {folder ?? "Nezvolena složka…"}
      </div>
      <Button variant="primary" onclick={pickFolder}>
        <Folder size={14} />
        Zvolit složku
      </Button>
    </div>
    {#if error}
      <div class="mt-2 text-xs text-zh-error">{error}</div>
    {/if}
  </Card>

  {#if folder}
    <Card>
      <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-2">
        Soubory ({files.length})
      </div>
      {#if files.length === 0}
        <div class="text-zh-text-muted text-sm py-4 text-center">
          Žádné databázové soubory (.ini, .cfg, .db, .sql) v této složce.
        </div>
      {:else}
        <div class="font-mono text-xs space-y-1 max-h-72 overflow-auto">
          {#each files as f}
            <div class="flex items-center gap-2 px-2 py-1.5 hover:bg-zh-card-hover rounded transition">
              <FileText size={12} class="text-zh-text-muted" />
              {f}
            </div>
          {/each}
        </div>
      {/if}
    </Card>
  {/if}
</div>
