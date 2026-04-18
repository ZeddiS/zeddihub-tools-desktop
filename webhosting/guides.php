<?php
/**
 * ZeddiHub Tools — Guides / Návody
 * Kompaktní stránka s návody pro začátečníky i pokročilé.
 */
define('GITHUB_REPO', 'ZeddiS/zeddihub-tools-desktop');
?>
<!DOCTYPE html>
<html lang="cs" data-lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ZeddiHub Tools — Návody & Guides</title>
<meta name="description" content="Kompletní návody pro ZeddiHub Tools Desktop — instalace, CS2 crosshair, Rust RCON, a další.">
<link rel="icon" type="image/x-icon" href="assets/web_favicon.ico">
<link rel="shortcut icon" type="image/x-icon" href="assets/web_favicon.ico">
<style>
:root {
  --bg:#080810; --bg2:#0e0e18; --card:#14141f; --card2:#1c1c2a; --border:#252535;
  --primary:#f0a500; --primary-h:#d4900a;
  --text:#eeeef5; --text-dim:#8888aa; --text-dark:#44445a;
  --cs2:#5b9cf6; --csgo:#fbbf24; --rust:#f97316;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.7}
a{color:var(--primary);text-decoration:none}
a:hover{text-decoration:underline}
code{background:var(--card2);padding:2px 7px;border-radius:4px;font-size:.85em;color:var(--text-dim);font-family:Consolas,monospace}
pre{background:var(--card2);border:1px solid var(--border);padding:14px;border-radius:8px;overflow-x:auto;margin:12px 0;font-family:Consolas,monospace;font-size:13px;color:var(--text)}

/* ── Navbar ── */
.navbar{position:sticky;top:0;z-index:100;background:rgba(8,8,16,.88);backdrop-filter:blur(14px);border-bottom:1px solid var(--border);padding:0 28px;height:58px;display:flex;align-items:center;justify-content:space-between}
.navbar-brand{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:700;color:var(--primary)}
.navbar-logo{height:34px;width:auto;display:block}
.navbar-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.nav-link{font-size:13px;color:var(--text-dim);padding:6px 10px;border-radius:6px;transition:color .15s,background .15s}
.nav-link:hover{color:var(--text);background:var(--card);text-decoration:none}
.nav-link.active{color:var(--primary)}
.btn-admin{display:inline-flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--border);color:var(--text);font-size:13px;font-weight:600;padding:7px 16px;border-radius:6px;transition:all .15s}
.btn-admin:hover{border-color:var(--primary);color:var(--primary);text-decoration:none}

/* ── Main layout ── */
.hero-sm{max-width:1140px;margin:0 auto;padding:40px 24px 12px;text-align:center}
.hero-sm h1{font-size:clamp(28px,4vw,40px);font-weight:800;letter-spacing:-.02em;margin-bottom:8px}
.hero-sm .sub{color:var(--text-dim);font-size:15px;max-width:640px;margin:0 auto 18px}
.badge{display:inline-block;background:var(--card);border:1px solid var(--border);color:var(--primary);font-size:11px;font-weight:700;padding:4px 10px;border-radius:20px;letter-spacing:.12em;text-transform:uppercase}

/* ── Layout: sidebar + content ── */
.layout{max-width:1140px;margin:0 auto;display:grid;grid-template-columns:260px 1fr;gap:28px;padding:24px}
.sidebar{position:sticky;top:78px;align-self:start;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:18px;max-height:calc(100vh - 96px);overflow-y:auto}
.sidebar h3{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--primary);margin-bottom:8px;margin-top:12px}
.sidebar h3:first-child{margin-top:0}
.sidebar a{display:block;padding:6px 10px;border-radius:6px;color:var(--text-dim);font-size:13px;transition:background .15s,color .15s}
.sidebar a:hover,.sidebar a.active{color:var(--text);background:var(--card2);text-decoration:none}

.content{min-width:0}
.guide{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:28px;margin-bottom:20px;scroll-margin-top:80px}
.guide::before{content:"";display:block;height:3px;background:var(--primary);border-radius:2px;margin:-28px -28px 20px;border-top-left-radius:10px;border-top-right-radius:10px}
.guide h2{font-size:22px;margin-bottom:8px}
.guide .meta{font-size:12px;color:var(--text-dark);margin-bottom:14px;display:flex;gap:12px;flex-wrap:wrap}
.guide .meta span{padding:2px 8px;background:var(--card2);border-radius:4px}
.guide h3{font-size:16px;margin:18px 0 8px;color:var(--primary)}
.guide p{color:var(--text-dim);margin-bottom:10px}
.guide ol,.guide ul{margin-left:22px;margin-bottom:10px;color:var(--text-dim)}
.guide li{margin-bottom:4px}
.guide strong{color:var(--text)}

