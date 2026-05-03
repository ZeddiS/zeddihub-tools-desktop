<script lang="ts">
  import { Cpu, MemoryStick, HardDrive, Laptop, RefreshCw } from "lucide-svelte";
  import { onMount, onDestroy } from "svelte";
  import Card from "$components/ui/Card.svelte";
  import Button from "$components/ui/Button.svelte";
  import { systemApi, type SystemInfo } from "$api/system";

  let info = $state<SystemInfo | null>(null);
  let busy = $state(false);
  let error = $state("");
  let timer: ReturnType<typeof setInterval> | null = null;

  async function refresh() {
    busy = true;
    error = "";
    try {
      info = await systemApi.info();
    } catch (e: any) {
      error = `✗ ${e?.message ?? e}`;
    }
    busy = false;
  }

  onMount(() => {
    refresh();
    timer = setInterval(refresh, 5000);
  });
  onDestroy(() => { if (timer) clearInterval(timer); });

  function fmtUptime(secs: number): string {
    const d = Math.floor(secs / 86400);
    const h = Math.floor((secs % 86400) / 3600);
    const m = Math.floor((secs % 3600) / 60);
    if (d > 0) return `${d}d ${h}h ${m}m`;
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
  }

  function fmtMb(mb: number): string {
    if (mb < 1024) return `${mb} MB`;
    return `${(mb / 1024).toFixed(1)} GB`;
  }
</script>

<div class="px-8 py-6 max-w-[1200px] mx-auto">
  <div class="flex items-center justify-between mb-1">
    <h1 class="text-3xl font-bold flex items-center gap-2">
      <Laptop size={26} class="text-zh-primary" />
      Systémové info
    </h1>
    <Button variant="ghost" onclick={refresh} disabled={busy} class="!h-8 text-xs">
      <RefreshCw size={12} class={busy ? "animate-spin" : ""} />
      Obnovit
    </Button>
  </div>
  <p class="text-zh-text-muted text-sm mb-5">Live informace o hardwaru, OS, CPU, RAM a discích. Auto-refresh každých 5 s.</p>

  {#if error}<div class="text-zh-error text-sm mb-3">{error}</div>{/if}

  {#if info}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-3">
      <!-- System -->
      <Card>
        <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-2 flex items-center gap-1.5">
          <Laptop size={11} />
          Systém
        </div>
        <ul class="text-xs space-y-1.5">
          <li><span class="text-zh-text-muted w-20 inline-block">OS:</span> <span class="text-zh-text">{info.os}</span></li>
          <li><span class="text-zh-text-muted w-20 inline-block">Arch:</span> <span class="text-zh-text font-mono">{info.arch}</span></li>
          <li><span class="text-zh-text-muted w-20 inline-block">Hostname:</span> <span class="text-zh-text font-mono">{info.hostname}</span></li>
          <li><span class="text-zh-text-muted w-20 inline-block">Uptime:</span> <span class="text-zh-text">{fmtUptime(info.uptime_secs)}</span></li>
        </ul>
      </Card>

      <!-- CPU -->
      <Card>
        <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-2 flex items-center gap-1.5">
          <Cpu size={11} />
          CPU
        </div>
        <div class="text-sm font-semibold mb-1">{info.cpu_name}</div>
        <div class="text-xs text-zh-text-muted mb-2">{info.cpu_cores} jader / threads</div>
        <div class="bg-zh-card-hover rounded-entry h-2 overflow-hidden mb-1">
          <div class="h-full transition-all"
               class:bg-zh-success={info.cpu_usage_pct < 50}
               class:bg-zh-warning={info.cpu_usage_pct >= 50 && info.cpu_usage_pct < 80}
               class:bg-zh-error={info.cpu_usage_pct >= 80}
               style:width="{info.cpu_usage_pct}%"></div>
        </div>
        <div class="text-xs font-mono text-right">{info.cpu_usage_pct.toFixed(1)} %</div>
      </Card>

      <!-- Memory -->
      <Card>
        <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-2 flex items-center gap-1.5">
          <MemoryStick size={11} />
          RAM
        </div>
        <div class="text-sm font-semibold mb-1">{fmtMb(info.used_memory_mb)} / {fmtMb(info.total_memory_mb)}</div>
        <div class="text-xs text-zh-text-muted mb-2">Volné: {fmtMb(info.total_memory_mb - info.used_memory_mb)}</div>
        <div class="bg-zh-card-hover rounded-entry h-2 overflow-hidden mb-1">
          <div class="h-full transition-all"
               class:bg-zh-success={info.mem_usage_pct < 50}
               class:bg-zh-warning={info.mem_usage_pct >= 50 && info.mem_usage_pct < 80}
               class:bg-zh-error={info.mem_usage_pct >= 80}
               style:width="{info.mem_usage_pct}%"></div>
        </div>
        <div class="text-xs font-mono text-right">{info.mem_usage_pct.toFixed(1)} %</div>
      </Card>
    </div>

    <!-- Disks -->
    <Card padding={3}>
      <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-3 flex items-center gap-1.5">
        <HardDrive size={11} />
        Disky ({info.disks.length})
      </div>
      <div class="space-y-2">
        {#each info.disks as d}
          <div>
            <div class="flex items-baseline justify-between text-xs mb-1">
              <span class="font-mono font-semibold">{d.mount}</span>
              <span class="text-zh-text-muted">{d.kind} — {fmtMb(d.used_mb)} / {fmtMb(d.total_mb)} ({d.usage_pct.toFixed(1)} %)</span>
            </div>
            <div class="bg-zh-card-hover rounded-entry h-1.5 overflow-hidden">
              <div class="h-full transition-all"
                   class:bg-zh-success={d.usage_pct < 70}
                   class:bg-zh-warning={d.usage_pct >= 70 && d.usage_pct < 90}
                   class:bg-zh-error={d.usage_pct >= 90}
                   style:width="{d.usage_pct}%"></div>
            </div>
          </div>
        {/each}
      </div>
    </Card>
  {:else}
    <Card>
      <div class="text-zh-text-muted text-sm">Načítám systémové info…</div>
    </Card>
  {/if}
</div>
