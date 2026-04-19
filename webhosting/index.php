<?php
/**
 * ZeddiHub Tools — Public Landing Page
 * Nahrajte tento soubor do kořene webhoistingu (vedle složky /admin/).
 */

define('GITHUB_REPO',    'ZeddiS/zeddihub-tools-desktop');
define('GITHUB_RELEASE', 'https://github.com/' . GITHUB_REPO . '/releases/latest');
define('DL_FILENAME',    'ZeddiHubTools.exe');
// Fallback download URL (používá se, pokud API nevrátí asset URL).
define('GITHUB_DL_FALLBACK', 'https://github.com/' . GITHUB_REPO . '/releases/latest/download/' . DL_FILENAME);

/**
 * Načte latest release z GitHub API + nacachuje 30 minut do .version_cache.json
 * vedle tohoto souboru. Cache obsahuje tag_name, download_url a published_at.
 * Single source of truth pro verzi i download link na celé landing page.
 */
function get_latest_release_cached(): array {
    $cache = __DIR__ . '/.version_cache.json';
    if (file_exists($cache) && (time() - filemtime($cache)) < 1800) {
        $d = json_decode(@file_get_contents($cache), true);
        if (is_array($d) && !empty($d['tag'])) return $d;
    }
    $api_url = 'https://api.github.com/repos/' . GITHUB_REPO . '/releases/latest';
    $json = null;
    if (function_exists('curl_init')) {
        $ch = curl_init($api_url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 4,
            CURLOPT_USERAGENT      => 'ZeddiHubTools-landing',
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_HTTPHEADER     => ['Accept: application/vnd.github.v3+json'],
        ]);
        $json = curl_exec($ch);
        curl_close($ch);
    }
    if (!$json && ini_get('allow_url_fopen')) {
        $ctx = stream_context_create(['http' => [
            'timeout' => 4, 'ignore_errors' => true,
            'header'  => "User-Agent: ZeddiHubTools-landing\r\nAccept: application/vnd.github.v3+json\r\n",
        ]]);
        $json = @file_get_contents($api_url, false, $ctx);
    }
    $data = ['tag' => null, 'download_url' => null, 'published' => null];
    if ($json) {
        $rel = json_decode($json, true);
        if (is_array($rel)) {
            $data['tag']       = ltrim($rel['tag_name'] ?? '', 'v') ?: null;
            $data['published'] = substr($rel['published_at'] ?? '', 0, 10) ?: null;
            if (!empty($rel['assets']) && is_array($rel['assets'])) {
                foreach ($rel['assets'] as $a) {
                    $name = $a['name'] ?? '';
                    if (stripos($name, '.exe') !== false && !empty($a['browser_download_url'])) {
                        $data['download_url'] = $a['browser_download_url'];
                        break;
                    }
                }
            }
        }
    }
    // Fallback na lokální version.json (pro tag) + fallback DL URL.
    if (!$data['tag']) {
        foreach ([__DIR__.'/../data/version.json', dirname(__DIR__).'/data/version.json', __DIR__.'/data/version.json'] as $f) {
            if (file_exists($f)) {
                $d = json_decode(@file_get_contents($f), true);
                if (!empty($d['version'])) { $data['tag'] = $d['version']; break; }
            }
        }
    }
    if (!$data['download_url']) {
        $data['download_url'] = GITHUB_DL_FALLBACK;
    }
    // Cachovat pouze pokud máme alespoň tag (jinak nechceme zafixovat '—').
    if ($data['tag']) {
        @file_put_contents($cache, json_encode($data));
    }
    return $data;
}

function get_latest_version(): string {
    $d = get_latest_release_cached();
    return $d['tag'] ?: '—';
}

function get_latest_download_url(): string {
    $d = get_latest_release_cached();
    return $d['download_url'] ?: GITHUB_DL_FALLBACK;
}

