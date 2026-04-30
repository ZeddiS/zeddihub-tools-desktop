// ZeddiHub Tools — Tauri PoC frontend.
// Vanilla JS, žádný framework — ať PoC zůstane minimal a srozumitelný.
// V reálné aplikaci by tu bylo React / Svelte / Vue / Solid / atd.

import { invoke } from "@tauri-apps/api/core";

// ── Fallback data (offline) ──────────────────────────
const FALLBACK_RECOMMENDED = [
  { name: "CS2 Crosshair", desc: "Vygeneruj svůj crosshair", color: "#5b9cf6" },
  { name: "CS2 Server CFG", desc: "Nastavení herního serveru", color: "#5b9cf6" },
  { name: "CS:GO Crosshair", desc: "CS:GO crosshair generátor", color: "#fbbf24" },
  { name: "Rust Server CFG", desc: "Konfiguruj Rust server", color: "#f97316" },
  { name: "Keybind Generator", desc: "Vizuální keybind editor", color: "#a78bfa" },
  { name: "Translator", desc: "Hromadný překlad .json/.lang", color: "#4ade80" },
];

// ── Panels ───────────────────────────────────────────
function renderHome(items, status) {
  const cards = items
    .slice(0, 6)
    .map(
      (it) => `
      <div class="card">
        <div class="card__strip" style="background:${it.color || "var(--primary)"}"></div>
        <h3 class="card__name">${escapeHtml(it.name || "")}</h3>
        <p class="card__desc">${escapeHtml(it.desc || "")}</p>
      </div>`
    )
    .join("");

  return `
    <h1 class="panel-title">Vítej zpět</h1>
    <p class="panel-subtitle">Doporučené nástroje pro rychlý přístup.</p>
    <p class="panel-status" id="home-status">${status}</p>
    <div class="cards-grid">${cards}</div>
  `;
}

function renderSettings() {
  return `
    <h1 class="panel-title">Nastavení</h1>
    <div class="form-card">
      <div class="form-section">Vzhled</div>
      <button class="btn" id="theme-toggle-2">Přepnout dark / light</button>

      <div class="form-section">Účet</div>
      <div class="input-row">
        <label>Uživatelské jméno:</label>
        <input type="text" placeholder="zeddi…" />
      </div>
      <div class="input-row">
        <label>E-mail:</label>
        <input type="email" placeholder="user@example.com" />
      </div>
    </div>

    <div class="form-card">
      <div class="form-section">Backend test</div>
      <p class="panel-subtitle">Zavoláme Rust funkci přes Tauri IPC:</p>
      <button class="btn" id="rust-call">Zeptat se Rust backendu</button>
      <p class="panel-status" id="rust-status">…</p>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ── Navigation / state ───────────────────────────────
let currentNav = "home";
const content = document.getElementById("content");

function navigate(navId) {
  currentNav = navId;
  document.querySelectorAll(".zh-nav").forEach((b) => {
    b.classList.toggle("active", b.dataset.nav === navId);
  });

  if (navId === "home") {
    content.innerHTML = renderHome(FALLBACK_RECOMMENDED, "Načítám doporučené nástroje…");
    fetchRecommended();
  } else if (navId === "settings") {
    content.innerHTML = renderSettings();
    document.getElementById("theme-toggle-2")?.addEventListener("click", toggleTheme);
    document.getElementById("rust-call")?.addEventListener("click", callRust);
  }
}

// ── Data fetching (přes Rust backend) ────────────────
async function fetchRecommended() {
  try {
    const items = await invoke("fetch_recommended");
    if (Array.isArray(items) && items.length > 0) {
      content.innerHTML = renderHome(items, `✓ ${items.length} nástrojů (live ze zeddihub.eu, fetched in Rust)`);
    } else {
      const status = document.getElementById("home-status");
      if (status) status.textContent = "⚠ Offline — zobrazen fallback";
    }
  } catch (e) {
    const status = document.getElementById("home-status");
    if (status) status.textContent = "⚠ Chyba: " + e;
  }
}

async function callRust() {
  const status = document.getElementById("rust-status");
  status.textContent = "Volám Rust…";
  try {
    const sysinfo = await invoke("get_system_info");
    status.textContent = `✓ ${sysinfo}`;
  } catch (e) {
    status.textContent = "✗ " + e;
  }
}

// ── Theme toggle ─────────────────────────────────────
function toggleTheme() {
  const cur = document.body.dataset.theme || "dark";
  document.body.dataset.theme = cur === "dark" ? "light" : "dark";
  document.getElementById("theme-toggle").textContent =
    document.body.dataset.theme === "dark" ? "🌙" : "☀";
}

// ── Init ─────────────────────────────────────────────
document.querySelectorAll(".zh-nav").forEach((btn) => {
  btn.addEventListener("click", () => navigate(btn.dataset.nav));
});
document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

// Boot to home
navigate("home");
