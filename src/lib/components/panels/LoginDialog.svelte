<script lang="ts">
  /**
   * Login + Register modal dialog.
   *
   * Use:
   *   <LoginDialog bind:open onSuccess={() => goto('/')} />
   *
   * Triggered from:
   *   - Header auth pill (when not authenticated)
   *   - HomePanel "Login" button
   *   - Sidebar locked nav item click (auth-required panels)
   */

  import { KeyRound, UserPlus, ExternalLink } from "lucide-svelte";
  import Modal from "$components/ui/Modal.svelte";
  import Tabs from "$components/ui/Tabs.svelte";
  import Button from "$components/ui/Button.svelte";
  import { auth } from "$stores/auth";
  import { t } from "$stores/locale";
  import { open as openUrl } from "@tauri-apps/plugin-shell";

  let {
    open = false,
    onClose = undefined as undefined | (() => void),
    onSuccess = undefined as undefined | (() => void),
  }: {
    open?: boolean;
    onClose?: () => void;
    onSuccess?: () => void;
  } = $props();

  // Local mirror so internal Modal can drive close; we then notify parent.
  let modalOpen = $state(false);
  $effect(() => { modalOpen = open; });
  $effect(() => {
    if (!modalOpen && open) {
      onClose?.();
    }
  });

  type Tab = "login" | "register";
  let active = $state<Tab>("login");

  // Login state
  let loginIdent = $state("");
  let loginPass = $state("");

  // Register state
  let regUser = $state("");
  let regEmail = $state("");
  let regPass = $state("");
  let regPass2 = $state("");
  let regError = $state("");

  let busy = $state(false);

  async function doLogin(e?: Event) {
    e?.preventDefault();
    if (busy || !loginIdent || !loginPass) return;
    busy = true;
    auth.clearError();
    const ok = await auth.login(loginIdent, loginPass);
    busy = false;
    if (ok) {
      loginIdent = "";
      loginPass = "";
      modalOpen = false;
      onSuccess?.();
    }
  }

  async function doRegister(e?: Event) {
    e?.preventDefault();
    regError = "";
    if (busy) return;
    if (!regUser || !regEmail || !regPass) {
      regError = "Vyplňte všechna pole.";
      return;
    }
    if (regPass !== regPass2) {
      regError = "Hesla se neshodují.";
      return;
    }
    if (regPass.length < 8) {
      regError = "Heslo musí mít alespoň 8 znaků.";
      return;
    }
    busy = true;
    auth.clearError();
    const ok = await auth.register(regUser, regEmail, regPass);
    busy = false;
    if (ok) {
      regUser = regEmail = regPass = regPass2 = "";
      modalOpen = false;
      onSuccess?.();
    }
  }
</script>

<Modal bind:open={modalOpen} title={active === "login" ? $t("auth_login") : $t("auth_register")} width="max-w-md">
  <Tabs
    bind:active
    tabs={[
      { id: "login",    label: $t("auth_login"),    icon: KeyRound },
      { id: "register", label: $t("auth_register"), icon: UserPlus },
    ]}
  />

  <div class="mt-4">
    {#if $auth.error}
      <div class="text-xs text-zh-error bg-zh-error/10 border border-zh-error/30 rounded-button px-3 py-2 mb-3">
        {$auth.error}
      </div>
    {/if}

    {#if active === "login"}
      <form onsubmit={doLogin} class="space-y-3">
        <div>
          <label for="li-ident" class="text-xs text-zh-text-muted block mb-1">
            {$t("auth_username")} / e-mail
          </label>
          <input
            id="li-ident"
            bind:value={loginIdent}
            autocomplete="username"
            required
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
          />
        </div>
        <div>
          <label for="li-pwd" class="text-xs text-zh-text-muted block mb-1">{$t("auth_password")}</label>
          <input
            id="li-pwd"
            type="password"
            bind:value={loginPass}
            autocomplete="current-password"
            required
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
          />
        </div>
        <Button variant="primary" type="submit" disabled={busy} class="w-full">
          <KeyRound size={14} />
          {busy ? "…" : $t("auth_login")}
        </Button>
      </form>

    {:else}
      <form onsubmit={doRegister} class="space-y-3">
        {#if regError}
          <div class="text-xs text-zh-warning bg-zh-warning/10 border border-zh-warning/30 rounded-button px-3 py-2">
            {regError}
          </div>
        {/if}
        <div>
          <label for="ri-user" class="text-xs text-zh-text-muted block mb-1">{$t("auth_username")}</label>
          <input
            id="ri-user"
            bind:value={regUser}
            placeholder="3–24 znaků, A–Z 0–9 . _ -"
            autocomplete="username"
            required
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
          />
        </div>
        <div>
          <label for="ri-email" class="text-xs text-zh-text-muted block mb-1">{$t("auth_email")}</label>
          <input
            id="ri-email"
            type="email"
            bind:value={regEmail}
            autocomplete="email"
            required
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
          />
        </div>
        <div>
          <label for="ri-pwd" class="text-xs text-zh-text-muted block mb-1">{$t("auth_password")}</label>
          <input
            id="ri-pwd"
            type="password"
            bind:value={regPass}
            placeholder="min. 8 znaků"
            autocomplete="new-password"
            required
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
          />
        </div>
        <div>
          <label for="ri-pwd2" class="text-xs text-zh-text-muted block mb-1">Heslo (znovu)</label>
          <input
            id="ri-pwd2"
            type="password"
            bind:value={regPass2}
            autocomplete="new-password"
            required
            class="w-full bg-zh-card-hover border border-zh-border rounded-entry px-3 h-10 text-sm focus:outline-none focus:border-zh-primary"
          />
        </div>
        <Button variant="primary" type="submit" disabled={busy} class="w-full">
          <UserPlus size={14} />
          {busy ? "…" : $t("auth_register")}
        </Button>
      </form>
    {/if}

    <div class="mt-4 pt-3 border-t border-zh-divider text-[11px] text-zh-text-muted text-center">
      Účet je sdílený s
      <button class="text-zh-primary hover:underline inline-flex items-center gap-1" onclick={() => openUrl("https://zeddihub.eu/tools/user/")}>
        zeddihub.eu/tools/user
        <ExternalLink size={9} />
      </button>
    </div>
  </div>
</Modal>
