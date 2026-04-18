<?php
/**
 * ZeddiHub Tools — Public Landing Page
 * Nahrajte tento soubor do kořene webhoistingu (vedle složky /admin/).
 */

define('GITHUB_REPO',    'ZeddiS/zeddihub-tools-desktop');
define('GITHUB_RELEASE', 'https://github.com/' . GITHUB_REPO . '/releases/latest');
define('GITHUB_DL',      'https://github.com/' . GITHUB_REPO . '/releases/latest/download/ZeddiHub.Tools.exe');

function get_latest_version(): string {
    $cache = sys_get_temp_dir() . '/zeddihub_version_cache.txt';
    if (file_exists($cache) && (time() - filemtime($cache)) < 600) {
        $v = trim(file_get_contents($cache));
        if ($v) return $v;
    }
    $api_url = 'https://api.github.com/repos/' . GITHUB_REPO . '/releases/latest';
    $tag = null;
    if (function_exists('curl_init')) {
        $ch = curl_init($api_url);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>4,CURLOPT_USERAGENT=>'ZeddiHubTools-landing',CURLOPT_SSL_VERIFYPEER=>true]);
        $json = curl_exec($ch); curl_close($ch);
        if ($json) $tag = ltrim(json_decode($json,true)['tag_name']??'','v')?:null;
    }
    if (!$tag && ini_get('allow_url_fopen')) {
        $ctx = stream_context_create(['http'=>['timeout'=>4,'ignore_errors'=>true,'header'=>"User-Agent: ZeddiHubTools-landing\r\n"]]);
        $json = @file_get_contents($api_url,false,$ctx);
        if ($json) $tag = ltrim(json_decode($json,true)['tag_name']??'','v')?:null;
    }
    if ($tag) { @file_put_contents($cache,$tag); return $tag; }
    foreach ([__DIR__.'/../data/version.json',dirname(__DIR__).'/data/version.json'] as $f) {
        if (file_exists($f)) { $d=json_decode(@file_get_contents($f),true); if(!empty($d['version'])) return $d['version']; }
    }
    return '—';
}

