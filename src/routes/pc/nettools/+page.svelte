<script lang="ts">
  import { Network, Search, Plug, Globe, Activity } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import { netToolsApi } from "$api/nettools";
  import { httpApi } from "$api/http";

  type Tab = "dns" | "port" | "ip" | "ping";
  let active = $state<Tab>("dns");

  // ── DNS lookup ──
  let dnsDomain = $state("");
  let dnsType = $state("A");
  let dnsResult = $state<string[]>([]);
  let dnsErr = $state("");
  let dnsBusy = $state(false);

  async function doDns(e?: Event) {
    e?.preventDefault();
    if (!dnsDomain.trim()) return;
    dnsBusy = true; dnsErr = ""; dnsResult = [];
    try { dnsResult = await netToolsApi.dnsLookup(dnsDomain.trim(), dnsType); }
    catch (e: any) { dnsErr = String(e?.message ?? e); }
    dnsBusy = false;
  }

  // ── Port checker ──
  let portHost = $state("");
  let portNum = $state(443);
  let portResult = $state<boolean | null>(null);
  let portLatency = $state<number | null>(null);
  let portBusy = $state(false);

  async function doPort(e?: Event) {
    e?.preventDefault();
    if (!portHost.trim()) return;
    portBusy = true; portResult = null; portLatency = null;
    try {
      const ms = await netToolsApi.tcpPing(portHost.trim(), portNum, 3000);
      portResult = ms !== null;
      portLatency = ms;
    } catch (_) { portResult = false; }
    portBusy = false;
  }

  // ── IP Geolocation (using ip-api.com free tier — http only, but Tauri can fetch) ──
  let ipQuery = $state("");
  let ipResult = $state<any | null>(null);
  let ipErr = $state("");
  let ipBusy = $state(false);

  async function doIp(e?: Event) {
    e?.preventDefault();
    ipBusy = true; ipErr = ""; ipResult = null;
    try {
      const target = ipQuery.trim() || "";
      const url = `http://ip-api.com/json/${encodeURIComponent(target)}?fields=status,message,country,regionName,city,zip,lat,lon,isp,org,as,query`;
      ipResult = await httpApi.fetchJson(url, 60, true);
    } catch (e: any) {
      ipErr = String(e?.message ?? e);
    }
    ipBusy = false;
  }

  // ── Ping (TCP probe) ──
  let pingHost = $state("");
  let pingPort = $state(443);
  let pingHistory = $state<{ ts: string; latency: number | null }[]>([]);
  let pingBusy = $state(false);

  async function doPing(e?: Event) {
    e?.preventDefault();
    if (!pingHost.trim()) return;
    pingBusy = true;
    try {
      const ms = await netToolsApi.tcpPing(pingHost.trim(), pingPort, 3000);
      const ts = new Date().toLocaleTimeString("cs-CZ", { hour12: false });
      pingHistory = [{ ts, latency: ms }, ...pingHistory].slice(0, 30);
    } catch (_) {
      const ts = new Date().toLocaleTimeString("cs-CZ", { hour12: false });
      pingHistory = [{ ts, latency: null }, ...pingHistory].slice(0, 30);
    }
    pingBusy = false;
  }
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Network size={26} class="text-zh-primary" />
    Síťové nástroje
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">DNS / Port / IP geolocation / Ping — vše přes Rust backend.</p>

  <Tabs
    bind:active
    tabs={[
      { id: "dns",  label: "DNS lookup",   icon: Search },
      { id: "port", label: "Port checker", icon: Plug },
      { id: "ip",   label: "IP geo",       icon: Globe },
      { id: "ping", label: "Ping tool",    icon: Activity },
    ]}
  />

  <div class="mt-6">
    {#if active === "dns"}
      <Card class="max-w-2xl">
        <h2 class="font-semibold mb-3 flex items-center gap-2">
          <Search size={16} class="text-zh-primary" /> DNS lookup
        </h2>
        <form onsubmit={doDns} class="space-y-2">
          <input bind:value={dnsDomain} placeholder="example.com"
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
          <select bind:value={dnsType}
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary">
            <option value="A">A (IPv4)</option>
            <option value="AAAA">AAAA (IPv6)</option>
          </select>
          <Button variant="primary" type="submit" disabled={dnsBusy} class="w-full">{dnsBusy ? "…" : "Vyhledat"}</Button>
        </form>
        {#if dnsErr}<div class="mt-3 text-xs text-zh-error">{dnsErr}</div>{/if}
        {#if dnsResult.length > 0}
          <div class="mt-3 text-xs font-mono space-y-1">
            {#each dnsResult as ip}<div class="bg-zh-card-hover px-3 py-1.5 rounded">{ip}</div>{/each}
          </div>
        {/if}
      </Card>

    {:else if active === "port"}
      <Card class="max-w-2xl">
        <h2 class="font-semibold mb-3 flex items-center gap-2">
          <Plug size={16} class="text-zh-primary" /> Port checker
        </h2>
        <form onsubmit={doPort} class="space-y-2">
          <input bind:value={portHost} placeholder="example.com nebo IP"
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
          <input bind:value={portNum} type="number" min="1" max="65535"
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
          <Button variant="primary" type="submit" disabled={portBusy} class="w-full">{portBusy ? "…" : "Otestovat"}</Button>
        </form>
        {#if portResult !== null}
          <div class="mt-3 text-sm font-semibold flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" class:bg-zh-success={portResult} class:bg-zh-error={!portResult}></span>
            {#if portResult}
              <span class="text-zh-success">Otevřený</span>
              {#if portLatency !== null}<span class="text-zh-text-muted text-xs">({portLatency.toFixed(0)} ms)</span>{/if}
            {:else}
              <span class="text-zh-error">Zavřený / nedostupný</span>
            {/if}
          </div>
        {/if}
      </Card>

    {:else if active === "ip"}
      <Card class="max-w-2xl">
        <h2 class="font-semibold mb-3 flex items-center gap-2">
          <Globe size={16} class="text-zh-primary" /> IP Geolocation
        </h2>
        <form onsubmit={doIp} class="space-y-2">
          <input bind:value={ipQuery} placeholder="IP nebo hostname (prázdné = tvoje IP)"
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
          <Button variant="primary" type="submit" disabled={ipBusy} class="w-full">{ipBusy ? "…" : "Vyhledat"}</Button>
        </form>
        {#if ipErr}<div class="mt-3 text-xs text-zh-error">{ipErr}</div>{/if}
        {#if ipResult}
          <div class="mt-3 text-xs space-y-1 font-mono bg-zh-card-hover rounded p-3">
            <div><span class="text-zh-text-muted w-24 inline-block">IP:</span> {ipResult.query}</div>
            {#if ipResult.country}<div><span class="text-zh-text-muted w-24 inline-block">Země:</span> {ipResult.country}</div>{/if}
            {#if ipResult.regionName}<div><span class="text-zh-text-muted w-24 inline-block">Region:</span> {ipResult.regionName}</div>{/if}
            {#if ipResult.city}<div><span class="text-zh-text-muted w-24 inline-block">Město:</span> {ipResult.city} {ipResult.zip ?? ""}</div>{/if}
            {#if ipResult.lat}<div><span class="text-zh-text-muted w-24 inline-block">GPS:</span> {ipResult.lat}, {ipResult.lon}</div>{/if}
            {#if ipResult.isp}<div><span class="text-zh-text-muted w-24 inline-block">ISP:</span> {ipResult.isp}</div>{/if}
            {#if ipResult.org}<div><span class="text-zh-text-muted w-24 inline-block">Org:</span> {ipResult.org}</div>{/if}
            {#if ipResult.as}<div><span class="text-zh-text-muted w-24 inline-block">AS:</span> {ipResult.as}</div>{/if}
          </div>
        {/if}
      </Card>

    {:else if active === "ping"}
      <Card class="max-w-2xl">
        <h2 class="font-semibold mb-3 flex items-center gap-2">
          <Activity size={16} class="text-zh-primary" /> Ping tool
        </h2>
        <form onsubmit={doPing} class="space-y-2">
          <div class="flex gap-2">
            <input bind:value={pingHost} placeholder="example.com"
              class="flex-1 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
            <input bind:value={pingPort} type="number" min="1" max="65535"
              class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
            <Button variant="primary" type="submit" disabled={pingBusy}>{pingBusy ? "…" : "Ping"}</Button>
          </div>
        </form>
        {#if pingHistory.length > 0}
          <div class="mt-3 max-h-48 overflow-auto font-mono text-xs space-y-0.5">
            {#each pingHistory as p}
              <div class="flex justify-between bg-zh-card-hover/50 rounded px-2 py-1">
                <span class="text-zh-text-muted">{p.ts}</span>
                {#if p.latency !== null}
                  <span class:text-zh-success={p.latency < 100} class:text-zh-warning={p.latency >= 100 && p.latency < 200} class:text-zh-error={p.latency >= 200}>
                    {p.latency.toFixed(0)} ms
                  </span>
                {:else}
                  <span class="text-zh-error">timeout</span>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </Card>
    {/if}
  </div>
</div>
