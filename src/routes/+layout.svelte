<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import Header from "$components/layout/Header.svelte";
  import Sidebar from "$components/layout/Sidebar.svelte";
  import { auth } from "$stores/auth";
  import { theme } from "$stores/theme";

  let { children } = $props();

  onMount(() => {
    // Sync theme class with stored preference on first paint
    const html = document.documentElement;
    const initial = $theme;
    html.classList.toggle("dark", initial === "dark");
    html.classList.toggle("light", initial === "light");

    // Try resume saved session in background — silent on failure.
    auth.resume();
  });
</script>

<div class="flex flex-col h-screen overflow-hidden bg-zh-bg">
  <Header />
  <div class="flex-1 flex overflow-hidden">
    <Sidebar />
    <main class="flex-1 overflow-auto bg-zh-content-bg">
      {@render children?.()}
    </main>
  </div>
</div>
