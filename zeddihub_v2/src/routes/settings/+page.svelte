<script lang="ts">
  import { Moon, Sun, Globe, User as UserIcon, KeyRound, Folder, RotateCcw } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { t, lang, setLang } from "$stores/locale";
  import { theme, toggleTheme } from "$stores/theme";
  import { auth, isAuthenticated } from "$stores/auth";

  type Tab = "account" | "appearance" | "language" | "data" | "updates";
  let activeTab = $state<Tab>("account");

  // Login form state (used when !$isAuthenticated)
  let loginIdent = $state("");
  let loginPass = $state("");
  let loginBusy = $state(false);

  async function doLogin() {
    if (!loginIdent || !loginPass) return;
    loginBusy = true;
    const ok = await auth.login(loginIdent, loginPass);
    loginBusy = false;
    if (ok) {
      loginIdent = "";
      loginPass = "";
    }
  }

  const tabs: { id: Tab; labelKey: string; icon: any }[] = [
    { id: "account",    labelKey: "settings_account",    icon: UserIcon },
    { id: "appearance", labelKey: "settings_appearance", icon: Moon },
    { id: "language",   labelKey: "settings_language",   icon: Globe },
    { id: "data",       labelKey: "settings_data_folder", icon: Folder },
    { id: "updates",    labelKey: "settings_updates",    icon: RotateCcw },
  ];
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">{$t("settings_title")}</h1>
  <p class="text-zh-text-muted text-sm mb-6">Konfigurace aplikace, účet a předvolby.</p>

  <!-- Tab strip -->
  <div class="flex gap-1 border-b border-zh-border mb-6">
    {#each tabs as tab}
      <button
        class="px-4 h-10 text-sm flex items-center gap-2 border-b-2 transition"
        class:border-zh-primary={activeTab === tab.id}
        class:text-zh-primary={activeTab === tab.id}
        class:border-transparent={activeTab !== tab.id}
        class:text-zh-text-muted={activeTab !== tab.id}
        class:hover:text-zh-text={activeTab !== tab.id}
        on:click={() => (activeTab = tab.id)}
      >
        <svelte:component this={tab.icon} size={14} />
        {$t(tab.labelKey)}
      </button>
    {/each}
  </div>

  <!-- Tab content -->
  {#if activeTab === "account"}
    <Card class="max-w-xl">
      {#if $isAuthenticated}
        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-full bg-zh-success/20 flex items-center justify-center text-zh-success font-bold text-lg">
            {$auth.user?.username?.[0]?.toUpperCase()}
          </div>
          <div>
            <div class="text-base font-semibold">{$auth.user?.username}</div>
            <div class="text-xs text-zh-text-muted">{$auth.user?.email}</div>
            <div class="text-xs text-zh-text-muted mt-0.5">Role: <span class="text-zh-primary">{$auth.user?.role}</span></div>
          </div>
        </div>
        <Button variant="secondary" onclick={() => auth.logout()}>{$t("auth_logout")}</Button>
      {:else}
        <h3 class="text-base font-semibold mb-3">{$t("auth_login")}</h3>
        {#if $auth.error}
          <div class="text-xs text-zh-error bg-zh-error/10 border border-zh-error/30 rounded-button px-3 py-2 mb-3">
            {$auth.error}
          </div>
        {/if}
        <form on:submit|preventDefault={doLogin} class="space-y-3">
          <div>
            <label for="ident" class="text-xs text-zh-text-muted block mb-1">{$t("auth_username")} / e-mail</label>
            <input
              id="ident"
              bind:value={loginIdent}
              autocomplete="username"
              required
              class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
            />
          </div>
          <div>
            <label for="pwd" class="text-xs text-zh-text-muted block mb-1">{$t("auth_password")}</label>
            <input
              id="pwd"
              type="password"
              bind:value={loginPass}
              autocomplete="current-password"
              required
              class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
            />
          </div>
          <Button variant="primary" type="submit" disabled={loginBusy} class="w-full">
            <KeyRound size={14} />
            {loginBusy ? "…" : $t("auth_login")}
          </Button>
        </form>
        <p class="text-xs text-zh-text-muted mt-4">
          Nemáš účet? Přihlášení i registrace probíhá přes
          <a href="https://zeddihub.eu/tools/user/" target="_blank" rel="noopener" class="text-zh-primary hover:underline">
            zeddihub.eu
          </a>.
        </p>
      {/if}
    </Card>
  {:else if activeTab === "appearance"}
    <Card class="max-w-xl">
      <h3 class="text-base font-semibold mb-3">{$t("settings_appearance")}</h3>
      <div class="flex items-center justify-between">
        <div>
          <div class="text-sm">Aktuální motiv</div>
          <div class="text-xs text-zh-text-muted">Tmavý nebo světlý.</div>
        </div>
        <Button variant="secondary" onclick={toggleTheme}>
          {#if $theme === "dark"}
            <Moon size={14} /> Dark
          {:else}
            <Sun size={14} /> Light
          {/if}
        </Button>
      </div>
    </Card>
  {:else if activeTab === "language"}
    <Card class="max-w-xl">
      <h3 class="text-base font-semibold mb-3">{$t("settings_language")}</h3>
      <div class="flex gap-2">
        <Button variant={$lang === "cs" ? "primary" : "secondary"} onclick={() => setLang("cs")}>🇨🇿 Čeština</Button>
        <Button variant={$lang === "en" ? "primary" : "secondary"} onclick={() => setLang("en")}>🇬🇧 English</Button>
      </div>
    </Card>
  {:else if activeTab === "data"}
    <Card class="max-w-xl">
      <h3 class="text-base font-semibold mb-3">{$t("settings_data_folder")}</h3>
      <p class="text-xs text-zh-text-muted">
        Bude implementováno: výběr datové složky, backup, factory reset.
      </p>
    </Card>
  {:else if activeTab === "updates"}
    <Card class="max-w-xl">
      <h3 class="text-base font-semibold mb-3">{$t("settings_updates")}</h3>
      <p class="text-xs text-zh-text-muted mb-3">
        Aktuální verze: <span class="text-zh-text">2.0.0-alpha.1</span>
      </p>
      <Button variant="secondary">Zkontrolovat aktualizace</Button>
    </Card>
  {/if}
</div>