function get_recent_releases(int $limit = 5): array {
    $cache = sys_get_temp_dir() . '/zeddihub_releases_cache.json';
    if (file_exists($cache) && (time() - filemtime($cache)) < 1800) {
        $data = json_decode(@file_get_contents($cache), true);
        if (is_array($data)) return array_slice($data, 0, $limit);
    }
    $api_url = 'https://api.github.com/repos/' . GITHUB_REPO . '/releases?per_page=' . $limit;
    $json = null;
    if (function_exists('curl_init')) {
        $ch = curl_init($api_url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 5,
            CURLOPT_USERAGENT      => 'ZeddiHubTools-landing',
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_HTTPHEADER     => ['Accept: application/vnd.github.v3+json'],
        ]);
        $json = curl_exec($ch);
        curl_close($ch);
    }
    if (!$json && ini_get('allow_url_fopen')) {
        $ctx = stream_context_create(['http' => [
            'timeout' => 5, 'ignore_errors' => true,
            'header'  => "User-Agent: ZeddiHubTools-landing\r\nAccept: application/vnd.github.v3+json\r\n",
        ]]);
        $json = @file_get_contents($api_url, false, $ctx);
    }
    if (!$json) return [];
    $rels = json_decode($json, true);
    if (!is_array($rels)) return [];
    $trim = [];
    foreach (array_slice($rels, 0, $limit) as $r) {
        $trim[] = [
            'tag'       => $r['tag_name'] ?? '?',
            'name'      => $r['name'] ?: ($r['tag_name'] ?? '?'),
            'body'      => $r['body'] ?? '',
            'published' => substr($r['published_at'] ?? '', 0, 10),
            'url'       => $r['html_url'] ?? '',
            'prerelease'=> !empty($r['prerelease']),
        ];
    }
    @file_put_contents($cache, json_encode($trim));
    return $trim;
}

