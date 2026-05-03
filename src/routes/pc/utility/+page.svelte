<script lang="ts">
  import { Wrench, Timer, Hourglass, Cpu, Power, RefreshCw, Search } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import { onMount, onDestroy } from "svelte";
  import { systemApi, type ProcessInfo } from "$api/system";
  import { Command } from "@tauri-apps/plugin-shell";

  type Tab = "stopwatch" | "countdown" | "processes" | "shutdown";
  let active = $state<Tab>("stopwatch");

  // ── Stopwatch ──
  let swElapsed = $state(0);
  let swRunning = $state(false);
  let swTimer: ReturnType<typeof setInterval> | null = null;
  let swLaps = $state<number[]>([]);

  function swStart() {
    if (swRunning) return;
    swRunning = true;
    const start = Date.now() - swElapsed;
    swTimer = setInterval(() => { swElapsed = Date.now() - start; }, 50);
  }
  function swStop() {
    swRunning = false;
    if (swTimer) { clearInterval(swTimer); swTimer = null; }
  }
  function swReset() {
    swStop();
    swElapsed = 0;
    swLaps = [];
  }
  function swLap() {
    if (swRunning) swLaps = [swElapsed, ...swLaps].slice(0, 30);
  }
  function fmtMs(ms: number): string {
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60).toString().padStart(2, "0");
    const s = (totalSec % 60).toString().padStart(2, "0");
    const cs = Math.floor((ms % 1000) / 10).toString().padStart(2, "0");
    return `${m}:${s}.${cs}`;
  }

  // ── Countdown ──
  let cdMin = $state(5);
  let cdSec = $state(0);
  let cdRemaining = $state(0);
  let cdRunning = $state(false);
  let cdTimer: ReturnType<typeof setInterval> | null = null;

  function cdStart() {
    if (cdRunning) return;
    cdRemaining = (cdMin * 60 + cdSec) * 1000;
    if (cdRemaining <= 0) return;
    cdRunning = true;
    const end = Date.now() + cdRemaining;
    cdTimer = setInterval(() => {
      cdRemaining = Math.max(0, end - Date.now());
      if (cdRemaining <= 0) {
        cdStop();
        try { new Audio("data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=").play(); } catch (_) {}
      }
    }, 100);
  }
  function cdStop() {
    cdRunning = false;
    if (cdTimer) { clearInterval(cdTimer); cdTimer = null; }
  }

  // ── Processes ──
  let procs = $state<ProcessInfo[]>([]);
  let procFilter = $state("");
  let procBusy = $state(false);
  let procAutoRefresh = $state(false);
  let procTimer: ReturnType<typeof setInterval> | null = null;

  async function refreshProcs() {
    procBusy = true;
    try { procs = await systemApi.processList(); }
    catch (_) {}
    procBusy = false;
  }

  $effect(() => {
    if (procAutoRefresh && active === "processes") {
      procTimer = setInterval(refreshProcs, 3000);
    } else if (procTimer) {
      clearInterval(procTimer); procTimer = null;
    }
  });

  $effect(() => {
    if (active === "processes" && procs.length === 0) refreshProcs();
  });

  let filtered = $derived.by(() => {
    if (!procFilter.trim()) return procs.slice(0, 100);
    const q = procFilter.toLowerCase();
    return procs.filter(p => p.name.toLowerCase().includes(q) || String(p.pid).includes(q)).slice(0, 100);
  });

  async function killProc(pid: number) {
    if (!confirm(`Opravdu zabít proces PID ${pid}?`)) return;
    try {
      await systemApi.processKill(pid);
      await refreshProcs();
    } catch (e) { console.warn(e); }
  }

  // ── Shutdown timer ──
  let sdMinutes = $state(60);
  let sdActive = $state(false);
  let sdRemaining = $state(0);
  let sdTimer: ReturnType<typeof setInterval> | null = null;

  async function sdSchedule() {
    if (sdActive) return;
    if (sdMinutes <= 0) return;
    sdActive = true;
    sdRemaining = sdMinutes * 60 * 1000;
    const end = Date.now() + sdRemaining;
    sdTimer = setInterval(() => {
      sdRemaining = Math.max(0, end - Date.now());
      if (sdRemaining <= 0 && sdTimer) { clearInterval(sdTimer); sdTimer = null; sdActive = false; }
    }, 1000);
    try {
      const cmd = Command.create("shutdown", ["/s", "/t", String(sdMinutes * 60)]);
      await cmd.execute();
    } catch (e) { console.warn(e); }
  }
  async function sdCancel() {
    sdActive = false;
    if (sdTimer) { clearInterval(sdTimer); sdTimer = null; }
    try {
      const cmd = Command.create("shutdown", ["/a"]);
      await cmd.execute();
    } catch (e) { console.warn(e); }
  }

  onDestroy(() => {
    if (swTimer) clearInterval(swTimer);
    if (cdTimer) clearInterval(cdTimer);
    if (procTimer) clearInterval(procTimer);
    if (sdTimer) clearInterval(sdTimer);
  });
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Wrench size={26} class="text-zh-primary" />
    Utility
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">Stopky / Odpočet / Procesy / Shutdown timer.</p>

  <Tabs
    bind:active
    tabs={[
      { id: "stopwatch", label: "Stopky",         icon: Timer },
      { id: "countdown", label: "Odpočet",        icon: Hourglass },
      { id: "processes", label: "Procesy",        icon: Cpu },
      { id: "shutdown",  label: "Shutdown timer", icon: Power },
    ]}
  />

  <div class="mt-6">
    {#if active === "stopwatch"}
      <Card class="max-w-2xl">
        <div class="text-center mb-4">
          <div class="text-6xl font-mono font-bold text-zh-primary">{fmtMs(swElapsed)}</div>
        </div>
        <div class="flex justify-center gap-2 mb-4">
          {#if !swRunning}
            <Button variant="primary" onclick={swStart}>Start</Button>
          {:else}
            <Button variant="secondary" onclick={swStop}>Pauza</Button>
          {/if}
          <Button variant="ghost" onclick={swLap} disabled={!swRunning}>Lap</Button>
          <Button variant="ghost" onclick={swReset}>Reset</Button>
        </div>
        {#if swLaps.length > 0}
          <div class="font-mono text-xs space-y-0.5 max-h-48 overflow-auto">
            {#each swLaps as l, i}
              <div class="flex justify-between bg-zh-card-hover/50 rounded px-3 py-1">
                <span class="text-zh-text-muted">Lap #{swLaps.length - i}</span>
                <span class="text-zh-text">{fmtMs(l)}</span>
              </div>
            {/each}
          </div>
        {/if}
      </Card>

    {:else if active === "countdown"}
      <Card class="max-w-2xl">
        <div class="flex flex-wrap items-end gap-3 mb-4">
          <label class="flex flex-col gap-1">
            <span class="text-[10px] uppercase text-zh-text-muted">Minuty</span>
            <input bind:value={cdMin} type="number" min="0" max="999" disabled={cdRunning}
              class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-[10px] uppercase text-zh-text-muted">Sekundy</span>
            <input bind:value={cdSec} type="number" min="0" max="59" disabled={cdRunning}
              class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
          </label>
          {#if !cdRunning}
            <Button variant="primary" onclick={cdStart}>Spustit</Button>
          {:else}
            <Button variant="secondary" onclick={cdStop}>Stop</Button>
          {/if}
        </div>
        <div class="text-center">
          <div class="text-6xl font-mono font-bold" class:text-zh-primary={cdRunning} class:text-zh-text-muted={!cdRunning}>
            {fmtMs(cdRemaining)}
          </div>
        </div>
      </Card>

    {:else if active === "processes"}
      <div class="flex flex-wrap gap-2 mb-3 items-center">
        <div class="relative flex-1 max-w-md">
          <Search size={12} class="absolute left-3 top-1/2 -translate-y-1/2 text-zh-text-muted" />
          <input bind:value={procFilter} placeholder="Filtr (name / pid)"
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry pl-9 pr-3 h-9 text-sm focus:outline-none focus:border-zh-primary" />
        </div>
        <Button variant="ghost" onclick={refreshProcs} disabled={procBusy}>
          <RefreshCw size={12} class={procBusy ? "animate-spin" : ""} /> Obnovit
        </Button>
        <label class="flex items-center gap-2 text-xs text-zh-text-muted cursor-pointer">
          <input type="checkbox" bind:checked={procAutoRefresh} class="accent-zh-primary" />
          Auto (3s)
        </label>
      </div>
      <Card padding={3}>
        <table class="w-full text-xs">
          <thead>
            <tr class="text-left text-[10px] uppercase tracking-wider text-zh-text-muted border-b border-zh-divider">
              <th class="py-2 pl-2">PID</th>
              <th class="py-2">Name</th>
              <th class="py-2">CPU %</th>
              <th class="py-2">Mem MB</th>
              <th class="py-2 pr-2"></th>
            </tr>
          </thead>
          <tbody>
            {#each filtered as p (p.pid)}
              <tr class="border-b border-zh-divider/40 hover:bg-zh-card-hover/40 transition">
                <td class="py-1 pl-2 font-mono">{p.pid}</td>
                <td class="py-1 truncate max-w-[280px]">{p.name}</td>
                <td class="py-1 font-mono" class:text-zh-warning={p.cpu_pct > 50}>{p.cpu_pct.toFixed(1)}</td>
                <td class="py-1 font-mono">{p.memory_mb}</td>
                <td class="py-1 pr-2">
                  <button class="text-zh-text-muted hover:text-zh-error text-[10px]" onclick={() => killProc(p.pid)}>Kill</button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
        <div class="text-[10px] text-zh-text-muted mt-2 text-right">{filtered.length} z {procs.length} procesů</div>
      </Card>

    {:else if active === "shutdown"}
      <Card class="max-w-2xl">
        <div class="flex flex-wrap items-end gap-3 mb-4">
          <label class="flex flex-col gap-1">
            <span class="text-[10px] uppercase text-zh-text-muted">Vypnutí za (min)</span>
            <input bind:value={sdMinutes} type="number" min="1" max="1440" disabled={sdActive}
              class="w-32 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
          </label>
          {#if !sdActive}
            <Button variant="primary" onclick={sdSchedule}>
              <Power size={14} /> Naplánovat vypnutí
            </Button>
          {:else}
            <Button variant="secondary" onclick={sdCancel}>Zrušit</Button>
          {/if}
        </div>
        {#if sdActive}
          <div class="text-center">
            <div class="text-xs text-zh-text-muted mb-1">PC se vypne za:</div>
            <div class="text-4xl font-mono font-bold text-zh-error">{fmtMs(sdRemaining)}</div>
          </div>
        {:else}
          <p class="text-xs text-zh-text-muted">
            Spustí Windows příkaz <code>shutdown /s /t {sdMinutes * 60}</code>. Můžeš kdykoliv zrušit.
          </p>
        {/if}
      </Card>
    {/if}
  </div>
</div>
