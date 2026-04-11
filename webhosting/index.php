<?php
/**
 * ZeddiHub Tools — Public Landing Page
 * Nahrajte tento soubor do kořene vašeho webhoistingu (vedle složky /admin/).
 */

define('GITHUB_REPO',    'ZeddiS/zeddihub-tools-desktop');
define('GITHUB_RELEASE', 'https://github.com/' . GITHUB_REPO . '/releases/latest');
define('GITHUB_DL',      'https://github.com/' . GITHUB_REPO . '/releases/latest/download/ZeddiHub.Tools.exe');

// Fetch latest version from GitHub Releases (cached 10 min).
// Automatically reflects every new release — no manual update needed.
function get_latest_version(): string {
    $cache = sys_get_temp_dir() . '/zeddihub_version_cache.txt';

    // Return cached value if fresh (< 10 min)
    if (file_exists($cache) && (time() - filemtime($cache)) < 600) {
        $v = trim(file_get_contents($cache));
        if ($v) return $v;
    }

    $api_url = 'https://api.github.com/repos/' . GITHUB_REPO . '/releases/latest';
    $tag = null;

    // 1. cURL — works even when allow_url_fopen = Off (most shared hosting)
    if (function_exists('curl_init')) {
        $ch = curl_init($api_url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 4,
            CURLOPT_USERAGENT      => 'ZeddiHubTools-landing',
            CURLOPT_SSL_VERIFYPEER => true,
        ]);
        $json = curl_exec($ch);
        curl_close($ch);
        if ($json) $tag = ltrim(json_decode($json, true)['tag_name'] ?? '', 'v') ?: null;
    }

    // 2. file_get_contents fallback (requires allow_url_fopen = On)
    if (!$tag && ini_get('allow_url_fopen')) {
        $ctx = stream_context_create(['http' => [
            'timeout' => 4, 'ignore_errors' => true,
            'header'  => "User-Agent: ZeddiHubTools-landing\r\n",
        ]]);
        $json = @file_get_contents($api_url, false, $ctx);
        if ($json) $tag = ltrim(json_decode($json, true)['tag_name'] ?? '', 'v') ?: null;
    }

    // Cache successful result
    if ($tag) { @file_put_contents($cache, $tag); return $tag; }

    // 3. Last resort: local data/version.json (stale but better than nothing)
    foreach ([__DIR__ . '/../data/version.json', dirname(__DIR__) . '/data/version.json'] as $f) {
        if (file_exists($f)) {
            $data = json_decode(@file_get_contents($f), true);
            if (!empty($data['version'])) return $data['version'];
        }
    }

    return '—';
}