$version  = get_latest_version();
$dl_url   = get_latest_download_url();
$releases = get_recent_releases(5);
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
.hero-banner{display:block;max-width:320px;width:100%;height:auto;margin:0 auto 24px;image-rendering:auto;image-rendering:-webkit-optimize-contrast;filter:none;object-fit:contain;filter:drop-shadow(0 8px 32px rgba(240,165,0,.25))}
.navbar-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.nav-link{font-size:13px;color:var(--text-dim);padding:6px 10px;border-radius:6px;transition:color .15s,background .15s}
.nav-link:hover{color:var(--text);background:var(--card);text-decoration:none}
.btn-lang{
  font-size:12px;font-weight:600;padding:5px 10px;border-radius:6px;
  background:var(--card2);border:1px solid var(--border);color:var(--text-dim);
  cursor:pointer;transition:all .15s;
  display:inline-flex;align-items:center;gap:6px;line-height:1;
}
.btn-lang:hover{color:var(--text);border-color:var(--primary)}
.btn-lang svg.flag{width:18px;height:13px;display:block;border-radius:2px;box-shadow:0 0 0 1px rgba(255,255,255,.08)}
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
  text-align:center;padding:48px 24px 80px;
  max-width:760px;margin:0 auto;
  position:relative;
}
.hero-glow{
  position:absolute;top:20px;left:50%;transform:translateX(-50%);
  width:620px;height:280px;
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
/* ── Feature category tags (F-11) ── */
.feature-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}
.feature-tag{
  display:inline-block;font-size:10px;font-weight:700;padding:2px 8px;
  border-radius:4px;border:1px solid;letter-spacing:.03em;
  text-transform:uppercase;
}
.tag-cs2    {background:#1a0c00;border-color:#4a2800;color:#f0a500}
.tag-csgo   {background:#0c1535;border-color:#253a7a;color:#5b9cf6}
.tag-rust   {background:#1a0600;border-color:#551a00;color:#f97316}
.tag-gaming {background:#00220a;border-color:#00551a;color:#22c55e}
.tag-pctool {background:#1a0a2a;border-color:#3a1a5a;color:#a78bfa}
.tag-server {background:#2a2000;border-color:#5a4400;color:#fbbf24}

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
  .hero{padding:32px 16px 56px}
  .hero-banner{max-width:260px;margin-bottom:20px}
  .hero-title{font-size:32px}
  .hero-sub{font-size:15px;margin-bottom:28px}
  section{padding:44px 16px}
  .navbar{padding:0 16px}
  .btn-download,.btn-outline{font-size:14px;padding:12px 22px}
}

/* ── News section (N-04) ── */
.news-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-top:12px}
.news-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:22px;transition:transform .18s,border-color .18s;position:relative;overflow:hidden}
.news-card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--primary)}
.news-card:hover{transform:translateY(-3px);border-color:var(--primary)}
.news-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}
.news-tag{color:var(--primary);font-weight:800;font-size:17px}
.news-date{color:var(--text-dark);font-size:12px;font-family:'Consolas',monospace}
.news-name{color:var(--text);font-size:14px;font-weight:600;margin-bottom:10px}
.news-body{color:var(--text-dim);font-size:13px;line-height:1.6;max-height:84px;overflow:hidden;margin-bottom:10px;white-space:pre-line}
.news-link{font-size:13px;color:var(--primary);font-weight:600}
.news-badge-pre{display:inline-block;margin-left:6px;padding:1px 6px;border-radius:3px;font-size:10px;background:var(--card2);color:var(--text-dim);font-weight:700}
.news-empty{color:var(--text-dim);font-style:italic;padding:24px;text-align:center}
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
    <a href="#news" class="nav-link" data-cs="Novinky" data-en="News">Novinky</a>
    <a href="guides.php" class="nav-link" data-cs="Návody" data-en="Guides">Návody</a>
    <a href="#start" class="nav-link" data-cs="Ke stažení" data-en="Download">Ke stažení</a>
    <a href="https://dsc.gg/zeddihub" target="_blank" rel="noopener" class="nav-link">Discord</a>
    <button class="btn-lang" onclick="toggleLang()" id="langBtn" aria-label="Switch language">
      <svg class="flag" viewBox="0 0 60 30" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <clipPath id="gb-s"><path d="M0,0 v30 h60 v-30 z"/></clipPath>
        <clipPath id="gb-t"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath>
        <g clip-path="url(#gb-s)">
          <path d="M0,0 v30 h60 v-30 z" fill="#012169"/>
          <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/>
          <path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#gb-t)" stroke="#C8102E" stroke-width="4"/>
          <path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/>
          <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/>
        </g>
      </svg>
      <span id="langBtnText">EN</span>
    </button>
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
    <a href="<?= htmlspecialchars($dl_url) ?>" class="btn-download" download="<?= DL_FILENAME ?>">
      ⬇ <span data-cs="Stáhnout <?= DL_FILENAME ?>" data-en="Download <?= DL_FILENAME ?>">Stáhnout <?= DL_FILENAME ?></span>
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

    <!-- 1. Crosshair Generator -->
    <div class="feature-card reveal" style="--fc:var(--cs2)">
      <span class="feature-icon">🎯</span>
      <div class="feature-name" data-cs="Crosshair Generator" data-en="Crosshair Generator">Crosshair Generator</div>
      <div class="feature-desc" data-cs="Live náhled, úprava všech parametrů, export kódu pro CS2 i CS:GO." data-en="Live preview, edit all parameters, export code for CS2 and CS:GO.">Live náhled, úprava všech parametrů, export kódu pro CS2 i CS:GO.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-cs2">CS2</span>
        <span class="feature-tag tag-csgo">CS:GO</span>
      </div>
    </div>

    <!-- 2. Server.cfg + RCON -->
    <div class="feature-card reveal" style="--fc:var(--primary)">
      <span class="feature-icon">⚙️</span>
      <div class="feature-name" data-cs="Server.cfg + RCON" data-en="Server.cfg + RCON">Server.cfg + RCON</div>
      <div class="feature-desc" data-cs="Generátor server konfigurace, gamemode presety a integrovaný RCON klient — bez externích programů." data-en="Server config generator, gamemode presets and built-in RCON client — no external tools needed.">Generátor server konfigurace, gamemode presety a integrovaný RCON klient.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-cs2">CS2</span>
        <span class="feature-tag tag-csgo">CS:GO</span>
        <span class="feature-tag tag-server">Server</span>
      </div>
    </div>

    <!-- 3. Rust Plugin Manager -->
    <div class="feature-card reveal" style="--fc:var(--rust)">
      <span class="feature-icon">🦀</span>
      <div class="feature-name" data-cs="Rust Plugin Manager" data-en="Rust Plugin Manager">Rust Plugin Manager</div>
      <div class="feature-desc" data-cs="Dávková oprava Oxide / uMod pluginů, detekce závislostí, správa příkazů a prefixů." data-en="Batch repair of Oxide / uMod plugins, dependency detection, commands and prefix management.">Dávková oprava Oxide / uMod pluginů, detekce závislostí, správa příkazů.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-rust">Rust</span>
        <span class="feature-tag tag-server">Server</span>
      </div>
    </div>

    <!-- 4. Sensitivity Converter -->
    <div class="feature-card reveal" style="--fc:#a78bfa">
      <span class="feature-icon">🎮</span>
      <div class="feature-name" data-cs="Sensitivity Converter" data-en="Sensitivity Converter">Sensitivity Converter</div>
      <div class="feature-desc" data-cs="Přepočet citlivosti mezi 20+ hrami, eDPI kalkulačka a auto-detekce Windows sensitivity z registru." data-en="Convert sensitivity between 20+ games, eDPI calculator and Windows sensitivity auto-detection from registry.">Přepočet citlivosti mezi 20+ hrami, eDPI kalkulačka a auto-detekce.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-cs2">CS2</span>
        <span class="feature-tag tag-csgo">CS:GO</span>
        <span class="feature-tag tag-rust">Rust</span>
        <span class="feature-tag tag-gaming">Gaming</span>
      </div>
    </div>

    <!-- 5. PC Optimization -->
    <div class="feature-card reveal" style="--fc:#10b981">
      <span class="feature-icon">⚡</span>
      <div class="feature-name" data-cs="PC Optimalizace" data-en="PC Optimization">PC Optimalizace</div>
      <div class="feature-desc" data-cs="Sys info (CPU, GPU, RAM), čištění TEMP, správce procesů a další utility pro ladění výkonu." data-en="Sys info (CPU, GPU, RAM), TEMP cleaner, process manager and more performance tweaking utilities.">Sys info, čištění TEMP, správce procesů a další utility pro ladění výkonu.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-pctool">PC Tool</span>
        <span class="feature-tag tag-gaming">Gaming</span>
      </div>
    </div>

    <!-- 6. Game Mode + HAGS -->
    <div class="feature-card reveal" style="--fc:#fbbf24">
      <span class="feature-icon">🚀</span>
      <div class="feature-name" data-cs="Game Mode + HAGS" data-en="Game Mode + HAGS">Game Mode + HAGS</div>
      <div class="feature-desc" data-cs="Jedním klikem zapne Windows Game Mode, Hardware Accelerated GPU Scheduling a další herní optimalizace." data-en="Toggle Windows Game Mode, Hardware Accelerated GPU Scheduling and other gaming optimizations with one click.">Windows Game Mode, HAGS a další herní optimalizace jedním klikem.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-gaming">Gaming</span>
        <span class="feature-tag tag-pctool">PC Tool</span>
      </div>
    </div>

    <!-- 7. DNS Tools -->
    <div class="feature-card reveal" style="--fc:#22d3ee">
      <span class="feature-icon">🌐</span>
      <div class="feature-name" data-cs="DNS Tools" data-en="DNS Tools">DNS Tools</div>
      <div class="feature-desc" data-cs="DNS flush, scanner pro A/AAAA/MX/NS/TXT/CNAME záznamy, DNS lookup s historií." data-en="DNS flush, scanner for A/AAAA/MX/NS/TXT/CNAME records, DNS lookup with history.">DNS flush, scanner záznamů (A/AAAA/MX/NS/TXT) a lookup s historií.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-pctool">PC Tool</span>
      </div>
    </div>

    <!-- 8. Speedtest + Ping -->
    <div class="feature-card reveal" style="--fc:#60a5fa">
      <span class="feature-icon">📡</span>
      <div class="feature-name" data-cs="Speedtest + Ping" data-en="Speedtest + Ping">Speedtest + Ping</div>
      <div class="feature-desc" data-cs="HTTP speedtest přes Cloudflare CDN, ping tester pro 10 herních serverů, port checker a IP geolokace." data-en="HTTP speedtest via Cloudflare CDN, ping tester for 10 game servers, port checker and IP geolocation.">Speedtest, ping tester pro herní servery, port checker a IP geolokace.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-pctool">PC Tool</span>
      </div>
    </div>

    <!-- 9. Sticky Notes & Autoclicker -->
    <div class="feature-card reveal" style="--fc:#f472b6">
      <span class="feature-icon">📝</span>
      <div class="feature-name" data-cs="Sticky Notes & Autoclicker" data-en="Sticky Notes & Autoclicker">Sticky Notes & Autoclicker</div>
      <div class="feature-desc" data-cs="Perzistentní poznámky na ploše s self-destruct timerem a globální autoclicker s nastavitelným CPS." data-en="Persistent desktop notes with self-destruct timer and a global autoclicker with adjustable CPS.">Perzistentní poznámky se self-destruct timerem a globální autoclicker.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-pctool">PC Tool</span>
      </div>
    </div>

    <!-- 10. YouTube Downloader -->
    <div class="feature-card reveal" style="--fc:#ef4444">
      <span class="feature-icon">📺</span>
      <div class="feature-name" data-cs="YouTube Downloader" data-en="YouTube Downloader">YouTube Downloader</div>
      <div class="feature-desc" data-cs="Stahování YouTube videí i zvuku (MP3). Výběr kvality od 360p po 4K, lazy yt-dlp." data-en="Download YouTube videos and audio (MP3). Quality from 360p to 4K, lazy yt-dlp.">Stahování YouTube videí i MP3, výběr kvality od 360p po 4K.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-pctool">PC Tool</span>
      </div>
    </div>

    <!-- 11. File Share Uploader -->
    <div class="feature-card reveal" style="--fc:#06b6d4">
      <span class="feature-icon">📤</span>
      <div class="feature-name" data-cs="File Share Uploader" data-en="File Share Uploader">File Share Uploader</div>
      <div class="feature-desc" data-cs="Rychlé sdílení souborů přes integrovaný uploader — odkaz připravený ke sdílení během vteřin." data-en="Quick file sharing via the built-in uploader — share-ready link in seconds.">Rychlé sdílení souborů přes integrovaný uploader — odkaz během vteřin.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-pctool">PC Tool</span>
      </div>
    </div>

    <!-- 12. Server Watchdog -->
    <div class="feature-card reveal" style="--fc:var(--success)">
      <span class="feature-icon">🐕</span>
      <div class="feature-name" data-cs="Server Watchdog" data-en="Server Watchdog">Server Watchdog</div>
      <div class="feature-desc" data-cs="Monitoring herních serverů na pozadí (UDP A2S + TCP fallback) s alertem při výpadku." data-en="Background game server monitoring (UDP A2S + TCP fallback) with downtime alerts.">Monitoring serverů na pozadí (A2S + TCP) s alertem při výpadku.</div>
      <div class="feature-tags">
        <span class="feature-tag tag-server">Server</span>
      </div>
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
      <div class="step-title" data-cs="1. Stáhnout .exe" data-en="1. Download .exe">1. Stáhnout .exe</div>
      <div class="step-desc" data-cs="Stáhněte ZeddiHub.Tools.exe z nejnovější verze na GitHubu." data-en="Download ZeddiHub.Tools.exe from the latest GitHub release.">Stáhněte <code>ZeddiHub.Tools.exe</code> z nejnovější verze na GitHubu.</div>
    </div>
    <div class="step reveal">
      <div class="step-title" data-cs="2. Spustit" data-en="2. Launch">2. Spustit</div>
      <div class="step-desc" data-cs="Žádná instalace, žádný Python. Dvojklik a aplikace se spustí." data-en="No installation, no Python. Double-click to launch.">Žádná instalace, žádný Python. Dvojklik a aplikace se spustí.</div>
    </div>
    <div class="step reveal">
      <div class="step-title" data-cs="3. Přihlásit se" data-en="3. Log in">3. Přihlásit se</div>
      <div class="step-desc" data-cs="Zadejte přihlašovací údaje nebo přístupový kód. Hotovo – aplikace běží v trayi." data-en="Enter credentials or an access code. Done – app runs in the system tray.">Zadejte přihlašovací údaje nebo přístupový kód. Hotovo – aplikace běží v trayi.</div>
    </div>
  </div>