footer{text-align:center;padding:40px 24px;color:var(--text-dark);font-size:13px;border-top:1px solid var(--border);margin-top:40px}
footer a{margin:0 10px}

@media (max-width: 840px) {
  .layout{grid-template-columns:1fr}
  .sidebar{position:static;max-height:none}
}
</style>
</head>
<body>

<nav class="navbar">
  <a href="index.php" class="navbar-brand">
    <img src="assets/logo2.png" alt="ZeddiHub Tools" class="navbar-logo">
  </a>
  <div class="navbar-right">
    <a href="index.php#features" class="nav-link" data-cs="Funkce" data-en="Features">Funkce</a>
    <a href="index.php#news" class="nav-link" data-cs="Novinky" data-en="News">Novinky</a>
    <a href="guides.php" class="nav-link active" data-cs="Návody" data-en="Guides">Návody</a>
    <a href="index.php#start" class="nav-link" data-cs="Ke stažení" data-en="Download">Ke stažení</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener" class="nav-link">Discord</a>
    <a href="admin/" class="btn-admin">🔐 Admin</a>
  </div>
</nav>

<div class="hero-sm">
  <span class="badge" data-cs="Dokumentace" data-en="Documentation">Dokumentace</span>
  <h1 data-cs="Návody & Průvodci" data-en="Guides & Walkthroughs">Návody &amp; Průvodci</h1>
  <p class="sub" data-cs="Kompletní příručka — od první instalace po pokročilou konfiguraci herních serverů." data-en="Complete reference — from first install to advanced server configuration.">Kompletní příručka — od první instalace po pokročilou konfiguraci herních serverů.</p>
</div>

