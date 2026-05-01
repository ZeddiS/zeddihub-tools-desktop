<script lang="ts">
  import { ArrowRight, Check, Globe, Folder, Sparkles } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { lang, setLang, t } from "$stores/locale";
  import { settings } from "$stores/settings";
  import { settingsApi } from "$api/settings";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";

  let step = $state<1 | 2 | 3>(1);
  let dataDir = $state("…");

  onMount(async () => {
    try {
      dataDir = await settingsApi.dataDir();
    } catch {
      dataDir = "Nedostupné";
    }
  });

  async function complete() {
    await settings.patch({ first_launch_done: true, lang: $lang });
    goto("/");
  }
</script>

<div class="h-screen flex items-center justify-center bg-zh-bg p-8 select-none">
  <Card class="w-full max-w-2xl" padding={8}>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <div class="w-12 h-12 rounded-card bg-zh-primary/15 flex items-center justify-center text-zh-primary">
        <Sparkles size={20} />
      </div>
      <div>
        <h1 class="text-2xl font-bold">Vítej v ZeddiHub Tools</h1>
        <p class="text-sm text-zh-text-muted">Pojďme nastavit aplikaci. Pár kroků.</p>
      </div>
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
            🇨🇿 Čeština
          </Button>
          <Button variant={$lang === "en" ? "primary" : "secondary"} onclick={() => setLang("en")}>
            🇬🇧 English
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
          Aplikace bude ukládat nastavení, šifrované přihlašovací údaje, presety a cache do následující složky:
        </p>
        <div class="bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all mb-4 border border-zh-border">
          {dataDir}
        </div>
        <p class="text-xs text-zh-text-muted mb-6">
          Cesta se dá změnit později v Nastavení → Datová složka.
        </p>
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
