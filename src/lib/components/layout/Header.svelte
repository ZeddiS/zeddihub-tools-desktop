<script lang="ts">
  import { Moon, Sun, User, LogOut } from "lucide-svelte";
  import { theme, toggleTheme } from "$stores/theme";
  import { lang, t, toggleLang } from "$stores/locale";
  import { auth, isAuthenticated } from "$stores/auth";
  import { loginDialog } from "$stores/loginDialog";
  import { goto } from "$app/navigation";

  function onAuthClick() {
    if ($isAuthenticated) {
      goto("/settings");
    } else {
      loginDialog.open();
    }
  }
</script>

<header class="zh-header h-14 bg-zh-header-bg border-b border-zh-border flex items-center px-5 gap-4 select-none">
  <div class="flex items-center gap-3">
    <div class="text-zh-primary font-bold text-lg">ZeddiHub Tools</div>
    <span class="text-zh-text-muted text-xs">v2.0.0 alpha</span>
  </div>

  <div class="flex-1"></div>

  <!-- Auth pill -->
  <button
    class="px-3 h-9 rounded-button text-xs flex items-center gap-2 hover:bg-zh-card-hover transition"
    class:text-zh-success={$isAuthenticated}
    class:text-zh-text-muted={!$isAuthenticated}
    onclick={onAuthClick}
  >
    {#if $isAuthenticated}
      <User size={14} />
      {$auth.user?.username}
    {:else}
      <LogOut size={14} />
      {$t("auth_not_logged_in")}
    {/if}
  </button>

  <!-- Lang toggle -->
  <button
    class="px-3 h-9 rounded-button text-xs hover:bg-zh-card-hover transition"
    onclick={toggleLang}
    title="Change language"
  >
    {$lang === "cs" ? "🇨🇿 CS" : "🇬🇧 EN"}
  </button>

  <!-- Theme toggle -->
  <button
    class="w-9 h-9 rounded-button hover:bg-zh-card-hover transition flex items-center justify-center"
    onclick={toggleTheme}
    title="Toggle theme"
  >
    {#if $theme === "dark"}
      <Moon size={16} />
    {:else}
      <Sun size={16} />
    {/if}
  </button>
</header>
