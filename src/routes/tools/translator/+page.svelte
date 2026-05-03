<script lang="ts">
  import { Languages, Play, FolderOpen, Save, Loader } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { open as openDialog, save as saveDialog } from "@tauri-apps/plugin-dialog";
  import { readTextFile, writeTextFile } from "@tauri-apps/plugin-fs";

  const LANGS: { code: string; label: string }[] = [
    { code: "auto", label: "Auto-detect" },
    { code: "en",   label: "English" },
    { code: "cs",   label: "Čeština" },
    { code: "de",   label: "Deutsch" },
    { code: "es",   label: "Español" },
    { code: "fr",   label: "Français" },
    { code: "it",   label: "Italiano" },
    { code: "pl",   label: "Polski" },
    { code: "ru",   label: "Русский" },
    { code: "uk",   label: "Українська" },
    { code: "sk",   label: "Slovenčina" },
    { code: "pt",   label: "Português" },
    { code: "nl",   label: "Nederlands" },
    { code: "tr",   label: "Türkçe" },
    { code: "ja",   label: "日本語" },
    { code: "ko",   label: "한국어" },
    { code: "zh",   label: "中文" },
    { code: "ar",   label: "العربية" },
    { code: "hu",   label: "Magyar" },
    { code: "ro",   label: "Română" },
  ];

  type Engine = "google" | "mymemory" | "libretranslate";

  let engine = $state<Engine>("mymemory");
  let srcLang = $state("auto");
  let dstLang = $state("cs");
  let inputText = $state("");
  let outputText = $state("");
  let busy = $state(false);
  let status = $state("");
  let inputFile = $state<string | null>(null);

  async function pickInput() {
    const sel = await openDialog({
      multiple: false,
      filters: [
        { name: "JSON / Text", extensions: ["json", "txt", "lang", "ini", "cfg"] },
        { name: "All", extensions: ["*"] },
      ],
      title: "Vyber zdrojový soubor",
    });
    if (!sel || typeof sel !== "string") return;
    inputFile = sel;
    try {
      inputText = await readTextFile(sel);
      status = `✓ Načteno: ${sel.split(/[\\/]/).pop()}  (${inputText.length} znaků)`;
    } catch (e: any) {
      status = `✗ ${e?.message ?? e}`;
    }
  }

  async function saveOutput() {
    if (!outputText) return;
    const ext = inputFile ? inputFile.split(".").pop() : "txt";
    const def = inputFile
      ? inputFile.replace(/\.([^.]+)$/, `_${dstLang}.$1`).split(/[\\/]/).pop()
      : `output_${dstLang}.${ext}`;
    const path = await saveDialog({
      defaultPath: def,
      filters: [{ name: "Text", extensions: [ext ?? "txt"] }, { name: "All", extensions: ["*"] }],
      title: "Uložit přeložený soubor",
    });
    if (!path) return;
    try {
      await writeTextFile(path, outputText);
      status = `✓ Uloženo: ${path}`;
    } catch (e: any) {
      status = `✗ ${e?.message ?? e}`;
    }
  }

  // ── Engines ────────────────────────────────────────────────────
  async function mymemoryTranslate(text: string, src: string, dst: string): Promise<string> {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${src === "auto" ? "auto" : src}|${dst}`;
    const resp = await fetch(url);
    const data = await resp.json();
    if (data?.responseData?.translatedText) return data.responseData.translatedText;
    throw new Error(data?.responseDetails ?? "MyMemory translate failed");
  }

  async function googleTranslate(text: string, src: string, dst: string): Promise<string> {
    const sl = src === "auto" ? "auto" : src;
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sl}&tl=${dst}&dt=t&q=${encodeURIComponent(text)}`;
    const resp = await fetch(url);
    const data = await resp.json();
    if (Array.isArray(data) && Array.isArray(data[0])) {
      return data[0].map((seg: any[]) => seg[0]).join("");
    }
    throw new Error("Google translate parse error");
  }

  async function libreTranslate(text: string, src: string, dst: string): Promise<string> {
    const resp = await fetch("https://libretranslate.com/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: text, source: src === "auto" ? "auto" : src, target: dst, format: "text" }),
    });
    const data = await resp.json();
    if (typeof data?.translatedText === "string") return data.translatedText;
    throw new Error(data?.error ?? "LibreTranslate failed");
  }

  async function translateText(text: string, src: string, dst: string): Promise<string> {
    switch (engine) {
      case "google":         return googleTranslate(text, src, dst);
      case "libretranslate": return libreTranslate(text, src, dst);
      default:               return mymemoryTranslate(text, src, dst);
    }
  }

  async function translate() {
    if (busy || !inputText.trim()) return;
    busy = true;
    status = `Překládám přes ${engine}…`;
    try {
      const chunks = inputText.split(/\n\n+/);
      const translated: string[] = [];
      for (const chunk of chunks) {
        if (!chunk.trim()) {
          translated.push(chunk);
          continue;
        }
        translated.push(await translateText(chunk, srcLang, dstLang));
      }
      outputText = translated.join("\n\n");
      status = `✓ Hotovo (${chunks.length} chunks, ${outputText.length} znaků)`;
    } catch (e: any) {
      status = `✗ ${e?.message ?? e}`;
    }
    busy = false;
  }
