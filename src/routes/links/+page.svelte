<script lang="ts">
  import {
    Globe, BookOpen, MessageCircle, Link as LinkIcon, Github, Youtube, Twitch,
    Server, Search, Plug, Heart, ExternalLink, Upload,
  } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import { t } from "$stores/locale";
  import { netToolsApi } from "$api/nettools";
  import { open as openUrl } from "@tauri-apps/plugin-shell";

  type Tab = "quick" | "dns" | "uploader" | "credits";
  let active = $state<Tab>("quick");

  // ── Quick links data (kategorizované) ───────────────────────────
  const linkSections = [
    {
      titleKey: "links_category_community",
      icon: MessageCircle,
      items: [
        { name: "Discord",       url: "https://dsc.gg/zeddihub",  icon: MessageCircle },
        { name: "Wiki",          url: "https://wiki.zeddihub.eu", icon: BookOpen },
        { name: "YouTube",       url: "https://www.youtube.com/@zeddihub", icon: Youtube },
        { name: "Twitch",        url: "https://twitch.tv/zeddihub", icon: Twitch },
      ],
    },
    {
      titleKey: "links_category_author",
      icon: Github,
      items: [
        { name: "ZeddiS.xyz",    url: "https://zeddis.xyz",        icon: LinkIcon },
        { name: "GitHub: ZeddiS", url: "https://github.com/ZeddiS", icon: Github },
        { name: "ZeddiHub web",   url: "https://zeddihub.eu",      icon: Globe },
      ],
    },
    {
      titleKey: "links_category_files",
      icon: Upload,
      items: [
        { name: "Tools repo",     url: "https://github.com/ZeddiS/zeddihub-tools-desktop", icon: Github },
        { name: "Releases",       url: "https://github.com/ZeddiS/zeddihub-tools-desktop/releases", icon: Github },
        { name: "Web Uploader",   url: "https://zeddihub.eu/tools/uploader/", icon: Upload },
      ],
    },
    {
      titleKey: "links_category_servers",
      icon: Server,
      items: [
        { name: "ZeddiHub CS2",   url: "steam://connect/93.99.7.63:27330", icon: Server },
        { name: "ZeddiHub Rust",  url: "steam://connect/93.99.7.86:28045", icon: Server },
        { name: "ZeddiHub CS:GO", url: "steam://connect/93.99.7.63:27380", icon: Server },
      ],
    },
  ];

  // ── DNS lookup state ────────────────────────────────────────────
  let dnsDomain = $state("");
  let dnsType = $state("A");
  let dnsLoading = $state(false);
  let dnsResult = $state<string[]>([]);
  let dnsError = $state("");

  async function doDnsLookup(e?: Event) {
    e?.preventDefault();
    if (!dnsDomain.trim()) return;
    dnsLoading = true;
    dnsError = "";
    dnsResult = [];
    try {
      dnsResult = await netToolsApi.dnsLookup(dnsDomain.trim(), dnsType);
    } catch (e: any) {
      dnsError = String(e?.message ?? e);
    }
    dnsLoading = false;
  }

  // ── Port check state ─────────────────────────────────────────────
  let portHost = $state("");
  let portNum = $state(80);
  let portLoading = $state(false);
  let portResult = $state<boolean | null>(null);
  let portError = $state("");

  async function doPortCheck(e?: Event) {
    e?.preventDefault();
    if (!portHost.trim()) return;
    portLoading = true;
    portError = "";
    portResult = null;
    try {
      portResult = await netToolsApi.portCheck(portHost.trim(), portNum, 3000);
    } catch (e: any) {
      portError = String(e?.message ?? e);
    }
    portLoading = false;
  }
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1">{$t("links_title")}</h1>
  <p class="text-zh-text-muted text-sm mb-6">{$t("links_subtitle")}</p>

  <Tabs
    bind:active
    tabs={[
      { id: "quick",    label: $t("links_tab_quick"),    icon: LinkIcon },
      { id: "dns",      label: $t("links_tab_dns"),      icon: Search },
      { id: "uploader", label: $t("links_tab_uploader"), icon: Upload },
      { id: "credits",  label: $t("links_tab_credits"),  icon: Heart },
    ]}
  />

  <div class="mt-5">
    {#if active === "quick"}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each linkSections as sec}
          <Card>
            <div class="flex items-center gap-2 mb-3">
              <svelte:component this={sec.icon} size={16} class="text-zh-primary" />
              <h2 class="font-semibold">{$t(sec.titleKey)}</h2>
            </div>
            <div class="space-y-1">
              {#each sec.items as item}
                <button
                  type="button"
                  class="w-full flex items-center gap-3 px-2 py-2 rounded-button text-sm hover:bg-zh-card-hover transition text-left"
                  onclick={() => openUrl(item.url)}
                >
                  <svelte:component this={item.icon} size={14} class="text-zh-text-muted shrink-0" />
                  <span class="flex-1">{item.name}</span>
                  <ExternalLink size={11} class="text-zh-text-muted shrink-0" />
                </button>
              {/each}
            </div>
          </Card>
        {/each}
      </div>

    {:else if active === "dns"}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h2 class="font-semibold mb-3 flex items-center gap-2">
            <Search size={16} class="text-zh-primary" />
            DNS lookup
          </h2>
          <form onsubmit={doDnsLookup} class="space-y-2">
            <label for="dns-domain" class="text-xs text-zh-text-muted block">{$t("dns_domain")}</label>
            <input
              id="dns-domain"
              bind:value={dnsDomain}
              placeholder="example.com"
              class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary"
            />
            <label for="dns-type" class="text-xs text-zh-text-muted block">{$t("dns_record_type")}</label>
            <select
              id="dns-type"
              bind:value={dnsType}
              class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary"
            >
              <option value="A">A (IPv4)</option>
              <option value="AAAA">AAAA (IPv6)</option>
            </select>
            <Button variant="primary" type="submit" disabled={dnsLoading} class="w-full">
              {dnsLoading ? "…" : $t("dns_lookup_btn")}
            </Button>
          </form>

          {#if dnsError}
            <div class="mt-3 text-xs text-zh-error bg-zh-error/10 border border-zh-error/30 rounded px-3 py-2">
              {dnsError}
            </div>
          {/if}
          {#if dnsResult.length > 0}
            <div class="mt-3 text-xs font-mono space-y-1">
              {#each dnsResult as ip}
                <div class="bg-zh-card-hover px-3 py-1.5 rounded">{ip}</div>
              {/each}
            </div>
          {:else if !dnsLoading && !dnsError && dnsDomain && dnsResult.length === 0}
            <div class="mt-3 text-xs text-zh-text-muted">{$t("dns_no_records")}</div>
          {/if}
        </Card>

        <Card>
          <h2 class="font-semibold mb-3 flex items-center gap-2">
            <Plug size={16} class="text-zh-primary" />
            Port checker
          </h2>
          <form onsubmit={doPortCheck} class="space-y-2">
            <label for="port-host" class="text-xs text-zh-text-muted block">{$t("port_host")}</label>
            <input
              id="port-host"
              bind:value={portHost}
              placeholder="example.com nebo IP"
              class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary"
            />
            <label for="port-port" class="text-xs text-zh-text-muted block">{$t("port_port")}</label>
            <input
              id="port-port"
              type="number"
              min="1"
              max="65535"
              bind:value={portNum}
              class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary"
            />
            <Button variant="primary" type="submit" disabled={portLoading} class="w-full">
              {portLoading ? "…" : $t("port_check_btn")}
            </Button>
          </form>

          {#if portError}
            <div class="mt-3 text-xs text-zh-error bg-zh-error/10 border border-zh-error/30 rounded px-3 py-2">
              {portError}
            </div>
          {/if}
          {#if portResult !== null}
            <div class="mt-3 text-sm font-semibold flex items-center gap-2">
              {#if portResult}
                <span class="w-2 h-2 rounded-full bg-zh-success"></span>
                <span class="text-zh-success">{$t("port_open")}</span>
              {:else}
                <span class="w-2 h-2 rounded-full bg-zh-error"></span>
                <span class="text-zh-error">{$t("port_closed")}</span>
              {/if}
            </div>
          {/if}
        </Card>
      </div>

    {:else if active === "uploader"}
      <Card>
        <div class="flex items-start gap-4">
          <Upload size={24} class="text-zh-primary mt-1" />
          <div class="flex-1">
            <h2 class="font-semibold mb-1">Web Uploader</h2>
            <p class="text-sm text-zh-text-muted mb-3">
              Sdílení souborů přes ZeddiHub uploader. 100 MB limit, 4 úrovně viditelnosti, tier quotas.
              Nativní integrace bude přidaná v týdnu 9.
            </p>
            <Button variant="primary" onclick={() => openUrl("https://zeddihub.eu/tools/uploader/")}>
              <ExternalLink size={14} />
              Otevřít uploader v prohlížeči
            </Button>
          </div>
        </div>
      </Card>

    {:else if active === "credits"}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h2 class="font-semibold mb-3 flex items-center gap-2">
            <Heart size={16} class="text-zh-error" />
            Tým
          </h2>
          <ul class="text-sm space-y-1.5 text-zh-text-muted">
            <li><span class="text-zh-text font-semibold">ZeddiS</span> — autor & maintainer</li>
            <li><span class="text-zh-text font-semibold">Claude</span> — AI asistent (Anthropic)</li>
            <li><span class="text-zh-text font-semibold">Komunita</span> — feedback, testing</li>
          </ul>
        </Card>
        <Card>
          <h2 class="font-semibold mb-3 flex items-center gap-2">
            <BookOpen size={16} class="text-zh-primary" />
            Poděkování
          </h2>
          <ul class="text-sm space-y-1.5 text-zh-text-muted">
            <li>Tauri team za parádní framework</li>
            <li>Svelte team za nejlepší DX</li>
            <li>Lucide ikony</li>
            <li>Steam komunita CS2/CS:GO/Rust</li>
            <li>Všichni testeři tools v Discordu</li>
          </ul>
        </Card>
      </div>
    {/if}
  </div>
</div>
