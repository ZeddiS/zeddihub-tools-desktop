<script lang="ts">
  import { onMount } from "svelte";
  import { Search, RotateCw, ExternalLink, Globe } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { t } from "$stores/locale";
  import { httpApi } from "$api/http";
  import { open as openUrl } from "@tauri-apps/plugin-shell";

  // ── Schema (mirrors /tools/data/quick_links.json) ─────────────────
  interface FilterOption { id: string; label: string }
  interface FilterGroup { id: string; label: string; options: FilterOption[] }
  interface AppItem {
    id: string;
    name: string;
    description: string;
    icon?: string;
    url: string;
    screenshot?: string | null;
    open_mode?: "webview" | "external" | "download";
    tags?: string[];
  }
  interface Catalog { filter_groups?: FilterGroup[]; items?: AppItem[] }

  const CATALOG_URL = "https://zeddihub.eu/tools/data/quick_links.json";

  let catalog = $state<Catalog>({ filter_groups: [], items: [] });
  let loading = $state(true);
  let statusKey = $state<"loading" | "live" | "offline">("loading");
  let liveCount = $state(0);

  let searchInput = $state("");
  let searchDebounced = $state("");      // debounced 250ms
  let searchTimer: ReturnType<typeof setTimeout> | null = null;

  let activeFilters = $state<Record<string, string>>({});  // group_id → option_id ("" = All)

  $effect(() => {
    // Debounce searchInput → searchDebounced
    if (searchTimer) clearTimeout(searchTimer);
    const v = searchInput;
    searchTimer = setTimeout(() => { searchDebounced = v; }, 250);
  });

  async function loadCatalog(force = false) {
    loading = true;
    try {
      const data = await httpApi.fetchJson<Catalog>(CATALOG_URL, 6 * 3600, force);
      if (data && typeof data === "object") {
        catalog = data;
        liveCount = (data.items ?? []).length;
        statusKey = "live";
      } else {
        statusKey = "offline";
      }
    } catch {
      statusKey = "offline";
    }
    loading = false;
  }

  onMount(() => loadCatalog(false));

  function setFilter(groupId: string, optionId: string) {
    if (optionId === "") {
      const clone = { ...activeFilters };
      delete clone[groupId];
      activeFilters = clone;
    } else {
      activeFilters = { ...activeFilters, [groupId]: optionId };
    }
  }

  function matches(item: AppItem): boolean {
    // Search match (text + tags)
    const needle = searchDebounced.trim().toLowerCase();
    if (needle) {
      const hay = [
        item.name ?? "",
        item.description ?? "",
        ...(item.tags ?? []),
      ].join(" ").toLowerCase();
      if (!hay.includes(needle)) return false;
    }
    // Filter match (AND across groups)
    for (const [groupId, optionId] of Object.entries(activeFilters)) {
      if (!optionId) continue;
      const tagToMatch = `${groupId}:${optionId}`;
      if (!(item.tags ?? []).includes(tagToMatch)) return false;
    }
    return true;
  }

  let visibleItems = $derived((catalog.items ?? []).filter(matches));

  function openItem(item: AppItem) {
    // PoC: external mode for everything; webview integration v týdnu 9.
    openUrl(item.url);
  }

  function statusText(): string {
    if (statusKey === "loading") return $t("apps_status_cache");
    if (statusKey === "offline") return $t("apps_status_offline");
    return $t("apps_status_live").replace("{count}", String(liveCount));
  }
</script>

<div class="px-8 py-6 max-w-[1400px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">{$t("apps_title")}</h1>
  <p class="text-zh-text-muted text-sm mb-4">{$t("apps_subtitle")}</p>

  <!-- Toolbar: search + refresh -->
  <div class="flex gap-3 mb-3">
    <div class="flex-1 relative">
      <Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-zh-text-muted pointer-events-none" />
      <input
        type="text"
        bind:value={searchInput}
        placeholder={$t("apps_search_placeholder")}
        class="w-full bg-zh-card-hover border border-zh-border rounded-entry pl-9 pr-3 h-9 text-sm focus:outline-none focus:border-zh-primary"
      />
    </div>
    <Button variant="secondary" disabled={loading} onclick={() => loadCatalog(true)}>
      <RotateCw size={14} class={loading ? "animate-spin" : ""} />
      {$t("refresh")}
    </Button>
  </div>

  <!-- Filter row -->
  {#if catalog.filter_groups && catalog.filter_groups.length > 0}
    <div class="flex flex-wrap gap-3 mb-4">
      {#each catalog.filter_groups as group}
        {@const current = activeFilters[group.id] ?? ""}
        <div>
          <div class="text-[10px] uppercase tracking-wider text-zh-text-muted mb-1">{group.label}</div>
          <div class="flex flex-wrap gap-1">
            <button
              type="button"
              class="px-2.5 h-7 rounded text-xs transition"
              class:bg-zh-primary={current === ""}
              class:text-zh-text-dark={current === ""}
              class:bg-zh-card-bg={current !== ""}
              class:hover:bg-zh-card-hover={current !== ""}
              onclick={() => setFilter(group.id, "")}
            >
              {$t("apps_filter_all")}
            </button>
            {#each group.options as opt}
              {@const isActive = current === opt.id}
              <button
                type="button"
                class="px-2.5 h-7 rounded text-xs transition"
                class:bg-zh-primary={isActive}
                class:text-zh-text-dark={isActive}
                class:bg-zh-card-bg={!isActive}
                class:hover:bg-zh-card-hover={!isActive}
                onclick={() => setFilter(group.id, opt.id)}
              >
                {opt.label}
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Status -->
  <div class="text-xs text-zh-text-muted mb-3">
    {statusText()} · {visibleItems.length} / {catalog.items?.length ?? 0}
  </div>

  <!-- Grid -->
  {#if visibleItems.length === 0}
    <Card>
      <div class="text-zh-text-muted text-sm">
        {loading ? $t("news_loading") : $t("apps_no_results")}
      </div>
    </Card>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {#each visibleItems as item (item.id)}
        <Card class="hover:bg-zh-card-hover cursor-pointer transition">
          <button type="button" class="text-left w-full" onclick={() => openItem(item)}>
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 rounded-button bg-zh-primary/10 flex items-center justify-center text-zh-primary shrink-0">
                <Globe size={18} />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="font-semibold truncate">{item.name}</span>
                  <ExternalLink size={11} class="text-zh-text-muted shrink-0" />
                </div>
                <p class="text-xs text-zh-text-muted leading-snug line-clamp-3">
                  {item.description}
                </p>
                {#if item.tags && item.tags.length > 0}
                  <div class="flex flex-wrap gap-1 mt-2">
                    {#each item.tags.slice(0, 4) as tag}
                      <span class="text-[9px] uppercase tracking-wide text-zh-text-muted bg-zh-card-bg px-1.5 py-0.5 rounded">
                        {tag.split(":").pop()}
                      </span>
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          </button>
        </Card>
      {/each}
    </div>
  {/if}
</div>