$version = get_latest_version();
?>
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ZeddiHub Tools — Desktop app pro správce CS2, CS:GO a Rust serverů</title>
<meta name="description" content="Zdarma ke stažení — desktop aplikace pro správce herních serverů. Crosshair generátor, RCON klient, Rust Plugin Manager, PC Tools a další.">
<style>
:root {
  --bg:       #0c0c0c;
  --bg2:      #111111;
  --card:     #1a1a1a;
  --card2:    #222222;
  --border:   #2a2a2a;
  --primary:  #f0a500;
  --primary-h:#d4900a;
  --text:     #e8e8e8;
  --text-dim: #888888;
  --text-dark:#555555;
  --success:  #22c55e;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Navbar ─────────────────────────────────────────────────────────────── */
.navbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(12,12,12,.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 700;
  color: var(--primary);
  text-decoration: none;
}
.navbar-brand:hover { text-decoration: none; }
.navbar-brand .brand-dot {
  width: 10px; height: 10px;
  background: var(--primary);
  border-radius: 50%;
  flex-shrink: 0;
}
.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.nav-link {
  font-size: 13px;
  color: var(--text-dim);
  padding: 6px 10px;
  border-radius: 6px;
  transition: color .15s, background .15s;
}
.nav-link:hover { color: var(--text); background: var(--card); text-decoration: none; }
.btn-admin {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  padding: 7px 16px;
  border-radius: 6px;
  transition: background .15s, border-color .15s;
}
.btn-admin:hover { background: var(--card2); border-color: var(--primary); color: var(--primary); text-decoration: none; }

/* ── Hero ───────────────────────────────────────────────────────────────── */
.hero {
  text-align: center;
  padding: 96px 24px 80px;
  max-width: 720px;
  margin: 0 auto;
}
.hero-badge {
  display: inline-block;
  background: #1a1200;
  border: 1px solid #3a2a00;
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  padding: 4px 14px;
  border-radius: 20px;
  margin-bottom: 20px;
  letter-spacing: .04em;
}
.hero-title {
  font-size: clamp(32px, 6vw, 56px);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -.02em;
  margin-bottom: 20px;
}
.hero-title .highlight { color: var(--primary); }
.hero-sub {
  font-size: 17px;
  color: var(--text-dim);
  max-width: 540px;
  margin: 0 auto 36px;
  line-height: 1.7;
}
.hero-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
.btn-download {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--primary);
  color: #0c0c0c;
  font-size: 15px;
  font-weight: 700;
  padding: 13px 28px;
  border-radius: 8px;
  transition: background .15s, transform .1s;
  text-decoration: none;
}
.btn-download:hover { background: var(--primary-h); text-decoration: none; transform: translateY(-1px); }
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--text);
  font-size: 15px;
  font-weight: 600;
  padding: 13px 28px;
  border-radius: 8px;
  border: 1px solid var(--border);
  transition: border-color .15s, background .15s;
}
.btn-outline:hover { border-color: var(--primary); background: #1a1200; color: var(--primary); text-decoration: none; }

.hero-meta {
  margin-top: 20px;
  font-size: 12px;
  color: var(--text-dark);
}
.hero-meta span { margin: 0 8px; }

/* ── Section ────────────────────────────────────────────────────────────── */
section {
  padding: 72px 24px;
  max-width: 1100px;
  margin: 0 auto;
}
.section-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--primary);
  margin-bottom: 10px;
}
.section-title {
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 700;
  margin-bottom: 12px;
  letter-spacing: -.01em;
}
.section-sub {
  font-size: 15px;
  color: var(--text-dim);
  max-width: 560px;
  margin-bottom: 48px;
}
.divider-line {
  border: none;
  border-top: 1px solid var(--border);
}

/* ── Features grid ──────────────────────────────────────────────────────── */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.feature-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  transition: border-color .2s, transform .2s;
}
.feature-card:hover {
  border-color: #3a2a00;
  transform: translateY(-2px);
}
.feature-icon {
  font-size: 26px;
  margin-bottom: 10px;
  display: block;
}
.feature-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text);
}
.feature-desc {
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.55;
}

/* ── Steps ──────────────────────────────────────────────────────────────── */
.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  counter-reset: steps;
}
.step {
  position: relative;
  padding-left: 48px;
  counter-increment: steps;
}
.step::before {
  content: counter(steps);
  position: absolute;
  left: 0; top: 0;
  width: 32px; height: 32px;
  background: #1a1200;
  border: 1px solid #3a2a00;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  line-height: 32px;
  text-align: center;
}
.step-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text);
}
.step-desc {
  font-size: 13px;
  color: var(--text-dim);
}

/* ── CTA ────────────────────────────────────────────────────────────────── */
.cta-section {
  padding: 80px 24px;
  text-align: center;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--bg2);
}
.cta-title {
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 700;
  margin-bottom: 12px;
}
.cta-sub {
  font-size: 15px;
  color: var(--text-dim);
  margin-bottom: 32px;
}

/* ── Footer ─────────────────────────────────────────────────────────────── */
footer {
  padding: 32px 24px;
  text-align: center;
  font-size: 12px;
  color: var(--text-dark);
  border-top: 1px solid var(--border);
}
footer a { color: var(--text-dim); }
footer a:hover { color: var(--primary); text-decoration: none; }
.footer-links { display: flex; gap: 20px; justify-content: center; margin-bottom: 12px; flex-wrap: wrap; }

