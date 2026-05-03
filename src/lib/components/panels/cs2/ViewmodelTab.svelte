<script lang="ts">
  import { Save, Sparkles } from "lucide-svelte";
  import Button from "$components/ui/Button.svelte";
  import Card from "$components/ui/Card.svelte";
  import Stepper from "$components/form/Stepper.svelte";
  import Dropdown from "$components/form/Dropdown.svelte";
  import { saveCfgFile } from "$api/saveFile";

  // Reactive vars (mirrors legacy _vm_vars)
  let viewmodel_fov       = $state("68");
  let viewmodel_offset_x  = $state("2.5");
  let viewmodel_offset_y  = $state("0");
  let viewmodel_offset_z  = $state("-1.5");
  let viewmodel_presetpos = $state("3");
  let cl_bob_lower_amt    = $state("5");
  let cl_bobamt_lat       = $state("0.1");
  let cl_bobamt_vert      = $state("0.1");

  let canvas: HTMLCanvasElement | null = $state(null);
  let saveStatus = $state("");

  type Vars = Record<string, string>;
  function buildVars(): Vars {
    return {
      viewmodel_fov, viewmodel_offset_x, viewmodel_offset_y, viewmodel_offset_z,
      viewmodel_presetpos, cl_bob_lower_amt, cl_bobamt_lat, cl_bobamt_vert,
    };
  }

  const presets: { name: string; vals: Vars }[] = [
    {
      name: "Competitive (Classic)",
      vals: { viewmodel_fov: "68", viewmodel_offset_x: "2.5", viewmodel_offset_y: "0", viewmodel_offset_z: "-1.5", viewmodel_presetpos: "3" },
    },
    {
      name: "Wide FOV",
      vals: { viewmodel_fov: "68", viewmodel_offset_x: "-2", viewmodel_offset_y: "0", viewmodel_offset_z: "-2", viewmodel_presetpos: "1" },
    },
    {
      name: "Pro player style",
      vals: {
        viewmodel_fov: "68", viewmodel_offset_x: "2.5", viewmodel_offset_y: "0", viewmodel_offset_z: "-1.5",
        viewmodel_presetpos: "3", cl_bob_lower_amt: "21", cl_bobamt_lat: "0.33", cl_bobamt_vert: "0.14",
      },
    },
  ];

  function applyPreset(vals: Vars) {
    if ("viewmodel_fov"      in vals) viewmodel_fov       = vals.viewmodel_fov;
    if ("viewmodel_offset_x" in vals) viewmodel_offset_x  = vals.viewmodel_offset_x;
    if ("viewmodel_offset_y" in vals) viewmodel_offset_y  = vals.viewmodel_offset_y;
    if ("viewmodel_offset_z" in vals) viewmodel_offset_z  = vals.viewmodel_offset_z;
    if ("viewmodel_presetpos" in vals) viewmodel_presetpos = vals.viewmodel_presetpos;
    if ("cl_bob_lower_amt"   in vals) cl_bob_lower_amt    = vals.cl_bob_lower_amt;
    if ("cl_bobamt_lat"      in vals) cl_bobamt_lat       = vals.cl_bobamt_lat;
    if ("cl_bobamt_vert"     in vals) cl_bobamt_vert      = vals.cl_bobamt_vert;
  }

  function draw() {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;

    const fov = parseFloat(viewmodel_fov) || 68;
    const ox  = parseFloat(viewmodel_offset_x) || 0;
    const oz  = parseFloat(viewmodel_offset_z) || 0;

    // Resolve theme tokens at draw time so light/dark switching reflects
    const cs = getComputedStyle(document.documentElement);
    const cardBg = `rgb(${cs.getPropertyValue("--zh-card-bg").trim()})`;
    const primary = `rgb(${cs.getPropertyValue("--zh-primary").trim()})`;
    const dim = `rgb(${cs.getPropertyValue("--zh-text-muted").trim()})`;
    const xhairColor = "#22dd22";

    ctx.fillStyle = cardBg;
    ctx.fillRect(0, 0, W, H);

    // Screen border
    ctx.strokeStyle = dim;
    ctx.lineWidth = 1;
    ctx.strokeRect(2, 2, W - 4, H - 4);

    // Crosshair (screen center)
    const cx = W >> 1, cy = H >> 1;
    ctx.strokeStyle = xhairColor;
    ctx.lineWidth = 2;
    for (const [dx, dy] of [[-8, 0], [8, 0], [0, -8], [0, 8]]) {
      ctx.beginPath();
      ctx.moveTo(cx + dx, cy + dy);
      ctx.lineTo(cx + dx * 2, cy + dy * 2);
      ctx.stroke();
    }

    // Weapon position
    const fovScale = (68 - fov) * 0.8;
    let gx = Math.round(W * 0.72 - ox * 9 + fovScale);
    let gy = Math.round(H * 0.68 - oz * 9 + fovScale * 0.3);
    gx = Math.max(60, Math.min(W - 10, gx));
    gy = Math.max(40, Math.min(H - 10, gy));

    const scale = 1.0 + (68 - fov) * 0.03;
    const s = scale;

    ctx.fillStyle = primary;

    // Barrel
    const bx = gx - Math.round(90 * s);
    const by = gy;
    ctx.fillRect(bx, by - 3, gx - Math.round(30 * s) - bx, 6);
    // Muzzle brake
    ctx.fillRect(bx - 4, by - 5, 6, 10);
    // Upper receiver
    const rx1 = gx - Math.round(30 * s);
    const ry1 = by - Math.round(8 * s);
    const rx2 = gx + Math.round(18 * s);
    const ry2 = by + Math.round(10 * s);
    ctx.fillRect(rx1, ry1, rx2 - rx1, ry2 - ry1);
    // Pistol grip
    ctx.beginPath();
    ctx.moveTo(gx + 6 * s,  by + 10 * s);
    ctx.lineTo(gx + 18 * s, by + 10 * s);
    ctx.lineTo(gx + 20 * s, by + 28 * s);
    ctx.lineTo(gx + 8 * s,  by + 30 * s);
    ctx.closePath();
    ctx.fill();
    // Stock
    ctx.beginPath();
    ctx.moveTo(gx + 18 * s, by - 4 * s);
    ctx.lineTo(gx + 18 * s, by + 10 * s);
    ctx.lineTo(gx + 42 * s, by + 10 * s);
    ctx.lineTo(gx + 46 * s, by + 2 * s);
    ctx.lineTo(gx + 42 * s, by - 8 * s);
    ctx.closePath();
    ctx.fill();
    // Stock butt plate
    ctx.fillRect(gx + 42 * s, by - 8 * s, 6, 18 * s);
    // Magazine
    const magX = gx - 8 * s;
    ctx.beginPath();
    ctx.moveTo(magX - 8 * s, by + 10 * s);
    ctx.lineTo(magX + 8 * s, by + 10 * s);
    ctx.lineTo(magX + 6 * s, by + 32 * s);
    ctx.lineTo(magX - 6 * s, by + 32 * s);
    ctx.closePath();
    ctx.fill();
    // Sights
    ctx.fillRect(gx - 40 * s, by - 12 * s, 20 * s, 4 * s);

    // Info text
    ctx.fillStyle = dim;
    ctx.font = "10px 'Segoe UI'";
    ctx.textAlign = "center";
    ctx.fillText(`FOV: ${fov.toFixed(0)}  X: ${ox > 0 ? "+" : ""}${ox.toFixed(1)}  Z: ${oz > 0 ? "+" : ""}${oz.toFixed(1)}`, W / 2, H - 8);
  }

  $effect(() => {
    void viewmodel_fov; void viewmodel_offset_x; void viewmodel_offset_y;
    void viewmodel_offset_z; void viewmodel_presetpos;
    void cl_bob_lower_amt; void cl_bobamt_lat; void cl_bobamt_vert;
    draw();
  });

  async function saveCfg() {
    saveStatus = "";
    const vars = buildVars();
    let content = "// CS2 Viewmodel - Generated by ZeddiHub Tools\n\n";
    for (const [k, v] of Object.entries(vars)) {
      content += `${k} "${v}"\n`;
    }
    try {
      const path = await saveCfgFile(content, {
        defaultName: "cs2_viewmodel.cfg",
        title: "Uložit viewmodel.cfg",
      });
      if (path) saveStatus = `✓ Uloženo: ${path}`;
    } catch (e: any) {
      saveStatus = `✗ ${e?.message ?? e}`;
    }
  }
