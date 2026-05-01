<script lang="ts">
  import { Github, MessageCircle, Globe, Mail, RotateCcw, FileText, Bug, ExternalLink } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { t } from "$stores/locale";
  import { open as openUrl } from "@tauri-apps/plugin-shell";
  import { getVersion } from "@tauri-apps/api/app";
  import { onMount } from "svelte";

  // Pulled from Tauri at runtime so we don't drift from tauri.conf.json
  let version = $state("…");
  onMount(async () => {
    try {
      version = await getVersion();
    } catch {
      version = "2.0.0-1";
    }
  });

  const repoUrl = "https://github.com/ZeddiS/zeddihub-tools-desktop";
  const issuesUrl = `${repoUrl}/issues/new`;
  const releasesUrl = `${repoUrl}/releases`;
  const changelogUrl = `${repoUrl}/blob/master/CHANGELOG.md`;

  const links = [
    { icon: Github,         label: "GitHub",  url: repoUrl },
    { icon: Globe,          label: "Web",     url: "https://zeddihub.eu" },
    { icon: MessageCircle,  label: "Discord", url: "https://dsc.gg/zeddihub" },
    { icon: Mail,           label: "Email",   url: "mailto:zeddi@zeddihub.eu" },
  ];

  const libraries: { name: string; license: string; url: string }[] = [
    { name: "Tauri 2",          license: "Apache-2.0 / MIT", url: "https://tauri.app" },
    { name: "SvelteKit 2",      license: "MIT",              url: "https://kit.svelte.dev" },
    { name: "Svelte 5",         license: "MIT",              url: "https://svelte.dev" },
    { name: "Tailwind CSS",     license: "MIT",              url: "https://tailwindcss.com" },
    { name: "lucide-svelte",    license: "ISC",              url: "https://lucide.dev" },
    { name: "tokio",            license: "MIT",              url: "https://tokio.rs" },
    { name: "reqwest",          license: "MIT / Apache-2.0", url: "https://docs.rs/reqwest" },
    { name: "chacha20poly1305", license: "MIT / Apache-2.0", url: "https://docs.rs/chacha20poly1305" },
    { name: "sysinfo",          license: "MIT",              url: "https://docs.rs/sysinfo" },
    { name: "serde",            license: "MIT / Apache-2.0", url: "https://serde.rs" },
  ];
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">{$t("about_title")}</h1>
  <p class="text-zh-text-muted text-sm mb-6">{$t("about_subtitle")}</p>

  <!-- Hero card -->
  <Card class="mb-4">
    <div class="flex items-start gap-6">
      <div class="w-20 h-20 rounded-card bg-zh-primary/15 flex items-center justify-center text-zh-primary font-bold text-3xl shrink-0">
        Z
      </div>
      <div class="flex-1">
        <div class="text-xl font-bold mb-1">ZeddiHub Tools</div>
        <div class="text-sm text-zh-text-muted mb-3">{$t("about_subtitle")}</div>
        <div class="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
          <div><span class="text-zh-text-muted">{$t("about_version")}:</span> <span class="font-mono">{version}</span></div>
          <div><span class="text-zh-text-muted">{$t("about_author")}:</span> ZeddiHub (ZeddiS)</div>
          <div><span class="text-zh-text-muted">{$t("about_license")}:</span> Proprietární</div>
          <div><span class="text-zh-text-muted">{$t("about_repository")}:</span>
            <button class="text-zh-primary hover:underline" onclick={() => openUrl(repoUrl)}>ZeddiS/zeddihub-tools-desktop</button>
          </div>
        </div>
      </div>
    </div>
  </Card>

  <!-- Quick action buttons -->
  <div class="flex gap-2 flex-wrap mb-6">
    <Button variant="primary" onclick={() => openUrl(releasesUrl)}>
      <RotateCcw size={14} />
      {$t("about_check_updates")}
    </Button>
    <Button variant="secondary" onclick={() => openUrl(changelogUrl)}>
      <FileText size={14} />
      {$t("about_changelog")}
    </Button>
    <Button variant="secondary" onclick={() => openUrl(issuesUrl)}>
      <Bug size={14} />
      {$t("about_report_bug")}
    </Button>
  </div>

  <!-- External links grid -->
  <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
    {#each links as l}
      <Card class="hover:bg-zh-card-hover cursor-pointer transition">
        <button type="button" class="w-full text-left" onclick={() => openUrl(l.url)}>
          <div class="flex items-center gap-3">
            <svelte:component this={l.icon} size={20} class="text-zh-primary" />
            <div class="flex-1 min-w-0">
              <div class="font-semibold text-sm">{l.label}</div>
              <div class="text-[10px] text-zh-text-muted truncate">{l.url}</div>
            </div>
            <ExternalLink size={12} class="text-zh-text-muted shrink-0" />
          </div>
        </button>
      </Card>
    {/each}
  </div>

  <!-- Libraries section -->
  <Card>
    <h2 class="text-base font-semibold mb-3">{$t("about_libs_section")}</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
      {#each libraries as lib}
        <button
          type="button"
          class="flex items-center justify-between text-left text-xs hover:bg-zh-card-hover px-2 py-1.5 -mx-2 rounded transition"
          onclick={() => openUrl(lib.url)}
        >
          <span class="font-mono">{lib.name}</span>
          <span class="text-zh-text-muted">{lib.license}</span>
        </button>
      {/each}
    </div>
  </Card>
</div>
