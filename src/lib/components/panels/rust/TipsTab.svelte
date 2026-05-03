<script lang="ts">
  import Card from "$components/ui/Card.svelte";

  // Mirror legacy rust.py:_build_tips
  const SECTIONS: { title: string; tips: [string, string][] }[] = [
    {
      title: "Výkon (FPS)",
      tips: [
        ["graphics.quality 0–2", "Snížení grafiky pro vyšší FPS (0=nejnižší)"],
        ["fps.limit 0",           "Odstraní FPS omezení — nech GPU na max"],
        ["grass.on false",        "Vypnutí trávy = velký FPS boost ve venkovních oblastech"],
        ["shadowmode 0",          "Vypnutí stínů = výrazné zvýšení FPS"],
        ["lodrange 100",          "Nižší LOD vzdálenost = méně detailů = vyšší FPS"],
        ["terrain.quality 50",    "Snížení kvality terénu pro výkon"],
      ],
    },
    {
      title: "Hratelnost",
      tips: [
        ["audio.voice 0.5",         "Ztlumení hlasů ostatních hráčů"],
        ["audio.game 0.8",          "Herní zvuky — nech slyšitelné pro kroky"],
        ["graphics.fov 90",         "Field of View — vyšší = lepší přehled"],
        ["net.connect <IP>:<PORT>", "Připojení k serveru přes konzoli"],
        ["status",                  "Zobrazí info o aktuálním serveru a hráčích"],
      ],
    },
    {
      title: "Užitečné konzolové příkazy",
      tips: [
        ["kill",                  "Zabiješ vlastní postavu (rychlý restart)"],
        ["respawn",               "Respawn na náhodné místo"],
        ["global.debugcamera",    "Debug kamera (pro adminy)"],
        ["quit",                  "Ukončení hry (alternativa k Alt+F4)"],
        ["client.connect <IP>",   "Přímé připojení k serveru"],
      ],
    },
  ];
</script>

<div>
  <h3 class="text-lg font-bold text-zh-primary mb-1">Rust — Tipy & Optimalizace</h3>
  <p class="text-xs text-zh-text-muted mb-4">Doporučené nastavení a tipy pro lepší výkon a hratelnost.</p>

  <div class="space-y-3">
    {#each SECTIONS as sec}
      <Card>
        <h4 class="text-sm font-bold text-zh-primary mb-2">{sec.title}</h4>
        <ul class="text-sm space-y-1.5">
          {#each sec.tips as [cmd, desc]}
            <li class="grid grid-cols-[200px_1fr] gap-3 items-baseline">
              <code class="text-zh-accent font-mono text-[11px] break-all">{cmd}</code>
              <span class="text-zh-text-muted text-xs">{desc}</span>
            </li>
          {/each}
        </ul>
      </Card>
    {/each}
  </div>
</div>
