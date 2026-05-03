<script lang="ts">
  import { ArrowRight, Check, Globe, Folder, Sparkles, FolderOpen } from "lucide-svelte";
  import { Cz, Gb } from "svelte-circle-flags";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { lang, setLang } from "$stores/locale";
  import { settings } from "$stores/settings";
  import { settingsApi } from "$api/settings";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { open as openDialog } from "@tauri-apps/plugin-dialog";

  let step = $state<1 | 2 | 3>(1);
  let dataDir = $state("…");
  let dataDirOverride = $state<string | null>(null);
  let dataDirError = $state("");

  onMount(async () => {
    try {
      dataDir = await settingsApi.dataDir();
    } catch {
      dataDir = "Nedostupné";
    }
  });

  async function pickDataDir() {
    dataDirError = "";
    try {
      const sel = await openDialog({
        directory: true,
        multiple: false,
        title: "Vyber datovou složku",
      });
      if (sel && typeof sel === "string") {
        dataDirOverride = sel;
      }
    } catch (e: any) {
      dataDirError = `✗ ${e?.message ?? e}`;
    }
  }

  async function complete() {
    await settings.patch({
      first_launch_done: true,
      lang: $lang,
      data_dir_override: dataDirOverride ?? null,
    });
    goto("/");
  }

  let displayedDataDir = $derived(dataDirOverride ?? dataDir);
</script>

<div class="h-screen flex items-center justify-center bg-zh-bg p-8 select-none">
  <Card class="w-full max-w-2xl" padding={8}>
    <!-- Header — centered with logo -->
    <div class="flex flex-col items-center text-center mb-6">
      <img src="/logo.png" alt="ZeddiHub" class="w-20 h-20 mb-3 drop-shadow-lg" />
      <h1 class="text-3xl font-bold text-zh-primary">ZeddiHub Tools</h1>
      <p class="text-sm text-zh-text-muted mt-1">Pojďme aplikaci nastavit. Pár kroků.</p>
    </div>

    <!-- Step indicators -->
    <div class="flex items-center gap-2 mb-6 text-xs">
      {#each [1, 2, 3] as n}
        <div
          class="flex items-center gap-2"
          class:text-zh-primary={step >= n}
          class:text-zh-text-muted={step < n}
        >
          <div
            class="w-6 h-6 rounded-full flex items-center justify-center font-bold text-[10px] border"
            class:bg-zh-primary={step > n}
            class:border-zh-primary={step >= n}
            class:text-zh-text-dark={step > n}
            class:border-zh-border={step < n}
          >
            {#if step > n}<Check size={12} />{:else}{n}{/if}
          </div>
          <span>
            {n === 1 ? "Jazyk" : n === 2 ? "Datová složka" : "Hotovo"}
          </span>
        </div>
        {#if n < 3}<div class="flex-1 h-px bg-zh-border"></div>{/if}
      {/each}
    </div>

    <!-- Step content -->
    {#if step === 1}
      <div>
        <div class="flex items-center gap-2 mb-3">
          <Globe size={18} class="text-zh-primary" />
          <h2 class="text-lg font-semibold">Vyber jazyk</h2>
        </div>
        <p class="text-sm text-zh-text-muted mb-4">Zvolíš si později kdykoliv v Nastavení.</p>
        <div class="flex gap-2 mb-6">
          <Button variant={$lang === "cs" ? "primary" : "secondary"} onclick={() => setLang("cs")}>
            <span class="w-5 h-5 inline-flex items-center"><Cz /></span>
            Čeština
          </Button>
          <Button variant={$lang === "en" ? "primary" : "secondary"} onclick={() => setLang("en")}>
            <span class="w-5 h-5 inline-flex items-center"><Gb /></span>
            English
          </Button>
        </div>
        <div class="flex justify-end">
          <Button variant="primary" onclick={() => (step = 2)}>
            Pokračovat
            <ArrowRight size={14} />
          </Button>
        </div>
      </div>

    {:else if step === 2}
      <div>
        <div class="flex items-center gap-2 mb-3">
          <Folder size={18} class="text-zh-primary" />
          <h2 class="text-lg font-semibold">Datová složka</h2>
        </div>
        <p class="text-sm text-zh-text-muted mb-3">
          Aplikace ukládá nastavení, šifrované přihlašovací údaje, presety a cache do následující složky:
        </p>
        <div class="bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all mb-3 border border-zh-border">
          {displayedDataDir}
        </div>
        {#if dataDirOverride}
          <div class="text-xs text-zh-warning mb-3">
            ⚠ Vlastní složka — změna se plně projeví po restartu aplikace.
          </div>
        {/if}
        <div class="flex gap-2 mb-4">
          <Button variant="secondary" onclick={pickDataDir}>
            <FolderOpen size={14} />
            Změnit složku…
          </Button>
          {#if dataDirOverride}
            <Button variant="ghost" onclick={() => (dataDirOverride = null)}>
              Vrátit default
            </Button>
          {/if}
        </div>
        {#if dataDirError}
          <div class="text-xs text-zh-error mb-3">{dataDirError}</div>
        {/if}
        <div class="flex gap-2 justify-between">
          <Button variant="ghost" onclick={() => (step = 1)}>← Zpět</Button>
          <Button variant="primary" onclick={() => (step = 3)}>
            Pokračovat
            <ArrowRight size={14} />
          </Button>
        </div>
      </div>

    {:else if step === 3}
      <div>
        <div class="flex items-center gap-2 mb-3">
          <Sparkles size={18} class="text-zh-success" />
          <h2 class="text-lg font-semibold">Hotovo!</h2>
        </div>
        <p class="text-sm text-zh-text-muted mb-4">
          Aplikace je připravená. Některé panely (CS2 ServerTools, Watchdog, atd.) vyžadují přihlášení —
          to můžeš udělat v Nastavení nebo přes 🔓 ikonu v hlavičce.
        </p>
        <ul class="text-sm space-y-1.5 mb-6 text-zh-text-muted">
          <li>✨ <span class="text-zh-text">25+ panelů</span> pro správu CS2 / CS:GO / Rust serverů</li>
          <li>🌐 <span class="text-zh-text">Sdílený účet</span> s mobilní aplikací a webem</li>
          <li>🌙 <span class="text-zh-text">Dark / Light</span> motiv, CS / EN jazyk</li>
          <li>💾 <span class="text-zh-text">Lokální data</span> šifrovaná machine-bound klíčem</li>
        </ul>
        <div class="flex gap-2 justify-between">
          <Button variant="ghost" onclick={() => (step = 2)}>← Zpět</Button>
          <Button variant="primary" onclick={complete}>
            <Check size={14} />
            Spustit aplikaci
          </Button>
        </div>
      </div>
    {/if}
  </Card>
</div>
