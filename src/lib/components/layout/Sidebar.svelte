<script lang="ts">
  import {
    Home,
    Settings,
    Info,
    Newspaper,
    Link as LinkIcon,
    LayoutGrid,
    Crosshair,
    Gamepad2,
    Puzzle,
    Languages,
    Gauge,
    Activity,
    Laptop,
    Network,
    Wrench,
    Eye,
    DownloadCloud,
    ChevronDown,
    ChevronRight,
  } from "lucide-svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { t } from "$stores/locale";
  import { isAuthenticated } from "$stores/auth";
  import { loginDialog } from "$stores/loginDialog";

  type NavItem = { id: string; href: string; icon: any; labelKey: string; requiresAuth?: boolean };
  type NavSection = { id: string; labelKey: string; icon: any; items: NavItem[] };

  /** Top-level shortcuts (no children) */
  const topItems: NavItem[] = [
    { id: "home",     href: "/",          icon: Home,       labelKey: "nav_home" },
    { id: "apps",     href: "/apps",      icon: LayoutGrid, labelKey: "nav_apps" },
  ];

  /** Collapsible sections — currently 5 (matches Python version) */
  const sections: NavSection[] = [
    {
      id: "pc",
      labelKey: "nav_section_pc",
      icon: Laptop,
      items: [
        { id: "pc/sysinfo",   href: "/pc/sysinfo",   icon: Laptop,  labelKey: "nav_pc_sysinfo" },
        { id: "pc/nettools",  href: "/pc/nettools",  icon: Network, labelKey: "nav_pc_nettools" },
        { id: "pc/utility",   href: "/pc/utility",   icon: Wrench,  labelKey: "nav_pc_utility" },
        { id: "pc/gameopt",   href: "/pc/gameopt",   icon: Gamepad2, labelKey: "nav_pc_gameopt" },
        { id: "pc/advanced",  href: "/pc/advanced",  icon: Wrench,  labelKey: "nav_pc_advanced" },
      ],
    },
    {
      id: "cs2",
      labelKey: "nav_section_cs2",
      icon: Crosshair,
      items: [
        { id: "cs2/player",  href: "/cs2/player",  icon: Crosshair, labelKey: "nav_player_tools" },
        { id: "cs2/server",  href: "/cs2/server",  icon: Wrench,    labelKey: "nav_server_tools", requiresAuth: true },
        { id: "cs2/keybind", href: "/cs2/keybind", icon: Gamepad2,  labelKey: "nav_keybind" },
      ],
    },
    {
      id: "csgo",
      labelKey: "nav_section_csgo",
      icon: Gamepad2,
      items: [
        { id: "csgo/player",  href: "/csgo/player",  icon: Crosshair, labelKey: "nav_player_tools" },
        { id: "csgo/server",  href: "/csgo/server",  icon: Wrench,    labelKey: "nav_server_tools", requiresAuth: true },
        { id: "csgo/keybind", href: "/csgo/keybind", icon: Gamepad2,  labelKey: "nav_keybind" },
      ],
    },
    {
      id: "rust",
      labelKey: "nav_section_rust",
      icon: Puzzle,
      items: [
        { id: "rust/player",  href: "/rust/player",  icon: Crosshair, labelKey: "nav_player_tools" },
        { id: "rust/server",  href: "/rust/server",  icon: Wrench,    labelKey: "nav_server_tools", requiresAuth: true },
        { id: "rust/keybind", href: "/rust/keybind", icon: Gamepad2,  labelKey: "nav_keybind" },
      ],
    },
    {
      id: "tools",
      labelKey: "nav_section_game_tools",
      icon: Gamepad2,
      items: [
        { id: "tools/translator",   href: "/tools/translator",   icon: Languages, labelKey: "nav_translator" },
        { id: "tools/sensitivity",  href: "/tools/sensitivity",  icon: Crosshair, labelKey: "nav_sensitivity" },
        { id: "tools/edpi",         href: "/tools/edpi",         icon: Gauge,     labelKey: "nav_edpi" },
        { id: "tools/ping",         href: "/tools/ping",         icon: Activity,  labelKey: "nav_ping_tester" },
      ],
    },
  ];

  /** Bottom items (always visible) */
  const bottomItems: NavItem[] = [
    { id: "watchdog", href: "/watchdog", icon: Eye,       labelKey: "nav_watchdog" },
    { id: "news",     href: "/news",     icon: Newspaper, labelKey: "nav_news" },
    { id: "links",    href: "/links",    icon: LinkIcon,  labelKey: "nav_links" },
    { id: "tools-download", href: "/tools-download", icon: DownloadCloud, labelKey: "nav_tools_download" },
    { id: "settings", href: "/settings", icon: Settings,  labelKey: "nav_settings" },
    { id: "about",    href: "/about",    icon: Info,      labelKey: "nav_about" },
  ];

  /** Collapsed state per section. Default: all collapsed except current. */
  let collapsed = $state<Record<string, boolean>>({
    pc: true, cs2: false, csgo: true, rust: true, tools: true,
  });

  function isActive(href: string): boolean {
    return $page.url.pathname === href;
  }

  function navigate(href: string, requiresAuth = false) {
    if (requiresAuth && !$isAuthenticated) {
      // Open login modal; on success, continue to the originally clicked panel.
      loginDialog.open(() => goto(href));
      return;
    }
    goto(href);
  }