<div class="layout">
  <aside class="sidebar">
    <h3 data-cs="Začínáme" data-en="Getting started">Začínáme</h3>
    <a href="#install"    data-cs="Instalace"               data-en="Installation">Instalace</a>
    <a href="#first-run"  data-cs="První spuštění"          data-en="First launch">První spuštění</a>
    <a href="#login"      data-cs="Přihlášení / kód"        data-en="Login / access code">Přihlášení / kód</a>

    <h3 data-cs="CS2 / CS:GO"        data-en="CS2 / CS:GO">CS2 / CS:GO</h3>
    <a href="#crosshair"  data-cs="Crosshair Generator"     data-en="Crosshair Generator">Crosshair Generator</a>
    <a href="#viewmodel"  data-cs="Viewmodel / Autoexec"    data-en="Viewmodel / Autoexec">Viewmodel / Autoexec</a>
    <a href="#cs-server"  data-cs="Server config & RCON"    data-en="Server config & RCON">Server config &amp; RCON</a>

    <h3 data-cs="Rust" data-en="Rust">Rust</h3>
    <a href="#rust-sens"  data-cs="Sensitivity kalkulátor"  data-en="Sensitivity calculator">Sensitivity kalkulátor</a>
    <a href="#rust-srv"   data-cs="Rust server + pluginy"   data-en="Rust server + plugins">Rust server + pluginy</a>

    <h3 data-cs="PC Nástroje" data-en="PC Tools">PC Nástroje</h3>
    <a href="#pc-basic"   data-cs="DNS flush, temp, ping"   data-en="DNS flush, temp, ping">DNS flush, temp, ping</a>
    <a href="#game-opt"   data-cs="Game Optimization"       data-en="Game Optimization">Game Optimization</a>
    <a href="#advanced"   data-cs="Pokročilé nástroje"      data-en="Advanced tools">Pokročilé nástroje</a>

    <h3 data-cs="Další" data-en="Other">Další</h3>
    <a href="#shortcuts"  data-cs="Klávesové zkratky"       data-en="Keyboard shortcuts">Klávesové zkratky</a>
    <a href="#tray"       data-cs="Tray ikona"              data-en="Tray icon">Tray ikona</a>
    <a href="#file-share" data-cs="File Share"              data-en="File Share">File Share</a>
    <a href="#bug-report" data-cs="Nahlášení chyby"         data-en="Bug report">Nahlášení chyby</a>
  </aside>

  <main class="content">

    <article class="guide" id="install">
      <h2 data-cs="Instalace" data-en="Installation">Instalace</h2>
      <div class="meta"><span>⏱ 2 min</span><span data-cs="Pro začátečníky" data-en="Beginner">Pro začátečníky</span></div>
      <p data-cs="ZeddiHub Tools je standalone .exe — žádná instalace, žádný Python." data-en="ZeddiHub Tools is a standalone .exe — no installation, no Python.">ZeddiHub Tools je standalone <code>.exe</code> — žádná instalace, žádný Python.</p>
      <ol>
        <li data-cs="Stáhněte ZeddiHubTools.exe ze stránky Ke stažení." data-en="Download ZeddiHubTools.exe from the Download page.">Stáhněte <code>ZeddiHubTools.exe</code> ze <a href="index.php#start">stránky Ke stažení</a>.</li>
        <li data-cs="Soubor uložte kamkoliv (ideálně Documents/ZeddiHub/)." data-en="Save the file anywhere (ideally Documents/ZeddiHub/).">Soubor uložte kamkoliv (ideálně <code>Documents/ZeddiHub/</code>).</li>
        <li data-cs="Pokud Windows SmartScreen zobrazí varování, klikněte 'Další informace' → 'Přesto spustit'." data-en="If Windows SmartScreen warns you, click 'More info' → 'Run anyway'.">Pokud Windows SmartScreen zobrazí varování, klikněte <strong>Další informace</strong> → <strong>Přesto spustit</strong>.</li>
      </ol>
    </article>

    <article class="guide" id="first-run">
      <h2 data-cs="První spuštění" data-en="First launch">První spuštění</h2>
      <p data-cs="Při prvním startu se zobrazí wizard s výběrem jazyka a datové složky. Po dokončení se otevře hlavní okno." data-en="On first launch, a wizard lets you pick a language and data folder, then the main window opens.">Při prvním startu se zobrazí wizard s výběrem jazyka a datové složky. Po dokončení se otevře hlavní okno.</p>
      <h3 data-cs="Datová složka" data-en="Data folder">Datová složka</h3>
      <p data-cs="Standardně Documents/ZeddiHub.Tools.Data. Obsahuje settings.json, zašifrované přihlašovací údaje (auth.enc) a cache." data-en="Default is Documents/ZeddiHub.Tools.Data. Contains settings.json, encrypted credentials (auth.enc) and cache.">Standardně <code>Documents/ZeddiHub.Tools.Data</code>. Obsahuje <code>settings.json</code>, zašifrované přihlašovací údaje (<code>auth.enc</code>) a cache.</p>
    </article>

    <article class="guide" id="login">
      <h2 data-cs="Přihlášení a přístupový kód" data-en="Login & access code">Přihlášení a přístupový kód</h2>
      <p data-cs="Server Tools a Advanced PC Tools vyžadují přihlášení. Registrace není otevřená — o přístup napište na Discord zeddis.xyz." data-en="Server Tools and Advanced PC Tools require login. Registration is not open — DM zeddis.xyz on Discord for access.">Server Tools a Advanced PC Tools vyžadují přihlášení. Registrace není otevřená — o přístup napište na Discord <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener">zeddis.xyz</a>.</p>
      <ul>
        <li data-cs="Šifrované uložení přes Fernet AES (klíč odvozen z Machine ID)." data-en="Fernet AES-encrypted storage (key derived from Machine ID).">Šifrované uložení přes <strong>Fernet AES</strong> (klíč odvozen z Machine ID).</li>
        <li data-cs="Přístupové kódy fungují bez uživatelského jména, jen jako jednořádkový kód." data-en="Access codes work without a username — single-line code.">Přístupové kódy fungují bez uživatelského jména, jen jako jednořádkový kód.</li>
      </ul>
    </article>

    <article class="guide" id="crosshair">
      <h2 data-cs="CS2 / CS:GO Crosshair Generator" data-en="CS2 / CS:GO Crosshair Generator">CS2 / CS:GO Crosshair Generator</h2>
      <p data-cs="Vizuální generátor s live preview. Výstupem je .cfg připravený pro autoexec." data-en="Visual generator with live preview. Outputs a .cfg ready for autoexec.">Vizuální generátor s live preview. Výstupem je <code>.cfg</code> připravený pro <code>autoexec</code>.</p>
      <ol>
        <li data-cs="Otevřete CS2 → Player Tools → Crosshair." data-en="Open CS2 → Player Tools → Crosshair.">Otevřete <strong>CS2 → Player Tools → Crosshair</strong>.</li>
        <li data-cs="Nastavte tvar, velikost, šířku, barvu a mezeru — preview se aktualizuje okamžitě." data-en="Adjust shape, size, width, color and gap — the preview updates live.">Nastavte tvar, velikost, šířku, barvu a mezeru — preview se aktualizuje okamžitě.</li>
        <li data-cs="Kliknutím na 'Uložit .cfg' vygenerujete soubor pro vložení do ..\game\csgo\cfg\." data-en="Click 'Save .cfg' to export into ..\game\csgo\cfg\.">Kliknutím na <strong>Uložit .cfg</strong> vygenerujete soubor do <code>..\game\csgo\cfg\</code>.</li>
      </ol>
    </article>

    <article class="guide" id="viewmodel">
      <h2 data-cs="Viewmodel & Autoexec" data-en="Viewmodel & Autoexec">Viewmodel &amp; Autoexec</h2>
      <p data-cs="Viewmodel editor zobrazuje siluetu zbraně s živým náhledem změn. Autoexec sdružuje všechny příkazy v jednom cfg souboru." data-en="Viewmodel editor shows a weapon silhouette with live preview. Autoexec bundles all commands into one cfg file.">Viewmodel editor zobrazuje siluetu zbraně s živým náhledem změn. Autoexec sdružuje všechny příkazy v jednom <code>cfg</code> souboru.</p>
      <pre>// autoexec.cfg (ukázka)
