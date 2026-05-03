<script lang="ts">
  import { Crosshair, Target, Ruler, FlaskConical } from "lucide-svelte";
  import Card from "$components/ui/Card.svelte";
  import { SENS_GAMES, SENS_GAME_NAMES } from "$lib/data/gameTools";

  let srcGame = $state<string>("CS2 / CS:GO");
  let srcSens = $state("1.0");
  let srcDpi  = $state("800");

  let dstGame = $state<string>("Valorant");
  let dstDpi  = $state("800");

  let result = $derived.by(() => {
    const s = parseFloat(srcSens.replace(",", "."));
    const sd = parseFloat(srcDpi);
    const dd = parseFloat(dstDpi);
    if (!Number.isFinite(s) || !Number.isFinite(sd) || !Number.isFinite(dd) || s <= 0 || sd <= 0 || dd <= 0) {
      return { sens: "—", cm360: 0, edpi: 0, detail: "Vyplň hodnoty výše" };
    }
    const sm = SENS_GAMES[srcGame] ?? 0.022;
    const dm = SENS_GAMES[dstGame] ?? 0.022;
    const cm360 = 36000 / (sd * s * sm);
    const dstSens = 36000 / (dd * dm * cm360);
    return {
      sens: dstSens.toFixed(4),
      cm360,
      edpi: Math.round(sd * s),
      detail: `${srcGame} ${s} @ ${Math.round(sd)} DPI  →  ${dstGame} ${dstSens.toFixed(4)} @ ${Math.round(dd)} DPI  ·  ${cm360.toFixed(2)} cm/360°`,
    };
  });

  const REFS: [string, string][] = [
    ["< 20 cm",   "Velmi rychlá — esport"],
    ["20–30 cm",  "Rychlá — FPS standard"],
    ["30–45 cm",  "Střední — comfortable"],
    ["45–70 cm",  "Pomalá — tactical / sniper"],
    ["> 70 cm",   "Velmi pomalá — strategy"],
  ];
</script>

<div class="px-8 py-6 max-w-[1100px] mx-auto">
  <h1 class="text-3xl font-bold mb-1 flex items-center gap-2">
    <Crosshair size={26} class="text-zh-primary" />
    Sensitivity Converter
  </h1>
  <p class="text-zh-text-muted text-sm mb-5">
    Převede citlivost myši mezi hrami. Zachovává stejné fyzické pohyby (cm/360°).
  </p>

  <!-- Input card -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-3">Zdrojová hra</div>
    <div class="flex flex-wrap items-center gap-3">
      <select bind:value={srcGame}
        class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary min-w-52">
        {#each SENS_GAME_NAMES as g}<option>{g}</option>{/each}
      </select>
      <label class="flex items-center gap-2 text-xs text-zh-text-muted">
        <span>Sensitivity:</span>
        <input bind:value={srcSens} type="text"
          class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <label class="flex items-center gap-2 text-xs text-zh-text-muted">
        <span>DPI:</span>
        <input bind:value={srcDpi} type="number" min="100" max="32000"
          class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
    </div>
    <div class="text-xs text-zh-text-muted mt-3 flex items-center gap-2">
      <Ruler size={12} />
      <span>cm/360°: <strong class="text-zh-text">{result.cm360.toFixed(2)} cm</strong>  |  eDPI: <strong class="text-zh-text">{result.edpi}</strong></span>
    </div>
  </Card>

  <!-- Output card -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-3">Cílová hra</div>
    <div class="flex flex-wrap items-center gap-3">
      <select bind:value={dstGame}
        class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary min-w-52">
        {#each SENS_GAME_NAMES as g}<option>{g}</option>{/each}
      </select>
      <label class="flex items-center gap-2 text-xs text-zh-text-muted">
        <span>Target DPI:</span>
        <input bind:value={dstDpi} type="number" min="100" max="32000"
          class="w-24 bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
    </div>
  </Card>

  <!-- Result -->
  <Card class="mb-3">
    <div class="text-sm font-bold text-zh-primary mb-1 flex items-center gap-2">
      <Target size={14} />
      Výsledek
    </div>
    <div class="text-4xl font-mono font-bold text-zh-success">{result.sens}</div>
    <div class="text-xs text-zh-text-muted mt-2">{result.detail}</div>
  </Card>

  <!-- Reference table -->
  <Card>
    <div class="text-sm font-bold text-zh-primary mb-3 flex items-center gap-2">
      <FlaskConical size={14} />
      Tabulka cm/360° → pocit
    </div>
    <ul class="text-sm space-y-1.5">
      {#each REFS as [range, desc]}
        <li class="flex items-baseline gap-3">
          <span class="text-zh-primary font-bold w-24 font-mono text-xs">{range}</span>
          <span class="text-zh-text-muted text-xs">{desc}</span>
        </li>
      {/each}
    </ul>
  </Card>
</div>
