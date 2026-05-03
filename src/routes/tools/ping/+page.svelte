<script lang="ts">
  import { Activity, Play, Trash2, Send } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { netToolsApi } from "$api/nettools";
  import { PING_SERVERS } from "$lib/data/gameTools";

  type Status = "waiting" | "measuring" | "ok" | "timeout";
  interface Row {
    name: string;
    host: string;
    port: number;
    latency: number | null;
    status: Status;
  }

  let rows = $state<Row[]>(
    PING_SERVERS.map((s) => ({ ...s, latency: null, status: "waiting" }))
  );

  let customHost = $state("");
  let customPort = $state(443);
  let customRow = $state<Row | null>(null);
  let busy = $state(false);

  function ratingFor(ms: number | null): { color: string; label: string } {
    if (ms === null) return { color: "text-zh-error", label: "❌ offline" };
    if (ms < 50)     return { color: "text-zh-success", label: "✅ excellent" };
    if (ms < 100)    return { color: "text-[#4ade80]", label: "✅ good" };
    if (ms < 200)    return { color: "text-zh-warning", label: "⚠ fair" };
    return { color: "text-zh-error", label: "🔴 high" };
  }

  async function runOne(idx: number) {
    rows[idx].status = "measuring";
    rows[idx].latency = null;
    try {
      const ms = await netToolsApi.tcpPing(rows[idx].host, rows[idx].port, 3000);
      rows[idx].latency = ms;
      rows[idx].status = ms === null ? "timeout" : "ok";
    } catch (_) {
      rows[idx].status = "timeout";
    }
  }

  async function runAll() {
    if (busy) return;
    busy = true;
    await Promise.all(rows.map((_, i) => runOne(i)));
    busy = false;
  }

  function clearAll() {
    rows = rows.map((r) => ({ ...r, latency: null, status: "waiting" }));
  }

  async function pingCustom() {
    const host = customHost.trim();
    if (!host) return;
    customRow = { name: "Vlastní", host, port: customPort, latency: null, status: "measuring" };
    try {
      const ms = await netToolsApi.tcpPing(host, customPort, 3000);
      customRow = { ...customRow, latency: ms, status: ms === null ? "timeout" : "ok" };
    } catch (e: any) {
      customRow = { ...customRow, latency: null, status: "timeout" };
    }
  }
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Activity size={26} class="text-zh-primary" />
    Ping Tester
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">
    Změří latenci k herním serverům a síťovým endpointům přes TCP/socket spojení.
  </p>

  <div class="flex gap-2 mb-3">
    <Button variant="primary" onclick={runAll} disabled={busy}>
      <Play size={14} />
      {busy ? "Měřím…" : "Testovat vše"}
    </Button>
    <Button variant="secondary" onclick={clearAll}>
      <Trash2 size={14} />
      Vymazat výsledky
    </Button>
  </div>

  <Card padding={3} class="mb-3">
    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-[10px] uppercase tracking-wider text-zh-text-muted border-b border-zh-divider">
          <th class="py-2 pl-2 font-semibold">Server</th>
          <th class="py-2 font-semibold">Host</th>
          <th class="py-2 font-semibold">Port</th>
          <th class="py-2 font-semibold">Latence</th>
          <th class="py-2 pr-2 font-semibold">Status</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as r, i (r.name)}
          {@const rating = ratingFor(r.latency)}
          <tr class="border-b border-zh-divider/40 hover:bg-zh-card-hover/40 transition">
            <td class="py-1.5 pl-2 text-zh-text">{r.name}</td>
            <td class="py-1.5 text-xs font-mono text-zh-text-muted truncate max-w-xs">{r.host}</td>
            <td class="py-1.5 text-xs font-mono text-zh-text-muted">{r.port}</td>
            <td class="py-1.5 font-bold font-mono text-sm" class:text-zh-text-muted={r.status === "waiting" || r.status === "measuring"} class:text-zh-success={r.status === "ok" && (r.latency ?? 999) < 100} class:text-zh-warning={r.status === "ok" && (r.latency ?? 999) >= 100 && (r.latency ?? 999) < 200} class:text-zh-error={r.status === "timeout" || (r.status === "ok" && (r.latency ?? 0) >= 200)}>
              {#if r.status === "waiting"}—
              {:else if r.status === "measuring"}…
              {:else if r.status === "timeout"}timeout
              {:else}{r.latency!.toFixed(0)} ms
              {/if}
            </td>
            <td class="py-1.5 pr-2 text-xs {rating.color}">
              {#if r.status === "waiting"}<span class="text-zh-text-muted">čeká</span>
              {:else if r.status === "measuring"}<span class="text-zh-text-muted">měřím</span>
              {:else}{rating.label}
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Card>

  <!-- Custom ping -->
  <Card>
    <div class="text-sm font-bold text-zh-primary mb-3">Vlastní server</div>
    <div class="flex gap-2 items-end">
      <label class="flex flex-col gap-1 flex-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Host</span>
        <input bind:value={customHost} placeholder="hostname nebo IP"
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Port</span>
        <input bind:value={customPort} type="number" min="1" max="65535"
          class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <Button variant="primary" onclick={pingCustom}>
        <Send size={14} />
        Ping
      </Button>
    </div>
    {#if customRow}
      {@const rating = ratingFor(customRow.latency)}
      <div class="mt-3 text-sm">
        <span class="font-mono text-zh-text-muted">{customRow.host}:{customRow.port}</span>
        →
        {#if customRow.status === "measuring"}<span class="text-zh-text-muted">měřím…</span>
        {:else if customRow.status === "timeout"}<span class="text-zh-error">timeout</span>
        {:else}<span class="font-bold font-mono">{customRow.latency!.toFixed(0)} ms</span> <span class={rating.color}>{rating.label}</span>
        {/if}
      </div>
    {/if}
  </Card>
</div>
