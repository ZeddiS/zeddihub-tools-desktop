<script lang="ts">
  import { onMount } from "svelte";
  import { Globe, BookOpen, MessageCircle, Link as LinkIcon, ExternalLink, Star, GitFork, Bug, Download } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { t } from "$stores/locale";
  import { auth, isAuthenticated } from "$stores/auth";
  import { httpApi } from "$api/http";
  import { open as openUrl } from "@tauri-apps/plugin-shell";

  // ── Recommended tools ──────────────────────────────────
  interface RecommendedItem {
    name: string;
    desc: string;
    nav_id?: string;
    color?: string;
  }
  const RECOMMENDED_URL = "https://zeddihub.eu/tools/data/recommended.json";
  const FALLBACK: RecommendedItem[] = [
    { name: "CS2 Crosshair",      desc: "Vygeneruj svůj crosshair",         nav_id: "/cs2/player",  color: "#5b9cf6" },
    { name: "CS2 Server CFG",     desc: "Nastavení herního serveru",        nav_id: "/cs2/server",  color: "#5b9cf6" },
    { name: "CS:GO Crosshair",    desc: "CS:GO crosshair generátor",        nav_id: "/csgo/player", color: "#fbbf24" },
    { name: "Rust Server CFG",    desc: "Konfiguruj Rust server",           nav_id: "/rust/server", color: "#f97316" },
    { name: "Keybind Generator",  desc: "Vizuální keybind editor",          nav_id: "/cs2/keybind", color: "#a78bfa" },
    { name: "Translator",         desc: "Hromadný překlad .json/.lang",     nav_id: "/tools/translator", color: "#4ade80" },
  ];
  let recommended = $state<RecommendedItem[]>(FALLBACK);
  let recStatus = $state("…");

  // ── GitHub stats ───────────────────────────────────────
  const GH_REPO_API = "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop";
  const GH_RELS_API = "https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases?per_page=5";
  let stats = $state({ stars: "?", forks: "?", issues: "?", downloads: "?" });
  let releases = $state<any[]>([]);

  onMount(async () => {
    // Recommended (TTL 30 min)
    try {
      const data = await httpApi.fetchJson<RecommendedItem[]>(RECOMMENDED_URL, 1800);
      if (Array.isArray(data) && data.length > 0) {
        recommended = data.slice(0, 6);
        recStatus = `✓ ${data.length} nástrojů (live)`;
      } else {
        recStatus = "⚠ Zobrazen fallback";
      }
    } catch (e) {
      recStatus = "⚠ Offline — zobrazen fallback";
    }

    // GitHub stats (TTL 1 h)
    try {
      const repo: any = await httpApi.fetchJson(GH_REPO_API, 3600);
      stats.stars = String(repo.stargazers_count ?? 0);
      stats.forks = String(repo.forks_count ?? 0);
      stats.issues = String(repo.open_issues_count ?? 0);
    } catch (e) { /* ignore */ }

    try {
      const rels: any = await httpApi.fetchJson(GH_RELS_API, 3600);
      if (Array.isArray(rels)) {
        let total = 0;
        for (const r of rels) {
          for (const a of r.assets ?? []) total += a.download_count ?? 0;
        }
        stats.downloads = String(total);
        releases = rels.slice(0, 5);
      }
    } catch (e) { /* ignore */ }
  });

  const quickLinks = [
    { label: "ZeddiHub.eu",  url: "https://zeddihub.eu",        icon: Globe },
    { label: "Wiki",         url: "https://wiki.zeddihub.eu",   icon: BookOpen },
    { label: "Discord",      url: "https://dsc.gg/zeddihub",    icon: MessageCircle },
    { label: "ZeddiS.xyz",   url: "https://zeddis.xyz",         icon: LinkIcon },
  ];

  function navTo(path?: string) {
    if (!path) return;
    if (path.startsWith("http")) {
      openUrl(path);
      return;
    }
    // Internal nav
    import("$app/navigation").then((m) => m.goto(path));
  }
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <!-- Title -->
  <h1 class="text-3xl font-bold mb-1">{$t("welcome")}</h1>
  <p class="text-zh-text-muted text-sm mb-6">{$t("welcome_desc")}</p>

  <!-- Quick links strip -->
  <div class="flex gap-2 mb-6">
    {#each quickLinks as link}
      <Button variant="ghost" onclick={() => openUrl(link.url)} class="!px-3 !h-8 text-xs">
        <svelte:component this={link.icon} size={14} />
        {link.label}
      </Button>
    {/each}
  </div>

  <!-- Login card + GitHub stats grid -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
    <Card class="lg:col-span-1">
      {#if $isAuthenticated}
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-full bg-zh-success/20 flex items-center justify-center text-zh-success font-bold">
            {$auth.user?.username?.[0]?.toUpperCase()}
          </div>
          <div>
            <div class="text-sm font-semibold">{$auth.user?.username}</div>
            <div class="text-xs text-zh-text-muted">{$auth.user?.role}</div>
          </div>
        </div>
        <Button variant="ghost" onclick={() => auth.logout()} class="!h-8 text-xs w-full">
          {$t("auth_logout")}
        </Button>
      {:else}
        <div class="text-sm font-semibold mb-1">{$t("auth_not_logged_in")}</div>
        <p class="text-xs text-zh-text-muted mb-3">
          Přihlaš se pro přístup k server nástrojům a admin sekcím.
        </p>
        <Button variant="primary" onclick={() => navTo("/settings")} class="!h-8 text-xs w-full">
          {$t("auth_login")}
        </Button>
      {/if}
    </Card>

    <Card class="lg:col-span-2">
      <div class="text-sm font-semibold mb-3">{$t("github_section")}</div>
      <div class="grid grid-cols-4 gap-3">
        {#each [
          { icon: Bug,      value: stats.issues,    label: $t("github_issues"),    color: "#f87171" },
          { icon: Star,     value: stats.stars,     label: $t("github_stars"),     color: "#fbbf24" },
          { icon: GitFork,  value: stats.forks,     label: $t("github_forks"),     color: "#5b9cf6" },
          { icon: Download, value: stats.downloads, label: $t("github_downloads"), color: "#4ade80" },
        ] as s}
          <div class="bg-zh-card-bg/40 rounded-button p-3">
            <div class="flex items-center gap-2 mb-1">
              <svelte:component this={s.icon} size={14} style="color: {s.color}" />
              <span class="text-xl font-bold" style:color={s.color}>{s.value}</span>
            </div>
            <div class="text-[10px] text-zh-text-muted uppercase tracking-wide">{s.label}</div>
          </div>
        {/each}
      </div>
    </Card>
  </div>

  <!-- Recommended grid -->
  <div class="flex items-center justify-between mb-3">
    <h2 class="text-lg font-semibold">{$t("recommended_tools")}</h2>
    <span class="text-xs text-zh-text-muted">{recStatus}</span>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
    {#each recommended as item}
      <button
        type="button"
        class="text-left"
        on:click={() => navTo(item.nav_id)}
      >
        <Card strip={item.color ?? "#f0a500"} class="hover:bg-zh-card-hover cursor-pointer transition">
          <div class="font-semibold mb-1">{item.name}</div>
          <p class="text-xs text-zh-text-muted leading-relaxed">{item.desc}</p>
        </Card>
      </button>
    {/each}
  </div>

  <!-- News (GitHub Releases) -->
  {#if releases.length > 0}
    <h2 class="text-lg font-semibold mb-3">{$t("news_section")}</h2>
    <div class="space-y-3">
      {#each releases as rel}
        <Card>
          <div class="flex items-center gap-2 mb-2">
            <span class="font-semibold">{rel.name || rel.tag_name}</span>
            <span class="text-xs text-zh-text-muted">({rel.tag_name})</span>
            <div class="flex-1"></div>
            <span class="text-xs text-zh-text-muted">{(rel.published_at || "").slice(0, 10)}</span>
          </div>
          {#if rel.body}
            <p class="text-xs text-zh-text-muted whitespace-pre-line line-clamp-3">{rel.body}</p>
          {/if}
          {#if rel.html_url}
            <Button variant="ghost" onclick={() => openUrl(rel.html_url)} class="!h-7 text-[11px] mt-2">
              <ExternalLink size={12} />
              {$t("open_github")}
            </Button>
          {/if}
        </Card>
      {/each}
    </div>
  {/if}
</div>