</script>

<div class="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-4">
  <!-- Form -->
  <div>
    <h3 class="text-lg font-bold text-zh-primary mb-1">CS2 — Viewmodel Generátor</h3>
    <p class="text-xs text-zh-text-muted mb-3">Pozice zbraně a bob.</p>

    <Card>
      <Stepper bind:value={viewmodel_fov}       label="FOV"      min={54}   max={68}  step={1}   hint="54–68" />
      <Stepper bind:value={viewmodel_offset_x}  label="Offset X" min={-2.5} max={2.5} step={0.5} hint="−2.5 – +2.5" />
      <Stepper bind:value={viewmodel_offset_y}  label="Offset Y" min={-2.5} max={2.5} step={0.5} hint="−2.5 – +2.5" />
      <Stepper bind:value={viewmodel_offset_z}  label="Offset Z" min={-2.5} max={2.5} step={0.5} hint="−2.5 – +2.5" />
      <Dropdown bind:value={viewmodel_presetpos} label="Preset"
        options={[
          { value: "1", label: "1 — Desktop" },
          { value: "2", label: "2 — Couch" },
          { value: "3", label: "3 — Classic" },
        ]}
        hint="Preset poloha"
      />
      <Stepper bind:value={cl_bob_lower_amt} label="Bob Lower" min={5}   max={30}  step={1}   hint="5–30" />
      <Stepper bind:value={cl_bobamt_lat}    label="Bob Lat"   min={0}   max={2}   step={0.1} hint="0–2" />
      <Stepper bind:value={cl_bobamt_vert}   label="Bob Vert"  min={0}   max={2}   step={0.1} hint="0–2" />
    </Card>

    <Button variant="primary" onclick={saveCfg} class="w-full mt-3">
      <Save size={14} />
      Uložit viewmodel.cfg
    </Button>

    {#if saveStatus}
      <div class="mt-2 text-xs text-zh-text-muted">{saveStatus}</div>
    {/if}

    <h4 class="text-sm font-semibold mt-5 mb-2 flex items-center gap-2">
      <Sparkles size={14} class="text-zh-primary" />
      Rychlé presety
    </h4>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
      {#each presets as p}
        <Button variant="secondary" onclick={() => applyPreset(p.vals)} class="!h-9 text-xs">
          {p.name}
        </Button>
      {/each}
    </div>
  </div>

  <!-- Preview -->
  <div>
    <Card padding={4}>
      <div class="text-xs text-zh-text-muted text-center mb-1">Náhled zbraně</div>
      <div class="text-[10px] text-zh-text-muted/70 text-center mb-2">Boční pohled — přibližné umístění</div>
      <div class="flex justify-center">
        <canvas bind:this={canvas} width={280} height={210} class="rounded-entry bg-zh-card-bg"></canvas>
      </div>
    </Card>
  </div>
</div>