viewmodel_offset_x "2"
viewmodel_offset_y "2"
viewmodel_offset_z "-2"
viewmodel_fov "68"
cl_bob_lower_amt "5"
cl_bobamt_lat "0.1"
cl_bobamt_vert "0.1"
host_writeconfig</pre>
    </article>

    <article class="guide" id="cs-server">
      <h2 data-cs="Server config a RCON klient" data-en="Server config & RCON client">Server config a RCON klient</h2>
      <p data-cs="Generátor pokryje gamemode, network, gameplay a GOTV sekce. RCON klient používá Source Engine protokol (TCP 27015)." data-en="Generator covers gamemode, network, gameplay and GOTV sections. The RCON client uses the Source Engine protocol (TCP 27015).">Generátor pokryje <code>gamemode</code>, <code>network</code>, <code>gameplay</code> a <code>GOTV</code> sekce. RCON klient používá Source Engine protokol (TCP 27015).</p>
      <h3 data-cs="Připojení k RCON" data-en="Connecting to RCON">Připojení k RCON</h3>
      <ol>
        <li data-cs="V app. otevřete CS2 → Server Tools → RCON Klient." data-en="In app open CS2 → Server Tools → RCON Client.">V app. otevřete <strong>CS2 → Server Tools → RCON Klient</strong>.</li>
        <li data-cs="Zadejte IP, port a rcon_password." data-en="Enter IP, port and rcon_password.">Zadejte IP, port a <code>rcon_password</code>.</li>
        <li data-cs="Posílejte příkazy; výstup se zobrazí v konzoli." data-en="Send commands; output appears in the console.">Posílejte příkazy; výstup se zobrazí v konzoli.</li>
      </ol>
    </article>

    <article class="guide" id="rust-sens">
      <h2 data-cs="Rust sensitivity kalkulátor" data-en="Rust sensitivity calculator">Rust sensitivity kalkulátor</h2>
      <p data-cs="Převod cm/360° mezi 5 hrami (Rust, CS2, CS:GO, Valorant, Apex) — zachovává svalovou paměť napříč hrami." data-en="cm/360° conversion across 5 games (Rust, CS2, CS:GO, Valorant, Apex) — preserve muscle memory across games.">Převod <code>cm/360°</code> mezi 5 hrami (Rust, CS2, CS:GO, Valorant, Apex) — zachovává svalovou paměť napříč hrami.</p>
    </article>

    <article class="guide" id="rust-srv">
      <h2 data-cs="Rust server + Oxide pluginy" data-en="Rust server + Oxide plugins">Rust server + Oxide pluginy</h2>
      <p data-cs="Generátor vytvoří .cfg + startup .bat. Plugin Manager umí hromadně opravit zastaralé Oxide pluginy regex-patchi." data-en="The generator produces .cfg + startup .bat. Plugin Manager can bulk-fix outdated Oxide plugins with regex patches.">Generátor vytvoří <code>.cfg</code> + startup <code>.bat</code>. Plugin Manager umí hromadně opravit zastaralé Oxide pluginy regex-patchi.</p>
      <h3 data-cs="Hromadná oprava (Bulk Fix)" data-en="Bulk Fix">Hromadná oprava (Bulk Fix)</h3>
      <ol>
        <li data-cs="Vyberte složku s Oxide/plugins/." data-en="Select the Oxide/plugins/ folder.">Vyberte složku s <code>Oxide/plugins/</code>.</li>
        <li data-cs="Analyzér detekuje prefixy a závislosti." data-en="The analyzer detects prefixes and dependencies.">Analyzér detekuje prefixy a závislosti.</li>
        <li data-cs="Klikněte 'Hromadně opravit' — aplikují se známé patche pro deprecated API." data-en="Click 'Bulk Fix' — known patches for deprecated APIs will apply.">Klikněte <strong>Hromadně opravit</strong> — aplikují se známé patche pro deprecated API.</li>
      </ol>
    </article>

    <article class="guide" id="pc-basic">
      <h2 data-cs="PC Nástroje — základy" data-en="PC Tools — basics">PC Nástroje — základy</h2>
      <ul>
        <li><strong>DNS flush</strong> — <code>ipconfig /flushdns</code> s historií</li>
        <li><strong>Temp cleaner</strong> — uživatelský + systémový TEMP, dual cleanup</li>
        <li><strong>Ping Tool</strong> — Windows ping s ICMP statistikou</li>
        <li><strong>IP Info</strong> — geolokace přes ip-api.com</li>
        <li><strong>Port Checker</strong> — TCP socket probe</li>
        <li><strong>Speedtest</strong> — HTTP download z Cloudflare CDN</li>
      </ul>
    </article>

    <article class="guide" id="game-opt">
      <h2 data-cs="Game Optimization" data-en="Game Optimization">Game Optimization</h2>
      <p data-cs="Jedním klikem aplikuje doporučená herní nastavení Windows. Vše lze vrátit zpět." data-en="One-click apply of recommended Windows gaming settings. Fully reversible.">Jedním klikem aplikuje doporučená herní nastavení Windows. Vše lze vrátit zpět.</p>
      <ul>
        <li><strong>Game Mode</strong> — <code>HKCU\Software\Microsoft\GameBar</code> AutoGameModeEnabled=1</li>
        <li><strong>HAGS</strong> — Hardware-accelerated GPU Scheduling (vyžaduje admin)</li>
        <li><strong>Xbox Game Bar</strong> — skrytí startup panelu</li>
        <li><strong>Fullscreen Optimizations</strong> — vypnutí pro stabilnější framerate</li>
        <li><strong>Power Plan</strong> — Ultimate Performance (<code>powercfg -duplicatescheme</code>)</li>
        <li><strong>Visual Effects</strong> — nastaveno na Performance</li>
      </ul>
    </article>

    <article class="guide" id="advanced">
      <h2 data-cs="Advanced PC Tools" data-en="Advanced PC Tools">Advanced PC Tools</h2>
      <p data-cs="Sekce vyžaduje přihlášení — obsahuje zálohu registru, Startup Manager, seznam služeb, reset sítě a BSOD historii." data-en="Section requires login — contains registry backup, Startup Manager, service list, network reset and BSOD history.">Sekce vyžaduje přihlášení — obsahuje zálohu registru, Startup Manager, seznam služeb, reset sítě a BSOD historii.</p>
      <p data-cs="Některé akce vyžadují administrátorská práva. V Reset sítě aplikace otevře admin CMD a zobrazí příkazy pro zkopírování." data-en="Some actions require admin rights. In Network Reset the app opens admin CMD and shows commands to paste.">Některé akce vyžadují administrátorská práva. V <strong>Reset sítě</strong> aplikace otevře admin CMD a zobrazí příkazy pro zkopírování.</p>
    </article>

    <article class="guide" id="shortcuts">
      <h2 data-cs="Klávesové zkratky" data-en="Keyboard shortcuts">Klávesové zkratky</h2>
      <ul>
        <li><code>Ctrl+1</code> — Domů</li>
        <li><code>Ctrl+2</code> — PC Nástroje</li>
        <li><code>Ctrl+3</code> — Nastavení</li>
        <li><code>Ctrl+4</code> — Odkazy</li>
        <li><code>F5</code> — Znovu načíst panel</li>
        <li><code>Ctrl+M</code> — Minimalizovat do tray</li>
        <li><code>Ctrl+Q</code> — Ukončit aplikaci</li>
        <li><code>F11</code> — Celá obrazovka</li>
        <li><code>F1</code> — Zobrazit tuto nápovědu</li>
      </ul>
      <p data-cs="Zkratky lze vypnout v Nastavení → Klávesové zkratky." data-en="Shortcuts can be disabled in Settings → Keyboard shortcuts.">Zkratky lze vypnout v <strong>Nastavení → Klávesové zkratky</strong>.</p>
    </article>

    <article class="guide" id="tray">
      <h2 data-cs="Tray ikona" data-en="Tray icon">Tray ikona</h2>
      <p data-cs="Zavřením okna se aplikace standardně minimalizuje do systémové lišty. Chování přepnete v Nastavení → Chování tlačítka Zavřít." data-en="Closing the window minimizes to the system tray by default. Change this in Settings → Close button behavior.">Zavřením okna se aplikace standardně minimalizuje do systémové lišty. Chování přepnete v <strong>Nastavení → Chování tlačítka Zavřít</strong>.</p>
    </article>

    <article class="guide" id="file-share">
      <h2 data-cs="File Share" data-en="File Share">File Share</h2>
      <p data-cs="V Odkazy → File Uploader vyberte soubor a klikněte 'Nahrát a sdílet'. Vrátí se krátká URL na files.zeddihub.eu, která se automaticky zkopíruje do schránky." data-en="In Links → File Uploader pick a file and hit 'Upload and share'. A short files.zeddihub.eu URL is returned and auto-copied to clipboard.">V <strong>Odkazy → File Uploader</strong> vyberte soubor a klikněte <strong>Nahrát a sdílet</strong>. Vrátí se krátká URL na <code>files.zeddihub.eu</code>, která se automaticky zkopíruje do schránky.</p>
    </article>

    <article class="guide" id="bug-report">
      <h2 data-cs="Nahlásit chybu" data-en="Report a bug">Nahlásit chybu</h2>
      <p data-cs="V Nastavení klikněte na 'Nahlásit chybu na GitHubu'. Otevře se připravený Issue template s verzí aplikace, OS, Python runtime a aktivním panelem." data-en="In Settings click 'Report a bug on GitHub'. A pre-filled Issue template opens with app version, OS, Python runtime and active panel.">V <strong>Nastavení</strong> klikněte na <strong>Nahlásit chybu na GitHubu</strong>. Otevře se připravený Issue template s verzí aplikace, OS, Python runtime a aktivním panelem.</p>
      <p><a href="https://github.com/<?= GITHUB_REPO ?>/issues/new" target="_blank" rel="noopener">GitHub → New Issue →</a></p>
    </article>

  </main>
</div>

<footer>
  <div>
    <a href="index.php">zeddihub.eu</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener">Discord</a>
    <a href="https://github.com/<?= GITHUB_REPO ?>" target="_blank" rel="noopener">GitHub</a>
    <a href="admin/">Admin</a>
  </div>
  <p>Made by <strong>ZeddiS</strong> &nbsp;·&nbsp; ZeddiHub Tools Guides</p>
</footer>

<script>
// Language toggle (respects localStorage from index.php)
let currentLang = localStorage.getItem('zh_lang') || 'cs';
function applyLang(lang) {
  document.documentElement.setAttribute('data-lang', lang);
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-cs][data-en]').forEach(el => {
    el.textContent = el.getAttribute(lang === 'en' ? 'data-en' : 'data-cs');
  });
}
applyLang(currentLang);

// Sidebar active section highlight
const links = Array.from(document.querySelectorAll('.sidebar a'));
const sections = links.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
function onScroll() {
  let active = sections[0];
  for (const s of sections) {
    if (s.getBoundingClientRect().top <= 120) active = s;
  }
  links.forEach(a => a.classList.toggle(
    'active',
    active && a.getAttribute('href') === '#' + active.id
  ));
}
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();
</script>
</body>
</html>
