<script lang="ts">
  import {
    Moon, Sun, Globe, User as UserIcon, Folder, RotateCcw, ExternalLink,
    Trash2, ShieldAlert, FolderOpen, AlertTriangle, KeyRound, LogOut as LogOutIcon,
  } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import Modal from "$components/ui/Modal.svelte";
  import { t, lang, setLang } from "$stores/locale";
  import { theme, toggleTheme } from "$stores/theme";
  import { auth, isAuthenticated } from "$stores/auth";
  import { settings } from "$stores/settings";
  import { loginDialog } from "$stores/loginDialog";
  import { settingsApi } from "$api/settings";
  import { onMount } from "svelte";
  import { open as openUrl } from "@tauri-apps/plugin-shell";
  import { getVersion } from "@tauri-apps/api/app";

  type Tab = "account" | "appearance" | "language" | "data" | "updates";
  let activeTab = $state<Tab>("account");

  let dataDir = $state("…");
  let appVersion = $state("…");

  // Confirm modals
  let confirmFactoryReset = $state(false);
  let confirmLogout = $state(false);

  let factoryStatus = $state("");

  onMount(async () => {
    await settings.ensureLoaded();
    try {
      dataDir = await settingsApi.dataDir();
    } catch (e) {
      dataDir = "Nedostupné";
    }
    try {
      appVersion = await getVersion();
    } catch {
      appVersion = "?";
    }
  });

  async function doFactoryReset() {
    confirmFactoryReset = false;
    try {
      const removed = await settings.factoryReset();
      factoryStatus = `✓ Smazáno ${removed} položek z datové složky.`;
    } catch (e: any) {
      factoryStatus = `✗ ${e?.message ?? e}`;
    }
  }

  async function openDataDir() {
    try {
      await openUrl(dataDir);
    } catch (e) {
      console.warn("openDataDir failed:", e);
    }
  }

  async function logout() {
    confirmLogout = false;
    await auth.logout();
  }
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">{$t("settings_title")}</h1>
  <p class="text-zh-text-muted text-sm mb-6">Konfigurace aplikace, účet a předvolby.</p>

  <Tabs
    bind:active={activeTab}
    tabs={[
      { id: "account",    label: $t("settings_account"),     icon: UserIcon },
      { id: "appearance", label: $t("settings_appearance"),  icon: Moon },
      { id: "language",   label: $t("settings_language"),    icon: Globe },
      { id: "data",       label: $t("settings_data_folder"), icon: Folder },
      { id: "updates",    label: $t("settings_updates"),     icon: RotateCcw },
    ]}
  />

  <div class="mt-6">
    {#if activeTab === "account"}
      <Card class="max-w-xl">
        {#if $isAuthenticated}
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded-full bg-zh-success/20 flex items-center justify-center text-zh-success font-bold text-lg">
              {$auth.user?.username?.[0]?.toUpperCase()}
            </div>
            <div class="flex-1">
              <div class="text-base font-semibold">{$auth.user?.username}</div>
              <div class="text-xs text-zh-text-muted">{$auth.user?.email}</div>
              <div class="text-xs text-zh-text-muted mt-0.5">
                Role: <span class="text-zh-primary font-mono">{$auth.user?.role}</span>
                {#if $auth.user?.isAdmin}
                  <span class="text-[9px] bg-zh-primary text-zh-text-dark px-1.5 py-0.5 ml-2 rounded font-bold">ADMIN</span>
                {/if}
              </div>
            </div>
          </div>
          <div class="flex gap-2">
            <Button variant="secondary" onclick={() => (confirmLogout = true)}>
              <LogOutIcon size={14} />
              {$t("auth_logout")}
            </Button>
            <Button variant="ghost" onclick={() => openUrl("https://zeddihub.eu/tools/user/")}>
              <ExternalLink size={14} />
              Spravovat účet (web)
            </Button>
          </div>
        {:else}
          <h3 class="text-base font-semibold mb-3">{$t("auth_login")}</h3>
          <p class="text-sm text-zh-text-muted mb-3">
            Pro přístup k server nástrojům a admin sekcím se musíš přihlásit.
          </p>
          <Button variant="primary" onclick={() => loginDialog.open()}>
            <KeyRound size={14} />
            {$t("auth_login")}
          </Button>
        {/if}
      </Card>

    {:else if activeTab === "appearance"}
      <Card class="max-w-xl">
        <h3 class="text-base font-semibold mb-3">{$t("settings_appearance")}</h3>
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm">Aktuální motiv</div>
            <div class="text-xs text-zh-text-muted">Dark / Light</div>
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
          <Button variant={$lang === "cs" ? "primary" : "secondary"} onclick={() => setLang("cs")}>
            🇨🇿 Čeština
          </Button>
          <Button variant={$lang === "en" ? "primary" : "secondary"} onclick={() => setLang("en")}>
            🇬🇧 English
          </Button>
        </div>
      </Card>

    {:else if activeTab === "data"}
      <div class="max-w-xl space-y-4">
        <Card>
          <h3 class="text-base font-semibold mb-2">{$t("settings_data_folder")}</h3>
          <div class="text-xs text-zh-text-muted mb-2">
            Aplikace ukládá nastavení, šifrované přihlašovací údaje, presety a cache do následující složky:
          </div>
          <div class="bg-zh-card-hover rounded-entry px-3 py-2 text-xs font-mono break-all mb-3">
            {dataDir}
          </div>
          <Button variant="secondary" onclick={openDataDir}>
            <FolderOpen size={14} />
            Otevřít ve správci souborů
          </Button>
        </Card>

        <Card>
          <h3 class="text-base font-semibold mb-1 flex items-center gap-2">
            <ShieldAlert size={16} class="text-zh-error" />
            Factory reset
          </h3>
          <p class="text-xs text-zh-text-muted mb-3">
            Smaže VŠE v datové složce kromě šifrovacího klíče (`.key`) — nastavení, presety, cache, přihlášení.
            Operace je nevratná.
          </p>
          {#if factoryStatus}
            <div class="text-xs text-zh-text mb-3">{factoryStatus}</div>
          {/if}
          <Button variant="secondary" onclick={() => (confirmFactoryReset = true)}>
            <Trash2 size={14} />
            Smazat všechna data
          </Button>
        </Card>

        <Card>
          <h3 class="text-base font-semibold mb-2">Backup / Restore</h3>
          <p class="text-xs text-zh-text-muted">
            Backup datové složky do .zip a obnova ze zálohy bude implementováno v týdnu 10
            (společně s migration bridge z Python verze).
          </p>
        </Card>
      </div>

    {:else if activeTab === "updates"}
      <div class="max-w-xl space-y-4">
        <Card>
          <h3 class="text-base font-semibold mb-3">{$t("settings_updates")}</h3>
          <div class="flex items-center justify-between mb-4">
            <div>
              <div class="text-sm">Aktuální verze</div>
              <div class="text-xs text-zh-text-muted font-mono">{appVersion}</div>
            </div>
            <Button variant="secondary" onclick={() => openUrl("https://github.com/ZeddiS/zeddihub-tools-desktop/releases/latest")}>
              <RotateCcw size={14} />
              Otevřít release
            </Button>
          </div>

          <label class="flex items-center justify-between gap-3 py-2 cursor-pointer">
            <div>
              <div class="text-sm">Automatické aktualizace</div>
              <div class="text-xs text-zh-text-muted">Kontrola při spuštění a stažení nových verzí.</div>
            </div>
            <input
              type="checkbox"
              checked={$settings.auto_update_enabled}
              onchange={(e) => settings.patch({ auto_update_enabled: (e.target as HTMLInputElement).checked })}
              class="w-4 h-4 accent-zh-primary"
            />
          </label>

          <label class="flex items-center justify-between gap-3 py-2 cursor-pointer border-t border-zh-divider">
            <div>
              <div class="text-sm">Telemetrie</div>
              <div class="text-xs text-zh-text-muted">Anonymní statistiky používání. Žádná osobní data.</div>
            </div>
            <input
              type="checkbox"
              checked={$settings.telemetry_enabled}
              onchange={(e) => settings.patch({ telemetry_enabled: (e.target as HTMLInputElement).checked })}
              class="w-4 h-4 accent-zh-primary"
            />
          </label>

          <label class="flex items-center justify-between gap-3 py-2 cursor-pointer border-t border-zh-divider">
            <div>
              <div class="text-sm">Po zavření okna</div>
              <div class="text-xs text-zh-text-muted">Minimalizovat do tray, nebo úplně ukončit.</div>
            </div>
            <select
              value={$settings.close_behavior}
              onchange={(e) => settings.patch({ close_behavior: (e.target as HTMLSelectElement).value as any })}
              class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary"
            >
              <option value="minimize">Minimalizovat do tray</option>
              <option value="quit">Ukončit aplikaci</option>
            </select>
          </label>
        </Card>
      </div>
    {/if}
  </div>
</div>

<!-- Confirm modals -->
<Modal bind:open={confirmFactoryReset} title="Opravdu smazat všechna data?" width="max-w-sm">
  <div class="space-y-3">
    <div class="flex items-start gap-3">
      <AlertTriangle size={20} class="text-zh-error shrink-0 mt-0.5" />
      <p class="text-sm text-zh-text-muted">
        Operace je nevratná. Smaže nastavení, šifrované přihlášení, presety, cache i historii.
        Zachová se pouze šifrovací klíč.
      </p>
    </div>
    <div class="flex gap-2 justify-end">
      <Button variant="ghost" onclick={() => (confirmFactoryReset = false)}>{$t("cancel")}</Button>
      <Button variant="primary" onclick={doFactoryReset}>
        <Trash2 size={14} />
        Smazat
      </Button>
    </div>
  </div>
</Modal>

<Modal bind:open={confirmLogout} title="Opravdu se odhlásit?" width="max-w-sm">
  <div class="space-y-3">
    <p class="text-sm text-zh-text-muted">
      Tvůj token bude zneplatněn na serveru a uložené přihlášení smazáno.
      Pro přístup k server nástrojům se budeš muset přihlásit znovu.
    </p>
    <div class="flex gap-2 justify-end">
      <Button variant="ghost" onclick={() => (confirmLogout = false)}>{$t("cancel")}</Button>
      <Button variant="primary" onclick={logout}>
        <LogOutIcon size={14} />
        {$t("auth_logout")}
      </Button>
    </div>
  </div>
</Modal>