/* ── Version tag ────────────────────────────────────────────────────────── */
.version-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #0a2010;
  border: 1px solid #166534;
  color: var(--success);
  font-size: 12px;
  font-weight: 600;
  padding: 3px 12px;
  border-radius: 20px;
  margin-left: 8px;
  vertical-align: middle;
}

@media (max-width: 600px) {
  .hero { padding: 64px 16px 56px; }
  section { padding: 48px 16px; }
  .navbar { padding: 0 16px; }
}
</style>
</head>
<body>

<!-- ── Navbar ──────────────────────────────────────────────────────────── -->
<nav class="navbar">
  <a href="#" class="navbar-brand">
    <div class="brand-dot"></div>
    ZeddiHub Tools
  </a>
  <div class="navbar-right">
    <a href="#features" class="nav-link">Funkce</a>
    <a href="#start" class="nav-link">Ke stažení</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener" class="nav-link">Discord</a>
    <a href="admin/" class="btn-admin">
      🔐 Admin panel
    </a>
  </div>
</nav>

<!-- ── Hero ──────────────────────────────────────────────────────────────── -->
<div class="hero">
  <div class="hero-badge">
    ✦ Aktuální verze: v<?= htmlspecialchars($version) ?>
  </div>
  <h1 class="hero-title">
    Desktop nástroje pro<br>
    <span class="highlight">herní servery</span>
  </h1>
  <p class="hero-sub">
    Vše, co potřebujete jako správce CS2, CS:GO nebo Rust serveru, na jednom místě.
    Bez instalace, bez Pythonu — stáhnout a spustit.
  </p>
  <div class="hero-actions">
    <a href="<?= GITHUB_DL ?>" class="btn-download">
      ⬇ Stáhnout ZeddiHub.Tools.exe
    </a>
    <a href="<?= GITHUB_RELEASE ?>" target="_blank" rel="noopener" class="btn-outline">
      📋 Všechny verze
    </a>
  </div>
  <p class="hero-meta">
    <span>🪟 Windows 10 / 11</span>
    <span>·</span>
    <span>🆓 Zdarma</span>
    <span>·</span>
    <span>⚡ Bez instalace</span>
  </p>
</div>

<hr class="divider-line">

<!-- ── Features ──────────────────────────────────────────────────────────── -->
<section id="features">
  <div class="section-label">Co aplikace umí</div>
  <h2 class="section-title">Všechny nástroje na jednom místě</h2>
  <p class="section-sub">Všechny sekce v jednom okně, přepínání jedním klikem.</p>

  <div class="features-grid">
    <div class="feature-card">
      <span class="feature-icon">🎯</span>
      <div class="feature-name">Crosshair Generator</div>
      <div class="feature-desc">Live náhled, úprava všech parametrů a export kódu přímo pro CS2 / CS:GO.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">🔫</span>
      <div class="feature-name">Viewmodel Editor</div>
      <div class="feature-desc">Nastavení zbraně ve hře s náhledem hodnot v reálném čase.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">📄</span>
      <div class="feature-name">Autoexec Editor</div>
      <div class="feature-desc">Úprava konfiguračního souboru přímo v aplikaci, bez hledání v souborovém systému.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">⚙️</span>
      <div class="feature-name">Server CFG Generator</div>
      <div class="feature-desc">Vytvoření serverové konfigurace klikáním — pro CS2 i Rust.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">📡</span>
      <div class="feature-name">RCON Klient</div>
      <div class="feature-desc">Vzdálená správa serveru přes RCON přímo z aplikace. Bez externích programů.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">⌨️</span>
      <div class="feature-name">Keybind Generator</div>
      <div class="feature-desc">Vizuální klávesnice — přiřaďte příkazy kliknutím na klávesy.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">🛒</span>
      <div class="feature-name">Buy Binds</div>
      <div class="feature-desc">Nákupní zkratky pro CS2 / CS:GO s rychlým exportem do configu.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">🦀</span>
      <div class="feature-name">Rust Plugin Manager</div>
      <div class="feature-desc">Dávková oprava pluginů, analýza závislostí a správa Oxide / uMod pluginů.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">🌐</span>
      <div class="feature-name">Translator</div>
      <div class="feature-desc">Překlad JSON / TXT / LANG souborů do 20+ jazyků pomocí AI překladu.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">💻</span>
      <div class="feature-name">PC Tools</div>
      <div class="feature-desc">Informace o systému (CPU, GPU, RAM, disky), DNS flush, čištění temp souborů, ping tester.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">🏠</span>
      <div class="feature-name">Live Server Status</div>
      <div class="feature-desc">Domovská stránka s live stavem serverů (hráči, mapa, ping) přes Steam A2S query.</div>
    </div>
    <div class="feature-card">
      <span class="feature-icon">🔄</span>
      <div class="feature-name">Automatické aktualizace</div>
      <div class="feature-desc">Aplikace při spuštění zkontroluje GitHub a nabídne aktualizaci — bez prohlížeče.</div>
    </div>
  </div>
