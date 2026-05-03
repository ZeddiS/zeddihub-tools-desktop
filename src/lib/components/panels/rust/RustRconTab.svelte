<script lang="ts">
  import { Plug, PlugZap, Send, Trash2 } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import { rustRconApi } from "$api/rustRcon";
  import { onDestroy } from "svelte";

  let host = $state("127.0.0.1");
  let port = $state(28016);
  let password = $state("");
  let cmd = $state("");
  let busy = $state(false);

  let connKey = $state<string | null>(null);
  let log = $state<{ kind: "in" | "out" | "info" | "err"; text: string; ts: string }[]>([]);
  let cmdHistory = $state<string[]>([]);
  let historyIdx = $state(-1);

  let logBox: HTMLDivElement | null = $state(null);
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  const QUICK_COMMANDS = [
    "playerlist",
    "serverinfo",
    "save",
    "say <ZeddiHub>: hello",
    "oxide.reload *",
  ];

  function append(kind: "in" | "out" | "info" | "err", text: string) {
    const ts = new Date().toLocaleTimeString("cs-CZ", { hour12: false });
    log = [...log, { kind, text, ts }];
    setTimeout(() => { if (logBox) logBox.scrollTop = logBox.scrollHeight; }, 0);
  }

  async function connect() {
    if (!password.trim()) {
      append("err", "RCON heslo je prázdné");
      return;
    }
    if (busy) return;
    busy = true;
    append("info", `→ Připojuji ws://${host}:${port}…`);
    try {
      const key = await rustRconApi.connect(host, port, password);
      connKey = key;
      append("info", `✓ Připojeno k ${key}`);
      // Start polling for buffered server messages every 500 ms
      pollTimer = setInterval(pollMessages, 500);
    } catch (e: any) {
      append("err", `✗ ${e?.message ?? e?.key ?? e}`);
    }
    busy = false;
  }

  async function pollMessages() {
    if (!connKey) return;
    try {
      const lines = await rustRconApi.recv(connKey);
      for (const line of lines) {
        if (line.trim()) append("in", `  ${line}`);
      }
    } catch (e: any) {
      // Connection died on backend — reset
      append("err", `! ${e?.message ?? e}`);
      stopPolling();
      connKey = null;
    }
  }

  function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  async function disconnect() {
    if (!connKey) return;
    stopPolling();
    try { await rustRconApi.disconnect(connKey); } catch (_) { /* ignore */ }
    append("info", `↓ Odpojeno od ${connKey}`);
    connKey = null;
  }

  async function send(text?: string) {
    const c = (text ?? cmd).trim();
    if (!c || !connKey || busy) return;
    busy = true;
    append("out", `> ${c}`);
    if (text === undefined) cmd = "";
    cmdHistory = [c, ...cmdHistory.filter((x) => x !== c)].slice(0, 50);
    historyIdx = -1;
    try {
      await rustRconApi.send(connKey, c);
      // Response will arrive via pollMessages()
    } catch (e: any) {
      append("err", `! ${e?.message ?? e}`);
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

  function clearLog() { log = []; }

  onDestroy(() => {
    stopPolling();
    if (connKey) {
      const k = connKey;
      rustRconApi.disconnect(k).catch(() => {});
    }
  });
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">Rust — RCON Klient (Facepunch / WebSocket)</h3>
  <p class="text-xs text-zh-text-muted mb-3">
    Připojení přes <code class="text-zh-primary">ws://host:port/password</code> — odlišný protokol než Source RCON.
  </p>

  <Card class="mb-3">
    <div class="grid grid-cols-1 md:grid-cols-[1fr_120px_1fr_auto] gap-2 items-end">
      <div>
        <label for="rrcon-host" class="text-[10px] uppercase tracking-wider text-zh-text-muted block mb-1">IP / Host</label>
        <input id="rrcon-host" type="text" bind:value={host} disabled={!!connKey}
          class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60" />
      </div>
      <div>
        <label for="rrcon-port" class="text-[10px] uppercase tracking-wider text-zh-text-muted block mb-1">RCON port</label>
        <input id="rrcon-port" type="number" min="1" max="65535" bind:value={port} disabled={!!connKey}
          class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60" />
      </div>
      <div>
        <label for="rrcon-pw" class="text-[10px] uppercase tracking-wider text-zh-text-muted block mb-1">RCON heslo</label>
        <input id="rrcon-pw" type="password" bind:value={password} disabled={!!connKey}
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

  <div class="flex gap-2 mb-2">
    <input type="text" bind:value={cmd} onkeydown={onKey}
      placeholder="Zadejte RCON příkaz… (↑/↓ historie)" disabled={!connKey}
      class="flex-1 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm font-mono focus:outline-none focus:border-zh-primary disabled:opacity-60" />
    <Button variant="primary" onclick={() => send()} disabled={!connKey || busy} class="!h-10">
      <Send size={14} />
      Odeslat
    </Button>
  </div>

  <div class="flex flex-wrap gap-1.5">
    <span class="text-[10px] uppercase tracking-wider text-zh-text-muted self-center mr-1">Quick:</span>
    {#each QUICK_COMMANDS as qc}
      <button type="button" onclick={() => send(qc)} disabled={!connKey || busy}
        class="px-2.5 h-7 rounded text-[11px] font-mono bg-zh-card-bg hover:bg-zh-card-hover transition disabled:opacity-40">
        {qc}
      </button>
    {/each}
  </div>
</div>
