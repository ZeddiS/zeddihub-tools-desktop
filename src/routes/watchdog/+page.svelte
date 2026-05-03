<script lang="ts">
  import { Eye, Play, Square, Plus, Trash2, RefreshCw, Bell } from "lucide-svelte";
  import { onMount, onDestroy } from "svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { a2sApi, type ServerInfo } from "$api/a2s";
  import { httpApi } from "$api/http";

  interface Server {
    name: string;
    ip: string;
    port: number;
    game?: string;
    online: boolean;
    ping_ms: number;
    map?: string | null;
    players?: number | null;
    max_players?: number | null;
    consecutive_failures: number;
  }

  // Default servers — same list as legacy/gui/panels/home.py + watchdog.py
  const DEFAULTS: Omit<Server, "online" | "ping_ms" | "consecutive_failures">[] = [
    { name: "ZeddiHub Rust",     ip: "93.99.7.86", port: 28045, game: "rust" },
    { name: "ZeddiHub CS2",      ip: "93.99.7.63", port: 27330, game: "cs2"  },
    { name: "ZeddiHub CS:GO #1", ip: "93.99.7.63", port: 27380, game: "csgo" },
    { name: "ZeddiHub CS:GO #2", ip: "93.99.7.86", port: 27355, game: "csgo" },
    { name: "ZeddiHub CS:GO #3", ip: "93.99.7.86", port: 27415, game: "csgo" },
  ];

  let servers = $state<Server[]>(
    DEFAULTS.map((s) => ({ ...s, online: false, ping_ms: 0, consecutive_failures: 0 }))
  );

  let monitoring = $state(false);
  let intervalSec = $state(30);
  let intervalTimer: ReturnType<typeof setInterval> | null = null;

  let log = $state<{ ts: string; kind: "ok" | "alert" | "info"; text: string }[]>([]);

  // Add server form
  let newName = $state("");
  let newIp = $state("");
  let newPort = $state(27015);

  function appendLog(kind: "ok" | "alert" | "info", text: string) {
    const ts = new Date().toLocaleTimeString("cs-CZ", { hour12: false });
    log = [{ ts, kind, text }, ...log].slice(0, 200);
  }

  async function probeOne(idx: number) {
    const s = servers[idx];
    try {
      const info: ServerInfo = await a2sApi.query(s.ip, s.port, 3000);
      const wasOnline = s.online;
      servers[idx] = {
        ...s,
        online: info.online,
        ping_ms: info.ping_ms,
        map: info.map,
        players: info.players,
        max_players: info.max_players,
        consecutive_failures: info.online ? 0 : s.consecutive_failures + 1,
      };
      // Edge transitions
      if (info.online && !wasOnline && s.consecutive_failures >= 2) {
        appendLog("ok", `✓ ${s.name} je zase online (${info.ping_ms} ms)`);
      } else if (!info.online && wasOnline) {
        appendLog("alert", `✗ ${s.name} přestal odpovídat`);
      }
    } catch (_) {
      servers[idx] = { ...s, online: false, ping_ms: 0, consecutive_failures: s.consecutive_failures + 1 };
    }
  }

  async function probeAll() {
    await Promise.all(servers.map((_, i) => probeOne(i)));
  }

  function startMonitoring() {
    if (monitoring) return;
    monitoring = true;
    appendLog("info", `▶ Monitoring spuštěn (interval ${intervalSec} s)`);
    probeAll();
    intervalTimer = setInterval(probeAll, Math.max(5, intervalSec) * 1000);
  }

  function stopMonitoring() {
    monitoring = false;
    if (intervalTimer) { clearInterval(intervalTimer); intervalTimer = null; }
    appendLog("info", "⏸ Monitoring zastaven");
  }

  function addServer() {
    const name = newName.trim();
    const ip = newIp.trim();
    if (!name || !ip || !newPort) return;
    servers = [...servers, { name, ip, port: newPort, online: false, ping_ms: 0, consecutive_failures: 0 }];
    newName = ""; newIp = ""; newPort = 27015;
  }

  function removeServer(idx: number) {
    servers = servers.filter((_, i) => i !== idx);
  }

  // Try fetch additional servers from website on mount
  onMount(async () => {
    try {
      const data = await httpApi.fetchJson<{ name: string; ip: string; port: number; game?: string }[]>(
        "https://zeddihub.eu/tools/data/servers.json", 3600,
      );
      if (Array.isArray(data)) {
        const seen = new Set(servers.map((s) => `${s.ip}:${s.port}`));
        for (const s of data) {
          const key = `${s.ip}:${s.port}`;
          if (!seen.has(key)) {
            servers = [...servers, { ...s, online: false, ping_ms: 0, consecutive_failures: 0 }];
            seen.add(key);
          }
        }
      }
    } catch (_) { /* offline OK */ }
  });

  onDestroy(() => {
    if (intervalTimer) clearInterval(intervalTimer);
  });
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <div class="flex items-center justify-between mb-1">
    <h1 class="text-3xl font-bold flex items-center gap-2">
      <Eye size={26} class="text-zh-primary" />
      Server Watchdog
    </h1>
    <div class="flex items-center gap-2 text-xs">
      <span class="w-2 h-2 rounded-full" class:bg-zh-success={monitoring} class:bg-zh-text-muted={!monitoring}></span>
      <span class:text-zh-success={monitoring} class:text-zh-text-muted={!monitoring}>
        {monitoring ? "Aktivní" : "Neaktivní"}
      </span>
    </div>
  </div>
  <p class="text-zh-text-muted text-sm mb-5">
    Periodicky monitoruje game servery (UDP A2S query) a hlásí změny stavu.
  </p>

  <!-- Controls -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-3">Nastavení</div>
    <div class="flex flex-wrap items-end gap-3">
      <label class="flex flex-col gap-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Interval kontroly (s)</span>
        <input bind:value={intervalSec} type="number" min="5" max="600"
          class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary"
          disabled={monitoring} />
      </label>
      {#if !monitoring}
        <Button variant="primary" onclick={startMonitoring}>
          <Play size={14} /> Spustit monitoring
        </Button>
      {:else}
        <Button variant="secondary" onclick={stopMonitoring}>
          <Square size={14} /> Zastavit
        </Button>
      {/if}
      <Button variant="ghost" onclick={probeAll}>
        <RefreshCw size={14} /> Otestovat hned
      </Button>
    </div>
  </Card>

  <!-- Server list -->
  <Card padding={3} class="mb-3">
    <table class="w-full text-sm">
      <thead>
        <tr class="text-left text-[10px] uppercase tracking-wider text-zh-text-muted border-b border-zh-divider">
          <th class="py-2 pl-2">Status</th>
          <th class="py-2">Server</th>
          <th class="py-2">IP : Port</th>
          <th class="py-2">Hra</th>
          <th class="py-2">Ping</th>
          <th class="py-2">Mapa</th>
          <th class="py-2">Hráči</th>
          <th class="py-2 pr-2"></th>
        </tr>
      </thead>
      <tbody>
        {#each servers as s, i (s.ip + ':' + s.port)}
          <tr class="border-b border-zh-divider/40 hover:bg-zh-card-hover/40 transition">
            <td class="py-1.5 pl-2">
              <span class="w-2.5 h-2.5 rounded-full inline-block" class:bg-zh-success={s.online} class:bg-zh-error={!s.online && s.consecutive_failures > 0} class:bg-zh-text-muted={!s.online && s.consecutive_failures === 0}></span>
            </td>
            <td class="py-1.5 font-semibold">{s.name}</td>
            <td class="py-1.5 text-xs font-mono text-zh-text-muted">{s.ip}:{s.port}</td>
            <td class="py-1.5 text-xs uppercase text-zh-text-muted">{s.game ?? "—"}</td>
            <td class="py-1.5 text-xs font-mono" class:text-zh-success={s.online && s.ping_ms < 100} class:text-zh-warning={s.online && s.ping_ms >= 100 && s.ping_ms < 200} class:text-zh-error={!s.online || s.ping_ms >= 200}>
              {s.online ? `${s.ping_ms} ms` : "—"}
            </td>
            <td class="py-1.5 text-xs text-zh-text-muted truncate max-w-[140px]">{s.map ?? "—"}</td>
            <td class="py-1.5 text-xs text-zh-text-muted">
              {#if s.players !== null && s.players !== undefined && s.max_players !== null && s.max_players !== undefined}
                {s.players} / {s.max_players}
              {:else}—{/if}
            </td>
            <td class="py-1.5 pr-2">
              <button onclick={() => removeServer(i)} class="text-zh-text-muted hover:text-zh-error transition">
                <Trash2 size={12} />
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Card>

  <!-- Add server -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-3 flex items-center gap-2">
      <Plus size={14} /> Přidat server
    </div>
    <div class="flex flex-wrap gap-2 items-end">
      <label class="flex flex-col gap-1 flex-1 min-w-[200px]">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Název</span>
        <input bind:value={newName} placeholder="ZeddiHub CS2 Test"
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
      </label>
      <label class="flex flex-col gap-1 flex-1 min-w-[150px]">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">IP / Host</span>
        <input bind:value={newIp} placeholder="93.99.7.63"
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Port</span>
        <input bind:value={newPort} type="number" min="1" max="65535"
          class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <Button variant="primary" onclick={addServer}>
        <Plus size={14} /> Přidat
      </Button>
    </div>
  </Card>

  <!-- Log -->
  <Card padding={3}>
    <div class="flex items-center gap-2 mb-2 text-[10px] uppercase tracking-wider text-zh-text-muted">
      <Bell size={11} />
      Log událostí
    </div>
    <div class="bg-black/40 rounded-entry h-48 overflow-auto p-3 font-mono text-[11px] leading-snug">
      {#if log.length === 0}
        <div class="text-zh-text-muted/60">// Log je prázdný. Spusť monitoring.</div>
      {/if}
      {#each log as e}
        <div class="flex gap-2">
          <span class="text-zh-text-muted/50 shrink-0">{e.ts}</span>
          <span class:text-zh-success={e.kind === "ok"} class:text-zh-error={e.kind === "alert"} class:text-zh-accent={e.kind === "info"}>
            {e.text}
          </span>
        </div>
      {/each}
    </div>
  </Card>
</div>