</section>

<hr class="divider-line">

<!-- ── Getting started ───────────────────────────────────────────────────── -->
<section id="start">
  <div class="section-label">Rychlý start</div>
  <h2 class="section-title">Hotovo za 3 kroky</h2>
  <p class="section-sub">Žádná instalace, žádný Python. Stáhnout a spustit.</p>

  <div class="steps">
    <div class="step">
      <div class="step-title">Stáhnout .exe</div>
      <div class="step-desc">Stáhněte <code>ZeddiHub.Tools.exe</code> z nejnovější verze na GitHubu níže.</div>
    </div>
    <div class="step">
      <div class="step-title">Spustit</div>
      <div class="step-desc">Žádná instalace. Při prvním spuštění zvolte jazyk a složku pro data.</div>
    </div>
    <div class="step">
      <div class="step-title">Přihlásit se</div>
      <div class="step-desc">Zadejte přihlašovací údaje nebo přístupový kód pro odemčení server tools.</div>
    </div>
    <div class="step">
      <div class="step-title">Hotovo</div>
      <div class="step-desc">Aplikace běží na pozadí v systémové liště. Přistupte kdykoli pravým klikem na ikonu.</div>
    </div>
  </div>

</section>

<!-- ── CTA ───────────────────────────────────────────────────────────────── -->
<div class="cta-section">
  <h2 class="cta-title">Stáhněte si ZeddiHub Tools zdarma</h2>
  <p class="cta-sub">
    Aktuální verze: <strong>v<?= htmlspecialchars($version) ?></strong> &nbsp;·&nbsp; Windows 10 / 11 &nbsp;·&nbsp; Zdarma
  </p>
  <div class="hero-actions">
    <a href="<?= GITHUB_DL ?>" class="btn-download">
      ⬇ Stáhnout .exe
    </a>
    <a href="<?= GITHUB_RELEASE ?>" target="_blank" rel="noopener" class="btn-outline">
      📋 Releases na GitHubu
    </a>
  </div>
</div>

<!-- ── Footer ────────────────────────────────────────────────────────────── -->
<footer>
  <div class="footer-links">
    <a href="https://zeddihub.eu">zeddihub.eu</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener">Discord</a>
    <a href="https://github.com/<?= GITHUB_REPO ?>" target="_blank" rel="noopener">GitHub</a>
    <a href="admin/">Admin panel</a>
  </div>
  <p>Made by <strong>ZeddiS</strong> &nbsp;·&nbsp; ZeddiHub Tools <?php if ($version !== '—') echo 'v' . htmlspecialchars($version); ?></p>
</footer>

</body>
</html>