</script>

<aside class="zh-sidebar w-60 bg-zh-sidebar-bg border-r border-zh-border flex flex-col gap-0.5 p-3 overflow-y-auto select-none">
  <!-- Top items -->
  {#each topItems as item}
    <button
      class="flex items-center gap-3 px-3 h-9 rounded-button text-sm transition text-left"
      class:bg-zh-primary={isActive(item.href)}
      class:text-black={isActive(item.href)}
      class:font-semibold={isActive(item.href)}
      class:hover:bg-zh-card-hover={!isActive(item.href)}
      onclick={() => navigate(item.href)}
    >
      <svelte:component this={item.icon} size={16} />
      {$t(item.labelKey)}
    </button>
  {/each}

  <div class="h-px bg-zh-border my-2"></div>

  <!-- Collapsible sections -->
  {#each sections as sec}
    <button
      class="flex items-center gap-2 px-3 h-7 rounded-button text-[10px] uppercase tracking-wider text-zh-text-muted hover:bg-zh-card-hover/50 transition mt-3"
      onclick={() => (collapsed[sec.id] = !collapsed[sec.id])}
    >
      <svelte:component this={sec.icon} size={11} />
      <span class="flex-1 text-left">{$t(sec.labelKey)}</span>
      {#if collapsed[sec.id]}
        <ChevronRight size={11} />
      {:else}
        <ChevronDown size={11} />
      {/if}
    </button>
    {#if !collapsed[sec.id]}
      {#each sec.items as item}
        {#if !item.requiresAuth || $isAuthenticated}
          <button
            class="flex items-center gap-3 px-3 h-8 rounded-button text-[13px] transition text-left ml-2"
            class:bg-zh-primary={isActive(item.href)}
            class:text-black={isActive(item.href)}
            class:font-semibold={isActive(item.href)}
            class:hover:bg-zh-card-hover={!isActive(item.href)}
            onclick={() => navigate(item.href, item.requiresAuth)}
          >
            <svelte:component this={item.icon} size={14} />
            <span class="flex-1">{$t(item.labelKey)}</span>
            {#if item.requiresAuth}
              <span class="text-[9px] bg-zh-success text-black rounded px-1.5 py-0.5 font-semibold">PREMIUM</span>
            {/if}
          </button>
        {/if}
      {/each}
    {/if}
  {/each}

  <div class="flex-1"></div>
  <div class="h-px bg-zh-border my-2"></div>

  <!-- Bottom items -->
  {#each bottomItems as item}
    {#if !item.requiresAuth || $isAuthenticated}
      <button
        class="flex items-center gap-3 px-3 h-9 rounded-button text-sm transition text-left"
        class:bg-zh-primary={isActive(item.href)}
        class:text-black={isActive(item.href)}
        class:font-semibold={isActive(item.href)}
        class:hover:bg-zh-card-hover={!isActive(item.href)}
        onclick={() => navigate(item.href, item.requiresAuth)}
      >
        <svelte:component this={item.icon} size={15} />
        {$t(item.labelKey)}
      </button>
    {/if}
  {/each}
</aside>