</section>

<hr class="divider-line">

<!-- ── News / Releases (N-04) ── -->
<section id="news">
  <div class="section-label reveal" data-cs="Novinky" data-en="What's new">Novinky</div>
  <h2 class="section-title reveal" data-cs="Aktualizace a changelog" data-en="Updates & changelog">Aktualizace a changelog</h2>
  <p class="section-sub reveal" data-cs="Posledních 5 verzí přímo z GitHub Releases — každá verze přináší nové funkce a opravy." data-en="Last 5 versions straight from GitHub Releases — each release brings new features and fixes.">Posledních 5 verzí přímo z GitHub Releases — každá verze přináší nové funkce a opravy.</p>

  <div class="news-grid">
    <?php if (empty($releases)): ?>
      <div class="news-empty" data-cs="Momentálně se nepodařilo načíst seznam verzí. Zkuste to prosím později nebo navštivte GitHub přímo." data-en="Unable to load releases right now. Please try again later or visit GitHub directly.">Momentálně se nepodařilo načíst seznam verzí. Zkuste to prosím později nebo navštivte GitHub přímo.</div>
    <?php else: foreach ($releases as $r): ?>
      <article class="news-card reveal">
        <div class="news-head">
          <div class="news-tag">
            <?= htmlspecialchars($r['tag']) ?>
            <?php if ($r['prerelease']): ?><span class="news-badge-pre">pre</span><?php endif; ?>
          </div>
          <div class="news-date"><?= htmlspecialchars($r['published']) ?></div>
        </div>
        <div class="news-name"><?= htmlspecialchars($r['name']) ?></div>
        <div class="news-body"><?= htmlspecialchars(
            mb_substr(preg_replace('/\r\n|\r/', "\n", $r['body'] ?? ''), 0, 280)
        ) ?><?= mb_strlen($r['body'] ?? '') > 280 ? '…' : '' ?></div>
        <?php if (!empty($r['url'])): ?>
          <a class="news-link" href="<?= htmlspecialchars($r['url']) ?>" target="_blank" rel="noopener" data-cs="Číst na GitHubu →" data-en="Read on GitHub →">Číst na GitHubu →</a>
        <?php endif; ?>
      </article>
    <?php endforeach; endif; ?>
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
    <a href="<?= htmlspecialchars($dl_url) ?>" class="btn-download" download="<?= DL_FILENAME ?>">
      ⬇ <span data-cs="Stáhnout <?= DL_FILENAME ?>" data-en="Download <?= DL_FILENAME ?>">Stáhnout <?= DL_FILENAME ?></span>
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
  // Update language button: show the OTHER language flag + label
  const btn = document.getElementById('langBtn');
  const txt = document.getElementById('langBtnText');
  const svg = btn.querySelector('svg.flag');
  if (lang === 'cs') {
    // Currently CS -> button offers switch to EN (show UK flag)
    txt.textContent = 'EN';
    svg.innerHTML = '<clipPath id="gb-s"><path d="M0,0 v30 h60 v-30 z"/></clipPath>'
      + '<clipPath id="gb-t"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath>'
      + '<g clip-path="url(#gb-s)">'
      + '<path d="M0,0 v30 h60 v-30 z" fill="#012169"/>'
      + '<path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/>'
      + '<path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#gb-t)" stroke="#C8102E" stroke-width="4"/>'
      + '<path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/>'
      + '<path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/>'
      + '</g>';
  } else {
    // Currently EN -> button offers switch to CS (show CZ flag)
    txt.textContent = 'CS';
    svg.innerHTML = '<rect width="60" height="15" y="0" fill="#fff"/>'
      + '<rect width="60" height="15" y="15" fill="#D7141A"/>'
      + '<path d="M0,0 L30,15 L0,30 Z" fill="#11457E"/>';
  }

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