$version = get_latest_version();
?>
<!DOCTYPE html>
<html lang="cs" data-lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ZeddiHub Tools — Desktop nástroje pro hráče</title>
<meta name="description" content="Zdarma ke stažení — desktop aplikace pro hráče a správce CS2, CS:GO a Rust serverů.">
<link rel="icon" type="image/x-icon" href="assets/web_favicon.ico">
<link rel="shortcut icon" type="image/x-icon" href="assets/web_favicon.ico">
<link rel="apple-touch-icon" href="assets/logo.png">
<style>
:root {
  --bg:       #080810;
  --bg2:      #0e0e18;
  --card:     #14141f;
  --card2:    #1c1c2a;
  --border:   #252535;
  --primary:  #f0a500;
  --primary-h:#d4900a;
  --primary-glow: rgba(240,165,0,.15);
  --text:     #eeeef5;
  --text-dim: #8888aa;
  --text-dark:#44445a;
  --success:  #22c55e;
  --cs2:      #5b9cf6;
  --csgo:     #fbbf24;
  --rust:     #f97316;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;overflow-x:hidden}
a{color:var(--primary);text-decoration:none}
a:hover{text-decoration:underline}
code{background:var(--card2);padding:2px 7px;border-radius:4px;font-size:.85em;color:var(--text-dim)}

/* ── Navbar ─── */
.navbar{
  position:sticky;top:0;z-index:100;
  background:rgba(8,8,16,.88);
  backdrop-filter:blur(14px);
  border-bottom:1px solid var(--border);
  padding:0 28px;height:58px;
  display:flex;align-items:center;justify-content:space-between;
}
.navbar-brand{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:700;color:var(--primary)}
.navbar-brand:hover{text-decoration:none}
.brand-dot{width:9px;height:9px;background:var(--primary);border-radius:50%;box-shadow:0 0 8px var(--primary)}
.navbar-logo{height:34px;width:auto;display:block;image-rendering:auto;image-rendering:-webkit-optimize-contrast;filter:none;object-fit:contain}
.hero-banner{display:block;max-width:340px;width:100%;height:auto;margin:0 auto 32px;image-rendering:auto;image-rendering:-webkit-optimize-contrast;filter:none;object-fit:contain}
.navbar-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.nav-link{font-size:13px;color:var(--text-dim);padding:6px 10px;border-radius:6px;transition:color .15s,background .15s}
.nav-link:hover{color:var(--text);background:var(--card);text-decoration:none}
.btn-lang{
  font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;
  background:var(--card2);border:1px solid var(--border);color:var(--text-dim);
  cursor:pointer;transition:all .15s;
}
.btn-lang:hover{color:var(--text);border-color:var(--primary)}
.btn-admin{
  display:inline-flex;align-items:center;gap:6px;
  background:var(--card);border:1px solid var(--border);color:var(--text);
  font-size:13px;font-weight:600;padding:7px 16px;border-radius:6px;
  transition:background .15s,border-color .15s;
}
.btn-admin:hover{background:var(--card2);border-color:var(--primary);color:var(--primary);text-decoration:none}

/* ── Animations ─── */
@keyframes fadeUp{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:translateY(0)}}
@keyframes glow{0%,100%{box-shadow:0 0 20px var(--primary-glow)}50%{box-shadow:0 0 40px var(--primary-glow)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.anim{opacity:0;animation:fadeUp .6s ease forwards}
.anim:nth-child(1){animation-delay:.05s}
.anim:nth-child(2){animation-delay:.12s}
.anim:nth-child(3){animation-delay:.19s}
.anim:nth-child(4){animation-delay:.26s}
.anim:nth-child(5){animation-delay:.33s}
.anim:nth-child(6){animation-delay:.40s}
.reveal{opacity:0;transform:translateY(20px);transition:opacity .5s ease,transform .5s ease}
.reveal.visible{opacity:1;transform:none}

/* ── Hero ─── */
.hero{
  text-align:center;padding:100px 24px 88px;
  max-width:760px;margin:0 auto;
  position:relative;
}
.hero-glow{
  position:absolute;top:0;left:50%;transform:translateX(-50%);
  width:600px;height:300px;
  background:radial-gradient(ellipse at center, var(--primary-glow) 0%, transparent 70%);
  pointer-events:none;z-index:0;
}
.hero>*{position:relative;z-index:1}
.hero-badge{
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(135deg,#1a1200,#1a1000);
  border:1px solid #3a2a00;color:var(--primary);
  font-size:12px;font-weight:700;padding:5px 16px;
  border-radius:20px;margin-bottom:24px;letter-spacing:.05em;
  animation:glow 3s ease-in-out infinite;
}
.badge-dot{width:6px;height:6px;background:var(--success);border-radius:50%;animation:pulse 2s ease-in-out infinite}
.hero-title{
  font-size:clamp(34px,6.5vw,62px);font-weight:900;
  line-height:1.12;letter-spacing:-.025em;margin-bottom:22px;
}
.hero-title .highlight{
  background:linear-gradient(135deg, var(--primary) 0%, #ff6b00 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.hero-sub{font-size:17px;color:var(--text-dim);max-width:560px;margin:0 auto 38px;line-height:1.75}
.hero-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.btn-download{
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(135deg,var(--primary),#ff8c00);
  color:#0c0c0c;font-size:15px;font-weight:700;
  padding:14px 30px;border-radius:9px;
  transition:transform .15s,box-shadow .15s;
  box-shadow:0 4px 20px rgba(240,165,0,.3);
}
.btn-download:hover{text-decoration:none;transform:translateY(-2px);box-shadow:0 6px 28px rgba(240,165,0,.4)}
.btn-outline{
  display:inline-flex;align-items:center;gap:8px;
  background:transparent;color:var(--text);font-size:15px;font-weight:600;
  padding:14px 30px;border-radius:9px;border:1px solid var(--border);
  transition:border-color .15s,background .15s;
}
.btn-outline:hover{border-color:var(--primary);background:var(--primary-glow);color:var(--primary);text-decoration:none}
.hero-meta{margin-top:22px;font-size:12px;color:var(--text-dark);display:flex;gap:16px;justify-content:center;flex-wrap:wrap}
.hero-meta span{display:flex;align-items:center;gap:5px}

/* ── Game badges ─── */
.game-badges{display:flex;gap:10px;justify-content:center;margin-top:32px;flex-wrap:wrap}
.game-badge{
  padding:6px 16px;border-radius:20px;font-size:12px;font-weight:700;
  border:1px solid;letter-spacing:.04em;
}
.badge-cs2{background:#0c1535;border-color:#253a7a;color:var(--cs2)}
.badge-csgo{background:#1a1400;border-color:#4a3800;color:var(--csgo)}
.badge-rust{background:#1a0a00;border-color:#4a2200;color:var(--rust)}

/* ── Divider ─── */
.divider-line{border:none;border-top:1px solid var(--border)}

/* ── Sections ─── */
section{padding:80px 24px;max-width:1140px;margin:0 auto}
.section-label{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.12em;color:var(--primary);margin-bottom:10px}
.section-title{font-size:clamp(26px,4vw,40px);font-weight:800;margin-bottom:12px;letter-spacing:-.02em}
.section-sub{font-size:15px;color:var(--text-dim);max-width:580px;margin-bottom:48px;line-height:1.7}

/* ── Features ─── */
.features-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.feature-card{
  background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:22px 20px;transition:border-color .2s,transform .2s,box-shadow .2s;
  position:relative;overflow:hidden;
}
.feature-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--fc,var(--primary)),transparent);
  opacity:0;transition:opacity .2s;
}
.feature-card:hover{border-color:var(--fc,var(--primary));transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.4)}
.feature-card:hover::before{opacity:1}
.feature-icon{font-size:24px;margin-bottom:12px;display:block}
.feature-name{font-size:14px;font-weight:700;margin-bottom:6px;color:var(--text)}
.feature-desc{font-size:12px;color:var(--text-dim);line-height:1.6}
.tag-game{
  display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;
  border-radius:4px;margin-top:8px;border:1px solid;
}

/* ── Steps ─── */
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:28px;counter-reset:steps}
.step{position:relative;padding-left:52px;counter-increment:steps}
.step::before{
  content:counter(steps);position:absolute;left:0;top:0;
  width:34px;height:34px;background:linear-gradient(135deg,#1a1200,#1a0800);
  border:1px solid #3a2a00;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:800;color:var(--primary);line-height:34px;text-align:center;
}
.step-title{font-size:15px;font-weight:700;margin-bottom:6px;color:var(--text)}
.step-desc{font-size:13px;color:var(--text-dim);line-height:1.6}

/* ── CTA ─── */
.cta-section{
  padding:88px 24px;text-align:center;
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
  background:linear-gradient(180deg,var(--bg2) 0%,var(--bg) 100%);
  position:relative;overflow:hidden;
}
.cta-section::before{
  content:'';position:absolute;top:-100px;left:50%;transform:translateX(-50%);
  width:800px;height:300px;
  background:radial-gradient(ellipse,var(--primary-glow) 0%,transparent 65%);
  pointer-events:none;
}
.cta-section>*{position:relative}
.cta-title{font-size:clamp(26px,4vw,42px);font-weight:900;margin-bottom:14px;letter-spacing:-.02em}
.cta-sub{font-size:15px;color:var(--text-dim);margin-bottom:36px}
.version-pill{
  display:inline-flex;align-items:center;gap:6px;
  background:#0a2010;border:1px solid #166534;color:var(--success);
  font-size:12px;font-weight:700;padding:3px 12px;border-radius:20px;
}

/* ── Footer ─── */
footer{padding:36px 24px;text-align:center;font-size:12px;color:var(--text-dark);border-top:1px solid var(--border)}
footer a{color:var(--text-dim)}
footer a:hover{color:var(--primary);text-decoration:none}
.footer-links{display:flex;gap:24px;justify-content:center;margin-bottom:12px;flex-wrap:wrap}

@media(max-width:640px){
  .hero{padding:72px 16px 60px}
  section{padding:52px 16px}
  .navbar{padding:0 16px}
  .btn-download,.btn-outline{font-size:14px;padding:12px 22px}
}
</style>
</head>
<body>

<!-- ── Navbar ── -->
<nav class="navbar">
  <a href="#" class="navbar-brand">
    <img src="assets/logo2.png" alt="ZeddiHub Tools" class="navbar-logo">
  </a>
  <div class="navbar-right">
    <a href="#features" class="nav-link" data-cs="Funkce" data-en="Features">Funkce</a>
    <a href="#start" class="nav-link" data-cs="Ke stažení" data-en="Download">Ke stažení</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener" class="nav-link">Discord</a>
    <button class="btn-lang" onclick="toggleLang()" id="langBtn">🇬🇧 EN</button>
    <a href="admin/" class="btn-admin">🔐 Admin</a>
  </div>
</nav>

<!-- ── Hero ── -->
<div class="hero">
  <div class="hero-glow"></div>
  <img src="assets/banner.png" alt="ZeddiHub Tools" class="hero-banner anim">
  <div class="hero-badge anim">
    <span class="badge-dot"></span>
    <span data-cs="Aktuální verze: v<?= htmlspecialchars($version) ?>" data-en="Latest version: v<?= htmlspecialchars($version) ?>">
      Aktuální verze: v<?= htmlspecialchars($version) ?>
    </span>
  </div>
  <h1 class="hero-title anim">
    Desktop nástroje<br>
    pro <span class="highlight" data-cs="hráče" data-en="gamers">hráče</span>
  </h1>
  <p class="hero-sub anim" data-cs="Vše, co potřebuješ jako hráč nebo správce CS2, CS:GO či Rust serveru, na jednom místě. Bez instalace, bez Pythonu." data-en="Everything you need as a player or CS2, CS:GO, or Rust server admin — in one place. No installation, no Python.">
    Vše, co potřebuješ jako hráč nebo správce CS2, CS:GO či Rust serveru, na jednom místě. Bez instalace, bez Pythonu.
  </p>
  <div class="hero-actions anim">
    <a href="<?= GITHUB_DL ?>" class="btn-download">
      ⬇ <span data-cs="Stáhnout ZeddiHub.Tools.exe" data-en="Download ZeddiHub.Tools.exe">Stáhnout ZeddiHub.Tools.exe</span>
    </a>
    <a href="<?= GITHUB_RELEASE ?>" target="_blank" rel="noopener" class="btn-outline">
      📋 <span data-cs="Všechny verze" data-en="All releases">Všechny verze</span>
    </a>
  </div>
  <div class="hero-meta anim">
    <span>🪟 <span data-cs="Windows 10 / 11" data-en="Windows 10 / 11">Windows 10 / 11</span></span>
    <span>🆓 <span data-cs="Zdarma" data-en="Free">Zdarma</span></span>
    <span>⚡ <span data-cs="Bez instalace" data-en="No installation">Bez instalace</span></span>
    <span>🌍 <span data-cs="CZ / EN interface" data-en="CZ / EN interface">CZ / EN interface</span></span>
  </div>
  <div class="game-badges anim">
    <span class="game-badge badge-cs2">Counter-Strike 2</span>
    <span class="game-badge badge-csgo">CS:GO</span>
    <span class="game-badge badge-rust">Rust</span>
  </div>
</div>

<hr class="divider-line">

<!-- ── Features ── -->
<section id="features">
  <div class="section-label reveal" data-cs="Co aplikace umí" data-en="What the app can do">Co aplikace umí</div>
  <h2 class="section-title reveal" data-cs="Všechny nástroje na jednom místě" data-en="All tools in one place">Všechny nástroje na jednom místě</h2>
  <p class="section-sub reveal" data-cs="Všechny sekce v jednom okně, přepínání jedním klikem." data-en="All sections in one window, switch with a single click.">Všechny sekce v jednom okně, přepínání jedním klikem.</p>

  <div class="features-grid">
    <div class="feature-card reveal" style="--fc:var(--cs2)">
      <span class="feature-icon">🎯</span>
      <div class="feature-name" data-cs="Crosshair Generator" data-en="Crosshair Generator">Crosshair Generator</div>
      <div class="feature-desc" data-cs="Live náhled, úprava všech parametrů, export kódu pro CS2 / CS:GO." data-en="Live preview, edit all parameters, export code for CS2 / CS:GO.">Live náhled, úprava všech parametrů, export kódu pro CS2 / CS:GO.</div>
      <span class="tag-game" style="background:#0c1535;border-color:#253a7a;color:var(--cs2)">CS2</span>
    </div>
    <div class="feature-card reveal" style="--fc:var(--cs2)">
      <span class="feature-icon">🔫</span>
      <div class="feature-name" data-cs="Viewmodel Editor" data-en="Viewmodel Editor">Viewmodel Editor</div>
      <div class="feature-desc" data-cs="Nastavení zbraně ve hře s náhledem hodnot v reálném čase." data-en="In-game weapon settings with real-time value preview.">Nastavení zbraně ve hře s náhledem hodnot v reálném čase.</div>
      <span class="tag-game" style="background:#0c1535;border-color:#253a7a;color:var(--cs2)">CS2</span>
    </div>
    <div class="feature-card reveal" style="--fc:var(--primary)">
      <span class="feature-icon">📄</span>
      <div class="feature-name" data-cs="Autoexec Editor" data-en="Autoexec Editor">Autoexec Editor</div>
      <div class="feature-desc" data-cs="Úprava konfiguračního souboru přímo v aplikaci." data-en="Edit your config file directly in the app.">Úprava konfiguračního souboru přímo v aplikaci.</div>
      <span class="tag-game" style="background:#0c1535;border-color:#253a7a;color:var(--cs2)">CS2</span>
      <span class="tag-game" style="background:#1a1400;border-color:#4a3800;color:var(--csgo)">CS:GO</span>
    </div>
    <div class="feature-card reveal" style="--fc:var(--primary)">
      <span class="feature-icon">⚙️</span>
      <div class="feature-name" data-cs="Server CFG Generator" data-en="Server CFG Generator">Server CFG Generator</div>
      <div class="feature-desc" data-cs="Vytvoření serverové konfigurace klikáním — pro CS2 i Rust." data-en="Create server config by clicking — for CS2 and Rust.">Vytvoření serverové konfigurace klikáním — pro CS2 i Rust.</div>
      <span class="tag-game" style="background:#0c1535;border-color:#253a7a;color:var(--cs2)">CS2</span>
      <span class="tag-game" style="background:#1a0a00;border-color:#4a2200;color:var(--rust)">Rust</span>
    </div>
    <div class="feature-card reveal" style="--fc:#888888">
      <span class="feature-icon">📡</span>
      <div class="feature-name" data-cs="RCON Klient" data-en="RCON Client">RCON Klient</div>
      <div class="feature-desc" data-cs="Vzdálená správa serveru přes RCON. Bez externích programů." data-en="Remote server management via RCON. No external tools.">Vzdálená správa serveru přes RCON. Bez externích programů.</div>
    </div>
    <div class="feature-card reveal" style="--fc:var(--primary)">
      <span class="feature-icon">⌨️</span>
      <div class="feature-name" data-cs="Keybind Generator" data-en="Keybind Generator">Keybind Generator</div>
      <div class="feature-desc" data-cs="Vizuální klávesnice — přiřaďte příkazy kliknutím na klávesy." data-en="Visual keyboard — assign commands by clicking keys.">Vizuální klávesnice — přiřaďte příkazy kliknutím na klávesy.</div>
    </div>
    <div class="feature-card reveal" style="--fc:var(--rust)">
      <span class="feature-icon">🦀</span>
      <div class="feature-name" data-cs="Rust Plugin Manager" data-en="Rust Plugin Manager">Rust Plugin Manager</div>
      <div class="feature-desc" data-cs="Dávková oprava pluginů, analýza závislostí, správa Oxide / uMod." data-en="Batch plugin repair, dependency analysis, Oxide / uMod management.">Dávková oprava pluginů, analýza závislostí, správa Oxide / uMod.</div>
      <span class="tag-game" style="background:#1a0a00;border-color:#4a2200;color:var(--rust)">Rust</span>
    </div>
    <div class="feature-card reveal" style="--fc:#22d3ee">
      <span class="feature-icon">🌐</span>
      <div class="feature-name" data-cs="Translator" data-en="Translator">Translator</div>
      <div class="feature-desc" data-cs="Překlad JSON / TXT / LANG souborů do 20+ jazyků." data-en="Translate JSON / TXT / LANG files to 20+ languages.">Překlad JSON / TXT / LANG souborů do 20+ jazyků.</div>
    </div>
    <div class="feature-card reveal" style="--fc:#a78bfa">
      <span class="feature-icon">💻</span>
      <div class="feature-name" data-cs="PC Tools" data-en="PC Tools">PC Tools</div>
      <div class="feature-desc" data-cs="Systémové info (CPU, GPU, RAM), DNS flush, ping tester, čištění tempu." data-en="System info (CPU, GPU, RAM), DNS flush, ping tester, temp cleaner.">Systémové info (CPU, GPU, RAM), DNS flush, ping tester, čištění tempu.</div>
    </div>
    <div class="feature-card reveal" style="--fc:var(--success)">
      <span class="feature-icon">🏠</span>
      <div class="feature-name" data-cs="Live Server Status" data-en="Live Server Status">Live Server Status</div>
      <div class="feature-desc" data-cs="Stav serverů (hráči, mapa, ping) přes Steam A2S query v reálném čase." data-en="Server status (players, map, ping) via Steam A2S query in real time.">Stav serverů (hráči, mapa, ping) přes Steam A2S query v reálném čase.</div>
    </div>
    <div class="feature-card reveal" style="--fc:var(--primary)">
      <span class="feature-icon">🔄</span>
      <div class="feature-name" data-cs="Auto aktualizace" data-en="Auto-update">Auto aktualizace</div>
      <div class="feature-desc" data-cs="Aplikace kontroluje GitHub při spuštění a nabídne aktualizaci." data-en="App checks GitHub on launch and offers an update download.">Aplikace kontroluje GitHub při spuštění a nabídne aktualizaci.</div>
    </div>
    <div class="feature-card reveal" style="--fc:#f472b6">
      <span class="feature-icon">🌙</span>
      <div class="feature-name" data-cs="Dark / Light mode" data-en="Dark / Light mode">Dark / Light mode</div>
      <div class="feature-desc" data-cs="Plný dark a light mode s barevnými tématy pro každou hru." data-en="Full dark and light mode with per-game color themes.">Plný dark a light mode s barevnými tématy pro každou hru.</div>
    </div>
  </div>
</section>

<hr class="divider-line">

<!-- ── Getting started ── -->
<section id="start">
  <div class="section-label reveal" data-cs="Rychlý start" data-en="Quick start">Rychlý start</div>
  <h2 class="section-title reveal" data-cs="Hotovo za 3 kroky" data-en="Done in 3 steps">Hotovo za 3 kroky</h2>
  <p class="section-sub reveal" data-cs="Žádná instalace, žádný Python. Stáhnout a spustit." data-en="No installation, no Python. Download and run.">Žádná instalace, žádný Python. Stáhnout a spustit.</p>

  <div class="steps">
    <div class="step reveal">
      <div class="step-title" data-cs="Stáhnout .exe" data-en="Download .exe">Stáhnout .exe</div>
      <div class="step-desc" data-cs="Stáhněte ZeddiHub.Tools.exe z nejnovější verze na GitHubu." data-en="Download ZeddiHub.Tools.exe from the latest GitHub release.">Stáhněte <code>ZeddiHub.Tools.exe</code> z nejnovější verze na GitHubu.</div>
    </div>
    <div class="step reveal">
      <div class="step-title" data-cs="Spustit" data-en="Launch">Spustit</div>
      <div class="step-desc" data-cs="Žádná instalace. Dvojklik a aplikace se spustí." data-en="No installation. Double-click to launch.">Žádná instalace. Dvojklik a aplikace se spustí.</div>
    </div>
    <div class="step reveal">
      <div class="step-title" data-cs="Přihlásit se" data-en="Log in">Přihlásit se</div>
      <div class="step-desc" data-cs="Zadejte přihlašovací údaje nebo přístupový kód pro odemčení server tools." data-en="Enter credentials or an access code to unlock server tools.">Zadejte přihlašovací údaje nebo přístupový kód pro odemčení server tools.</div>
    </div>
    <div class="step reveal">
      <div class="step-title" data-cs="Hotovo" data-en="Done">Hotovo</div>
      <div class="step-desc" data-cs="Aplikace běží v trayi. Přistupte pravým klikem na ikonu v liště." data-en="App runs in the system tray. Right-click the tray icon to access it.">Aplikace běží v trayi. Přistupte pravým klikem na ikonu v liště.</div>
    </div>
  </div>
</section>

<!-- ── CTA ── -->
<div class="cta-section">
  <h2 class="cta-title reveal">
    <span data-cs="Stáhněte si ZeddiHub Tools" data-en="Download ZeddiHub Tools">Stáhněte si ZeddiHub Tools</span>
  </h2>
  <p class="cta-sub reveal">
    <span class="version-pill">✓ v<?= htmlspecialchars($version) ?></span>
    &nbsp; Windows 10 / 11 &nbsp;·&nbsp;
    <span data-cs="Zdarma" data-en="Free">Zdarma</span>
  </p>
  <div class="hero-actions reveal">
    <a href="<?= GITHUB_DL ?>" class="btn-download">
      ⬇ <span data-cs="Stáhnout .exe" data-en="Download .exe">Stáhnout .exe</span>
    </a>
    <a href="<?= GITHUB_RELEASE ?>" target="_blank" rel="noopener" class="btn-outline">
      📋 <span data-cs="Releases na GitHubu" data-en="GitHub Releases">Releases na GitHubu</span>
    </a>
  </div>
</div>

<!-- ── Footer ── -->
<footer>
  <div class="footer-links">
    <a href="https://zeddihub.eu">zeddihub.eu</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener">Discord</a>
    <a href="https://github.com/<?= GITHUB_REPO ?>" target="_blank" rel="noopener">GitHub</a>
    <a href="admin/">Admin</a>
  </div>
  <p>Made by <strong>ZeddiS</strong> &nbsp;·&nbsp; ZeddiHub Tools <?php if ($version!=='—') echo 'v'.htmlspecialchars($version); ?></p>
</footer>

<script>
// ── Language toggle ──────────────────────────────────────────────────────────
let currentLang = localStorage.getItem('zh_lang') || 'cs';

function applyLang(lang) {
  currentLang = lang;
  localStorage.setItem('zh_lang', lang);
  document.documentElement.setAttribute('data-lang', lang);
  document.getElementById('langBtn').textContent = lang === 'cs' ? '🇬🇧 EN' : '🇨🇿 CS';

  // Replace text content from data-cs / data-en attributes
  document.querySelectorAll('[data-' + lang + ']').forEach(el => {
    // Only update text nodes, not the whole innerHTML if child elements exist
    const newText = el.getAttribute('data-' + lang);
    if (newText && el.children.length === 0) {
      el.textContent = newText;
    }
  });

  // Update nav links
  document.querySelectorAll('.nav-link[data-' + lang + ']').forEach(el => {
    el.textContent = el.getAttribute('data-' + lang);
  });
}

function toggleLang() {
  applyLang(currentLang === 'cs' ? 'en' : 'cs');
}

// Init on load
document.addEventListener('DOMContentLoaded', () => {
  if (currentLang !== 'cs') applyLang(currentLang);
});

// ── Scroll reveal ────────────────────────────────────────────────────────────
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
</script>

</body>
</html>
