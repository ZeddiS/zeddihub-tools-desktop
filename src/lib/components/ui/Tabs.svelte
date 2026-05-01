<script lang="ts" generics="T extends string">
  /**
   * Generic horizontal tabs component.
   *
   * Use:
   *   <Tabs tabs={[{id:"a",label:"A"},{id:"b",label:"B"}]} bind:active />
   *   {#if active === "a"} … {/if}
   */

  interface Tab { id: T; label: string; icon?: any }

  let {
    tabs,
    active = $bindable(),
    onChange = undefined as undefined | ((id: T) => void),
  }: {
    tabs: Tab[];
    active: T;
    onChange?: (id: T) => void;
  } = $props();

  function setActive(id: T) {
    active = id;
    onChange?.(id);
  }
</script>

<div class="flex gap-1 border-b border-zh-border">
  {#each tabs as tab}
    {@const isActive = active === tab.id}
    <button
      class="px-4 h-10 text-sm flex items-center gap-2 border-b-2 transition"
      class:border-zh-primary={isActive}
      class:text-zh-primary={isActive}
      class:border-transparent={!isActive}
      class:text-zh-text-muted={!isActive}
      class:hover:text-zh-text={!isActive}
      onclick={() => setActive(tab.id)}
    >
      {#if tab.icon}<svelte:component this={tab.icon} size={14} />{/if}
      {tab.label}
    </button>
  {/each}
</div>
