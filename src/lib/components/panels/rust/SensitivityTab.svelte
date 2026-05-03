<script lang="ts">
  /**
   * Rust Sensitivity calculator — converts sens between 5 supported games.
   * Mirrors legacy/gui/panels/rust.py:_build_sensitivity (_SENS_MULT table).
   */

  import Card from "$components/ui/Card.svelte";

  type GameId = "CS2 / CS:GO" | "Rust" | "Valorant" | "Apex Legends" | "Overwatch";

  const SENS_MULT: Record<GameId, number> = {
    "CS2 / CS:GO": 0.022,
    "Rust": 0.1,
    "Valorant": 0.07,
    "Apex Legends": 0.022,
    "Overwatch": 0.0066,
  };

  const ALL_GAMES: GameId[] = ["CS2 / CS:GO", "Rust", "Valorant", "Apex Legends", "Overwatch"];

  let srcGame = $state<GameId>("CS2 / CS:GO");
  let srcSens = $state("1.0");
  let srcDpi  = $state("800");

  let dstGame = $state<GameId>("Rust");
  let dstDpi  = $state("800");

  // Derived: result + cm/360
  let result = $derived.by(() => {
    const s = parseFloat(srcSens.replace(",", "."));
    const sd = parseFloat(srcDpi);
    const dd = parseFloat(dstDpi);
    if (!Number.isFinite(s) || !Number.isFinite(sd) || !Number.isFinite(dd) || sd <= 0 || dd <= 0) {
      return { sens: "—", edpi: "Zadej platná čísla", cm: 0 };
    }
    const srcMult = SENS_MULT[srcGame];
    const dstMult = SENS_MULT[dstGame];
    if (s <= 0 || srcMult <= 0 || dstMult <= 0) return { sens: "—", edpi: "—", cm: 0 };
    const cmPer360 = 36000 / (sd * s * srcMult);
    const dstSens = 36000 / (dd * dstMult * cmPer360);
    return {
      sens: dstSens.toFixed(4).replace(/\.?0+$/, ""),
      edpi: `eDPI: ${Math.round(dd * dstSens)}  ·  ${cmPer360.toFixed(1)} cm/360°`,
      cm: cmPer360,
    };
  });

  const REFERENCE = [
    { label: "Nízká (sniperi)",      edpi: "200–400 eDPI",  cm: "12–25 cm" },
    { label: "Střední (universál)",  edpi: "400–800 eDPI",  cm: "5–12 cm" },
    { label: "Vysoká (CQC/stavba)",  edpi: "800–1600 eDPI", cm: "3–5 cm" },
  ];
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">Sensitivity Kalkulátor</h3>
  <p class="text-xs text-zh-text-muted mb-4">Převod mezi CS2/CS:GO, Rust, Valorant, Apex a Overwatch.</p>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
    <!-- Source -->
    <Card>
      <h4 class="text-sm font-bold text-zh-primary mb-3">Zdrojová hra</h4>
      <label class="grid grid-cols-[80px_1fr] items-center gap-3 py-1.5 text-sm">
        <span class="text-zh-text-muted">Hra:</span>
        <select bind:value={srcGame}
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary">
          {#each ALL_GAMES as g}
            <option value={g}>{g}</option>
          {/each}
        </select>
      </label>
      <label class="grid grid-cols-[80px_1fr] items-center gap-3 py-1.5 text-sm">
        <span class="text-zh-text-muted">Sensitivity:</span>
        <input type="text" bind:value={srcSens}
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
      <label class="grid grid-cols-[80px_1fr] items-center gap-3 py-1.5 text-sm">
        <span class="text-zh-text-muted">DPI:</span>
        <input type="number" bind:value={srcDpi} min="100" max="32000"
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
    </Card>

    <!-- Target -->
    <Card>
      <h4 class="text-sm font-bold text-zh-primary mb-3">Cílová hra</h4>
      <label class="grid grid-cols-[80px_1fr] items-center gap-3 py-1.5 text-sm">
        <span class="text-zh-text-muted">Hra:</span>
        <select bind:value={dstGame}
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm focus:outline-none focus:border-zh-primary">
          {#each ALL_GAMES as g}
            <option value={g}>{g}</option>
          {/each}
        </select>
      </label>
      <label class="grid grid-cols-[80px_1fr] items-center gap-3 py-1.5 text-sm">
        <span class="text-zh-text-muted">DPI:</span>
        <input type="number" bind:value={dstDpi} min="100" max="32000"
          class="bg-zh-card-hover border border-zh-border rounded-entry px-3 h-9 text-sm font-mono focus:outline-none focus:border-zh-primary" />
      </label>
    </Card>
  </div>

  <!-- Result -->
  <Card class="mb-4">
    <h4 class="text-sm font-bold text-zh-primary mb-2">Výsledek</h4>
    <div class="text-3xl font-mono font-bold text-zh-primary">{result.sens}</div>
    <div class="text-xs text-zh-text-muted mt-1">{result.edpi}</div>
  </Card>

  <!-- Reference -->
  <Card>
    <h4 class="text-sm font-bold text-zh-primary mb-2">Referenční cm/360°</h4>
    <ul class="text-sm space-y-1.5">
      {#each REFERENCE as r}
        <li class="flex items-baseline gap-2">
          <span class="text-zh-text">• {r.label}</span>
          <span class="text-zh-text-muted text-xs">{r.edpi} / {r.cm}/360°</span>
        </li>
      {/each}
    </ul>
  </Card>
</div>
