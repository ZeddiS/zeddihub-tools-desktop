<script lang="ts">
  import { ExternalLink, Tag, Calendar, Download } from "lucide-svelte";
  import { onMount } from "svelte";
  import { marked } from "marked";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { t } from "$stores/locale";
  import { httpApi } from "$api/http";
  import { open as openUrl } from "@tauri-apps/plugin-shell";

  interface ReleaseAsset {
    name: string;
    size: number;
    download_count: number;
    browser_download_url: string;
  }
  interface Release {
    tag_name: string;
    name: string | null;
    body: string | null;
    published_at: string;
    html_url: string;
    prerelease: boolean;
    assets: ReleaseAsset[];
  }

  const PER_PAGE = 10;
  const RELEASES_API = (page: number) =>
    `https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases?per_page=${PER_PAGE}&page=${page}`;

  let releases = $state<Release[]>([]);
  let page = $state(1);
  let loading = $state(true);
  let loadingMore = $state(false);
  let hasMore = $state(true);
  let showPrereleases = $state(false);
  let errorMsg = $state("");

  async function loadPage(p: number) {
    try {
      const data = await httpApi.fetchJson<Release[]>(RELEASES_API(p), 1800);
      if (Array.isArray(data)) {
        if (p === 1) releases = data;
        else releases = [...releases, ...data];
        hasMore = data.length === PER_PAGE;
      } else {
        errorMsg = "Načtení selhalo.";
      }
    } catch (e: any) {
      errorMsg = String(e?.message ?? e);
    }
  }

  onMount(async () => {
    loading = true;
    await loadPage(1);
    loading = false;
  });

  async function loadMore() {
    if (loadingMore || !hasMore) return;
    loadingMore = true;
    page += 1;
    await loadPage(page);
    loadingMore = false;
  }

  function fmtBytes(n: number): string {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    return (n / 1024 / 1024).toFixed(1) + " MB";
  }

  function renderMd(body: string | null): string {
    if (!body) return "";
    try {
      return marked.parse(body, { async: false }) as string;
    } catch {
      return body;
    }
  }

  let visibleReleases = $derived(
    showPrereleases ? releases : releases.filter((r) => !r.prerelease)
  );
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <div class="flex items-baseline justify-between mb-1">
    <h1 class="text-3xl font-bold">{$t("news_title_panel")}</h1>
    <label class="flex items-center gap-2 text-xs text-zh-text-muted cursor-pointer">
      <input type="checkbox" bind:checked={showPrereleases} class="w-3.5 h-3.5 accent-zh-primary" />
      {$t("news_show_prereleases")}
    </label>
  </div>
  <p class="text-zh-text-muted text-sm mb-6">GitHub Releases pro zeddihub-tools-desktop.</p>

  {#if loading}
    <Card>
      <div class="text-zh-text-muted text-sm">{$t("news_loading")}</div>
    </Card>
  {:else if errorMsg}
    <Card>
      <div class="text-zh-error text-sm">{errorMsg}</div>
    </Card>
  {:else if visibleReleases.length === 0}
    <Card>
      <div class="text-zh-text-muted text-sm">{$t("news_no_items")}</div>
    </Card>
  {:else}
    <div class="space-y-3">
      {#each visibleReleases as rel (rel.tag_name)}
        <Card>
          <div class="flex items-baseline gap-3 mb-2">
            <span class="font-bold text-base">{rel.name || rel.tag_name}</span>
            <span class="text-xs text-zh-text-muted flex items-center gap-1">
              <Tag size={10} />
              {rel.tag_name}
            </span>
            {#if rel.prerelease}
              <span class="text-[10px] bg-zh-warning/20 text-zh-warning px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide">pre</span>
            {/if}
            <div class="flex-1"></div>
            <span class="text-xs text-zh-text-muted flex items-center gap-1">
              <Calendar size={10} />
              {rel.published_at?.slice(0, 10)}
            </span>
          </div>

          {#if rel.body}
            <div class="prose prose-sm prose-invert max-w-none text-zh-text-muted text-sm leading-relaxed mb-3
                        [&_h1]:text-base [&_h1]:font-bold [&_h1]:text-zh-text [&_h1]:mt-3 [&_h1]:mb-1
                        [&_h2]:text-sm [&_h2]:font-bold [&_h2]:text-zh-text [&_h2]:mt-3 [&_h2]:mb-1
                        [&_h3]:text-xs [&_h3]:font-bold [&_h3]:text-zh-text [&_h3]:mt-2 [&_h3]:mb-1
                        [&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:my-1 [&_li]:my-0.5
                        [&_code]:bg-zh-card-hover [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-[11px] [&_code]:font-mono
                        [&_a]:text-zh-primary [&_a]:no-underline hover:[&_a]:underline">
              {@html renderMd(rel.body)}
            </div>
          {/if}

          {#if rel.assets.length > 0}
            <div class="border-t border-zh-divider pt-2 mb-2">
              <div class="text-[10px] uppercase tracking-wide text-zh-text-muted mb-1.5">{$t("news_assets")}</div>
              <div class="flex flex-wrap gap-1.5">
                {#each rel.assets as asset}
                  <button
                    type="button"
                    class="flex items-center gap-1.5 text-xs bg-zh-card-hover hover:bg-zh-border px-2 py-1 rounded transition"
                    onclick={() => openUrl(asset.browser_download_url)}
                  >
                    <Download size={11} />
                    <span class="font-mono">{asset.name}</span>
                    <span class="text-zh-text-muted">{fmtBytes(asset.size)}</span>
                    {#if asset.download_count > 0}
                      <span class="text-zh-text-muted">· {asset.download_count}×</span>
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/if}

          <Button variant="ghost" onclick={() => openUrl(rel.html_url)} class="!h-7 text-[11px] !px-2">
            <ExternalLink size={12} />
            {$t("open_in_github")}
          </Button>
        </Card>
      {/each}
    </div>

    {#if hasMore}
      <div class="flex justify-center mt-4">
        <Button variant="secondary" disabled={loadingMore} onclick={loadMore}>
          {loadingMore ? "…" : $t("news_load_more")}
        </Button>
      </div>
    {/if}
  {/if}
</div>
