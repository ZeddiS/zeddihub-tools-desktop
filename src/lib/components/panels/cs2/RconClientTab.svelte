<script lang="ts">
  import { Plug, PlugZap, Send, Trash2 } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { rconApi } from "$api/rcon";
  import { onDestroy } from "svelte";

  let host = $state("127.0.0.1");
  let port = $state(27015);
  let password = $state("");
  let cmd = $state("");
  let busy = $state(false);

  /** Active connection key (host:port) — null when not connected. */
  let connKey = $state<string | null>(null);
  let log = $state<{ kind: "in" | "out" | "info" | "err"; text: string; ts: string }[]>([]);
  let cmdHistory = $state<string[]>([]);
  let historyIdx = $state(-1);

  let logBox: HTMLDivElement | null = $state(null);

  const QUICK_COMMANDS = [
    "status",
    "users",
    "say Hello from ZeddiHub Tools",
    "changelevel de_dust2",
    "mp_restartgame 1",
  ];

  function append(kind: "in" | "out" | "info" | "err", text: string) {
    const ts = new Date().toLocaleTimeString("cs-CZ", { hour12: false });
    log = [...log, { kind, text, ts }];
    setTimeout(() => {
      if (logBox) logBox.scrollTop = logBox.scrollHeight;
    }, 0);
  }

  async function connect() {
    if (!password.trim()) {
      append("err", "RCON heslo je prázdné");
      return;
    }
    if (busy) return;
    busy = true;
    append("info", `→ Připojuji k ${host}:${port}…`);
    try {
      const key = await rconApi.connect(host, port, password);
      connKey = key;
      append("info", `✓ Připojeno k ${key}`);
    } catch (e: any) {
      append("err", `✗ ${e?.message ?? e?.key ?? e}`);
    }
    busy = false;
  }

  async function disconnect() {
    if (!connKey) return;
    try {
      await rconApi.disconnect(connKey);
    } catch (e) {
      console.warn("disconnect failed:", e);
    }
    append("info", `↓ Odpojeno od ${connKey}`);
    connKey = null;
  }

  async function send(text?: string) {
    const c = (text ?? cmd).trim();
    if (!c || !connKey || busy) return;
    busy = true;
    append("out", `> ${c}`);
    if (text === undefined) cmd = "";  // typed command -> clear input
    cmdHistory = [c, ...cmdHistory.filter((x) => x !== c)].slice(0, 50);
    historyIdx = -1;
    try {
      const resp = await rconApi.send(connKey, c);
      if (resp.trim()) {
        for (const line of resp.split(/\r?\n/)) {
          if (line) append("in", `  ${line}`);
        }
      } else {
        append("info", "  (no response)");
      }
    } catch (e: any) {
      append("err", `! ${e?.message ?? e}`);
      // If error suggests broken connection, reset state
      connKey = null;
    }
    busy = false;
  }

  function onKey(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    } else if (e.key === "ArrowUp" && cmdHistory.length > 0) {
      e.preventDefault();
      historyIdx = Math.min(historyIdx + 1, cmdHistory.length - 1);
      cmd = cmdHistory[historyIdx];
    } else if (e.key === "ArrowDown") {
      if (historyIdx > 0) {
        historyIdx -= 1;
        cmd = cmdHistory[historyIdx];
      } else {
        historyIdx = -1;
        cmd = "";
      }
    }
  }

  function clearLog() {
    log = [];
  }

  // Disconnect on component unmount (panel switch)
  onDestroy(() => {
    if (connKey) {
      const k = connKey;
      rconApi.disconnect(k).catch(() => {});
    }
  });
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">CS2 — RCON Klient</h3>
  <p class="text-xs text-zh-text-muted mb-3">Připojení k CS2 serveru přes Source RCON protokol (TCP).</p>

  <!-- Connection bar -->
  <Card class="mb-3">
    <div class="grid grid-cols-1 md:grid-cols-[1fr_120px_1fr_auto] gap-2 items-end">
      <div>
        <label for="rcon-host" class="text-[10px] uppercase tracking-wider text-zh-text-muted block mb-1">IP adresa</label>
        <input id="rcon-host" type="text" bind:value={host} disabled={!!connKey}
          class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60" />
      </div>
      <div>
        <label for="rcon-port" class="text-[10px] uppercase tracking-wider text-zh-text-muted block mb-1">Port</label>
        <input id="rcon-port" type="number" min="1" max="65535" bind:value={port} disabled={!!connKey}
          class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60" />
      </div>
      <div>
        <label for="rcon-pw" class="text-[10px] uppercase tracking-wider text-zh-text-muted block mb-1">RCON heslo</label>
        <input id="rcon-pw" type="password" bind:value={password} disabled={!!connKey}
          class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60" />
      </div>
      <div>
        {#if connKey}
          <Button variant="secondary" onclick={disconnect}>
            <PlugZap size={14} />
            Odpojit
          </Button>
        {:else}
          <Button variant="primary" onclick={connect} disabled={busy}>
            <Plug size={14} />
            {busy ? "…" : "Připojit"}
          </Button>
        {/if}
      </div>
    </div>

    <div class="flex items-center gap-2 mt-3 text-xs">
      <span class="w-2 h-2 rounded-full" class:bg-zh-success={connKey} class:bg-zh-error={!connKey}></span>
      <span class:text-zh-success={connKey} class:text-zh-error={!connKey}>
        {connKey ? `Připojeno: ${connKey}` : "Odpojeno"}
      </span>
    </div>
  </Card>

  <!-- Console output -->
  <Card padding={3} class="mb-3">
    <div class="flex items-center justify-between mb-2">
      <span class="text-[10px] uppercase tracking-wider text-zh-text-muted">Výstup konzole</span>
      <Button variant="ghost" onclick={clearLog} class="!h-6 text-[10px]">
        <Trash2 size={11} />
        Vyčistit
      </Button>
    </div>
    <div bind:this={logBox} class="bg-black/40 rounded-entry h-72 overflow-auto p-3 font-mono text-[11px] leading-snug">
      {#if log.length === 0}
        <div class="text-zh-text-muted/60">// Nepřipojeno. Vyplňte údaje nahoře a klikněte Připojit.</div>
      {/if}
      {#each log as entry}
        <div class="flex gap-2">
          <span class="text-zh-text-muted/50 shrink-0">{entry.ts}</span>
          <span
            class:text-[#22dd22]={entry.kind === "in"}
            class:text-zh-primary={entry.kind === "out"}
            class:text-zh-accent={entry.kind === "info"}
            class:text-zh-error={entry.kind === "err"}
            class="whitespace-pre-wrap break-words"
          >{entry.text}</span>
        </div>
      {/each}
    </div>
  </Card>

  <!-- Command input + quick buttons -->
  <div class="flex gap-2 mb-2">
    <input
      type="text"
      bind:value={cmd}
      onkeydown={onKey}
      placeholder="Zadejte RCON příkaz… (↑/↓ historie)"
      disabled={!connKey}
      class="flex-1 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60"
    />
    <Button variant="primary" onclick={() => send()} disabled={!connKey || busy} class="!h-10">
      <Send size={14} />
      Odeslat
    </Button>
  </div>

  <div class="flex flex-wrap gap-1.5">
    <span class="text-[10px] uppercase tracking-wider text-zh-text-muted self-center mr-1">Quick:</span>
    {#each QUICK_COMMANDS as qc}
      <button
        type="button"
        onclick={() => send(qc)}
        disabled={!connKey || busy}
        class="px-2.5 h-7 rounded text-[11px] font-mono bg-zh-card-bg hover:bg-zh-card-hover transition disabled:opacity-40"
      >
        {qc}
      </button>
    {/each}
  </div>
</div>
