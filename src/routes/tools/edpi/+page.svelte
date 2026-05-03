<script lang="ts">
  import { Calculator, Trophy } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import { CS2_PROS } from "$lib/data/gameTools";

  let dpi  = $state("800");
  let sens = $state("1.0");

  let edpi = $derived.by(() => {
    const d = parseFloat(dpi.replace(",", "."));
    const s = parseFloat(sens.replace(",", "."));
    if (!Number.isFinite(d) || !Number.isFinite(s) || d <= 0 || s <= 0) return null;
    return d * s;
  });

  let rating = $derived.by(() => {
    if (edpi === null) return "";
    if (edpi < 400)  return "⬇ Velmi nízké eDPI — extreme low sens";
    if (edpi < 800)  return "🎯 Nízké eDPI — competitive / esport tier";
    if (edpi < 1600) return "✅ Střední eDPI — typický hráč";
    if (edpi < 3200) return "⬆ Vysoké eDPI — casual hráč";
    return "🔺 Velmi vysoké eDPI — zkus snížit DPI nebo sens";
  });

  const TIERS: { range: string; color: string; desc: string }[] = [
    { range: "< 400",      color: "#f87171", desc: "Velmi nízké — extreme low sens" },
    { range: "400–800",    color: "#fb923c", desc: "Nízké — competitive / esport" },
    { range: "800–1600",   color: "#4ade80", desc: "Střední — běžný hráč" },
    { range: "1600–3200",  color: "#fbbf24", desc: "Vysoké — casual" },
    { range: "> 3200",     color: "#a78bfa", desc: "Velmi vysoké — beginners" },
  ];
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Calculator size={26} class="text-zh-primary" />
    eDPI Kalkulačka
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">
    eDPI (effective DPI) = DPI × in-game sensitivity. Umožňuje porovnání citlivosti napříč různými DPI.
  </p>

  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-3">Výpočet eDPI</div>
    <div class="flex flex-wrap items-end gap-6">
      <label class="flex flex-col gap-1">
        <span class="text-xs text-zh-text-muted">DPI:</span>
        <input bind:value={dpi} type="number" min="100" max="32000"
          class="w-32 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-base font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-xs text-zh-text-muted">In-game Sensitivity:</span>
        <input bind:value={sens} type="text"
          class="w-32 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-base font-mono focus:outline-none focus:border-zh-primary" />
      </label>
    </div>
  </Card>

  <!-- Result -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-1">eDPI:</div>
    <div class="text-5xl font-mono font-bold text-zh-success">{edpi !== null ? edpi.toFixed(0) : "—"}</div>
    <div class="text-xs text-zh-text-muted mt-2">{rating}</div>
  </Card>

  <!-- Tiers -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-3">eDPI Tiers pro FPS hry</div>
    <ul class="text-sm space-y-1.5">
      {#each TIERS as t}
        <li class="flex items-center gap-3">
          <span class="w-3 h-3 rounded shrink-0" style:background-color={t.color}></span>
          <span class="text-zh-text font-bold w-24 font-mono text-xs">{t.range}</span>
          <span class="text-zh-text-muted text-xs">{t.desc}</span>
        </li>
      {/each}
    </ul>
  </Card>

  <!-- CS2 pros table -->
  <Card>
    <div class="text-sm font-bold text-zh-primary mb-3 flex items-center gap-2">
      <Trophy size={14} />
      Referenční hodnoty pro-hráčů (CS2)
    </div>
    <div class="overflow-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-xs uppercase tracking-wider text-zh-text-muted border-b border-zh-divider">
            <th class="py-2 font-semibold">Hráč</th>
            <th class="py-2 font-semibold">DPI</th>
            <th class="py-2 font-semibold">Sens</th>
            <th class="py-2 font-semibold">eDPI</th>
          </tr>
        </thead>
        <tbody>
          {#each CS2_PROS as p}
            <tr class="border-b border-zh-divider/50 hover:bg-zh-card-hover/40 transition">
              <td class="py-1.5 font-semibold">{p.name}</td>
              <td class="py-1.5 font-mono text-zh-text-muted">{p.dpi}</td>
              <td class="py-1.5 font-mono text-zh-text-muted">{p.sens}</td>
              <td class="py-1.5 font-mono text-zh-primary">{Math.round(p.dpi * p.sens)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </Card>
</div>
