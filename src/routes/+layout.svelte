<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import Header from "$components/layout/Header.svelte";
  import Sidebar from "$components/layout/Sidebar.svelte";
  import LoginDialog from "$components/panels/LoginDialog.svelte";
  import { auth } from "$stores/auth";
  import { theme } from "$stores/theme";
  import { loginDialog } from "$stores/loginDialog";
  import { settings } from "$stores/settings";

  let { children } = $props();

  // Welcome (first-launch) and Splash routes use a clean layout — no shell.
  let showShell = $derived(
    !$page.url.pathname.startsWith("/welcome") &&
    !$page.url.pathname.startsWith("/splash")
  );

  onMount(async () => {
    // Sync theme class with stored preference on first paint
    const html = document.documentElement;
    const initial = $theme;
    html.classList.toggle("dark", initial === "dark");
    html.classList.toggle("light", initial === "light");

    // Try resume saved session in background — silent on failure.
    auth.resume();

    // Load settings (creates default if missing). If first launch is not
    // marked done yet, redirect to /welcome wizard.
    const s = await settings.ensureLoaded();
    if (!s.first_launch_done && !$page.url.pathname.startsWith("/welcome")) {
      goto("/welcome");
    }
  });
</script>

{#if showShell}
  <div class="flex flex-col h-screen overflow-hidden bg-zh-bg">
    <Header />
    <div class="flex-1 flex overflow-hidden">
      <Sidebar />
      <main class="flex-1 overflow-auto bg-zh-content-bg">
        {@render children?.()}
      </main>
    </div>
  </div>
{:else}
  {@render children?.()}
{/if}

<!-- Global login modal — opens via loginDialog.open() from anywhere -->
<LoginDialog
  open={$loginDialog.open}
  onClose={() => loginDialog.close()}
  onSuccess={() => $loginDialog.onSuccess?.()}
/>
