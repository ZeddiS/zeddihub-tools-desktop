<script lang="ts">
  import { Trash2, Check } from "lucide-svelte";
  import Modal from "$components/ui/Modal.svelte";
  import Button from "$components/ui/Button.svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import { getCommandCatalog, type Game } from "$lib/data/keyboard";

  let {
    open = false,
    onClose = undefined as undefined | (() => void),
    onResult = undefined as undefined | ((cmd: string | null) => void),
    keyName = "",
    current = "",
    game = "cs2" as Game,
  }: {
    open?: boolean;
    onClose?: () => void;
    onResult?: (cmd: string | null) => void;
    keyName?: string;
    current?: string;
    game?: Game;
  } = $props();

  type Tab = "items" | "custom";
  let active = $state<Tab>("items");
  let customCmd = $state("");

  $effect(() => {
    if (open) {
      customCmd = current;
      active = "items";
    }
  });

  let modalOpen = $state(false);
  $effect(() => { modalOpen = open; });
  $effect(() => {
    if (!modalOpen && open) onClose?.();
  });

  let catalog = $derived(getCommandCatalog(game));

  function pickItem(cmd: string) {
    onResult?.(cmd);
    modalOpen = false;
  }

  function confirmCustom() {
    onResult?.(customCmd.trim());
    modalOpen = false;
  }

  function removeBinding() {
    onResult?.(null);
    modalOpen = false;
  }
</script>

<Modal bind:open={modalOpen} title={`Bind klávesy: ${keyName}`} width="max-w-2xl">
  <Tabs
    bind:active
    tabs={[
      { id: "items",  label: "Katalog" },
      { id: "custom", label: "Vlastní příkaz" },
    ]}
  />

  <div class="mt-4">
    {#if active === "items"}
      <div class="max-h-96 overflow-auto space-y-4">
        {#each catalog as cat}
          <div>
            <div class="text-xs uppercase tracking-wider text-zh-text-muted mb-1.5">{cat.title}</div>
            <div class="flex flex-wrap gap-1.5">
              {#each cat.items as item}
                <button
                  type="button"
                  class="px-2.5 h-7 rounded text-[11px] font-mono bg-zh-card-hover hover:bg-zh-primary hover:text-zh-text-dark transition"
                  onclick={() => pickItem(item)}
                >
                  {item}
                </button>
              {/each}
            </div>
          </div>
        {/each}
      </div>

    {:else}
      <div class="space-y-2">
        <label for="custom-cmd" class="text-xs text-zh-text-muted block">Vlastní bind příkaz</label>
        <input
          id="custom-cmd"
          type="text"
          bind:value={customCmd}
          placeholder="např. say hello / +jump / toggle cl_righthand 0 1"
          class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm font-mono focus:outline-none focus:border-zh-primary"
          onkeydown={(e) => { if (e.key === "Enter") { e.preventDefault(); confirmCustom(); } }}
        />
        <div class="text-[10px] text-zh-text-muted leading-relaxed pt-1">
          Můžeš použít <code class="text-zh-primary">+jump</code> stylem (held action),
          <code class="text-zh-primary">slot1</code> / <code class="text-zh-primary">slot2</code>,
          chat příkazy <code class="text-zh-primary">say !rr</code>, atd.
        </div>
        <Button variant="primary" onclick={confirmCustom} class="w-full mt-2">
          <Check size={14} />
          Uložit bind
        </Button>
      </div>
    {/if}

    {#if current}
      <div class="border-t border-zh-divider mt-4 pt-3 flex items-center justify-between text-xs">
        <span class="text-zh-text-muted">
          Aktuální bind: <code class="text-zh-text font-mono">{current}</code>
        </span>
        <Button variant="ghost" onclick={removeBinding} class="!h-7 text-[11px] !text-zh-error">
          <Trash2 size={12} />
          Odstranit
        </Button>
      </div>
    {/if}
  </div>
</Modal>