</script>

<div class="px-8 py-6 max-w-[1200px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Languages size={26} class="text-zh-primary" />
    Translator
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">
    Hromadný překladač pro .json / .txt / .lang / .ini soubory. 3 enginy: MyMemory (zdarma), Google Translate, LibreTranslate.
  </p>

  <Card class="mb-3">
    <div class="flex flex-wrap items-end gap-3">
      <label class="flex flex-col gap-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Engine</span>
        <select bind:value={engine}
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary">
          <option value="mymemory">MyMemory (free)</option>
          <option value="google">Google Translate</option>
          <option value="libretranslate">LibreTranslate</option>
        </select>
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Z jazyka</span>
        <select bind:value={srcLang}
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary">
          {#each LANGS as l}<option value={l.code}>{l.label}</option>{/each}
        </select>
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Do jazyka</span>
        <select bind:value={dstLang}
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary">
          {#each LANGS.filter(l => l.code !== "auto") as l}<option value={l.code}>{l.label}</option>{/each}
        </select>
      </label>
      <Button variant="ghost" onclick={pickInput}>
        <FolderOpen size={14} /> Načíst soubor…
      </Button>
      <Button variant="primary" onclick={translate} disabled={busy || !inputText.trim()}>
        {#if busy}<Loader size={14} class="animate-spin" />{:else}<Play size={14} />{/if}
        Přeložit
      </Button>
    </div>
    {#if status}<div class="text-xs text-zh-text-muted mt-3">{status}</div>{/if}
  </Card>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
    <Card padding={3}>
      <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-2">Vstup</div>
      <textarea bind:value={inputText} rows="18" spellcheck="false"
        placeholder="Vlož text k přeložení nebo načti soubor…"
        class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 py-2 text-xs font-mono leading-relaxed focus:outline-none focus:border-zh-primary resize-y"></textarea>
      <div class="text-[10px] text-zh-text-muted mt-1 text-right">{inputText.length} znaků</div>
    </Card>

    <Card padding={3}>
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs uppercase tracking-wider text-zh-text-muted">Výstup</span>
        <Button variant="ghost" onclick={saveOutput} disabled={!outputText} class="!h-6 text-[10px]">
          <Save size={11} /> Uložit
        </Button>
      </div>
      <textarea bind:value={outputText} rows="18" spellcheck="false" readonly
        placeholder="Sem se zobrazí přeložený text…"
        class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 py-2 text-xs font-mono leading-relaxed focus:outline-none focus:border-zh-primary resize-y"></textarea>
      <div class="text-[10px] text-zh-text-muted mt-1 text-right">{outputText.length} znaků</div>
    </Card>
  </div>
</div>
