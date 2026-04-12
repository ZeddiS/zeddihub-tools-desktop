<?php
/**
 * ZeddiHub Tools - Web Admin Panel
 * Správa klientů, doporučených nástrojů, tray funkcí a serverů.
 *
 * Požadavky: PHP 7.4+, práva zápisu do ../data/
 * Nahrát na webhosting do složky /admin/
 * Data soubory musí být v /data/ (o úroveň výše od /admin/)
 */

// ── Session — works with mod_php AND FastCGI/php-fpm, PHP 7.0+ ───────────────
$_session_opts = ['cookie_httponly' => true];
if (PHP_VERSION_ID >= 70300) {               // cookie_samesite added in PHP 7.3
    $_session_opts['cookie_samesite'] = 'Strict';
}
if (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') {
    $_session_opts['cookie_secure'] = true;
}
session_start($_session_opts);

// ── Configuration ────────────────────────────────────────────────────────────
// Resolve data directory robustly — realpath() returns false if dir doesn't exist yet
$_data_path = realpath(__DIR__ . '/../data');
if ($_data_path === false) {
    $_data_path = dirname(__DIR__) . '/data';
}
define('DATA_DIR', rtrim($_data_path, '/\\') . '/');
define('APP_TITLE',  'ZeddiHub Admin');

define('FILE_AUTH',        DATA_DIR . 'auth.json');
define('FILE_RECOMMENDED', DATA_DIR . 'recommended.json');
define('FILE_TRAY',        DATA_DIR . 'tray_tools.json');
define('FILE_SERVERS',     DATA_DIR . 'servers.json');
define('FILE_VERSION',     DATA_DIR . 'version.json');
define('FILE_TELEMETRY',   DATA_DIR . 'telemetry.json');
define('FILE_GH_CACHE',    DATA_DIR . '.gh_cache.json');
define('GITHUB_REPO',      'ZeddiS/zeddihub_tools_desktop');
define('APP_VERSION',      '1.6.0');

// ── Startup check ─────────────────────────────────────────────────────────────
if (!is_dir(DATA_DIR)) {
    http_response_code(503);
    echo '<!DOCTYPE html><html lang="cs"><head><meta charset="UTF-8">
<title>Setup chyba – ZeddiHub Admin</title>
<style>body{font-family:Segoe UI,sans-serif;background:#0c0c0c;color:#e8e8e8;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
.box{background:#1a1a1a;border:1px solid #f0a500;border-radius:10px;padding:32px 40px;max-width:520px;}
h2{color:#f0a500;margin-bottom:12px}code{background:#222;padding:2px 6px;border-radius:4px;font-size:13px}
</style></head><body><div class="box">
<h2>&#9888; Složka <code>data/</code> nenalezena</h2>
<p>Admin panel očekává složku <code>data/</code> o úroveň výše než složka <code>admin/</code>.</p>
<p style="margin-top:12px;color:#888;font-size:13px">
Struktura na serveru musí být:<br><br>
<code>admin/index.php</code><br>
<code>data/auth.json</code><br>
<code>data/servers.json</code> atd.
</p>
<p style="margin-top:16px;color:#888;font-size:13px">
Aktuální cesta hledaná pro data: <code>' . htmlspecialchars(DATA_DIR) . '</code>
</p>
</div></body></html>';
    exit;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function read_json(string $path): array {
    if (!file_exists($path)) return [];
    $raw = file_get_contents($path);
    return json_decode($raw, true) ?? [];
}

function write_json(string $path, $data): bool {
    $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    return file_put_contents($path, $json) !== false;
}

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

function flash(string $type, string $msg): void {
    $_SESSION['flash'] = ['type' => $type, 'msg' => $msg];
}

function get_flash(): ?array {
    $f = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $f;
}

function csrf_token(): string {
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['csrf'];
}

function check_csrf(): void {
    if (($_POST['_csrf'] ?? '') !== ($_SESSION['csrf'] ?? '')) {
        http_response_code(403);
        die('CSRF check failed.');
    }
}

function redirect(string $url): void {
    header("Location: $url");
    exit;
}

function require_login(): void {
    if (empty($_SESSION['admin_user'])) {
        redirect('?page=login');
    }
}

// ── Language ──────────────────────────────────────────────────────────────────

function admin_lang(): string {
    if (isset($_GET['lang']) && in_array($_GET['lang'], ['cs', 'en'])) {
        $_SESSION['admin_lang'] = $_GET['lang'];
    }
    return $_SESSION['admin_lang'] ?? 'cs';
}

function L(string $key): string {
    static $strings = null;
    if ($strings === null) {
        $strings = [
            'cs' => [
                'dashboard'    => 'Dashboard',
                'clients'      => 'Klienti',
                'recommended'  => 'Doporučené',
                'tray'         => 'Tray nástroje',
                'servers'      => 'Servery',
                'version'      => 'Verze / Update',
                'telemetry'    => 'Telemetrie',
                'logged_as'    => 'Přihlášen',
                'logout'       => 'Odhlásit',
                'quick_actions'=> 'Rychlé akce',
                'github_stats' => 'GitHub statistiky',
                'telemetry_overview' => 'Přehled telemetrie',
                'total_launches'     => 'Celkem spuštění',
                'unique_users'       => 'Jedinečných uživatelů',
                'anonymous'          => 'Anonymních relací',
                'total_events'       => 'Celkem událostí',
                'top_panels'         => 'Nejpoužívanější panely',
                'versions_breakdown' => 'Verze klientů',
                'os_breakdown'       => 'Operační systémy',
                'last_30_days'       => 'Posledních 30 dní',
                'fetching'           => 'Načítám...',
                'gh_stars'           => 'Hvězdičky',
                'gh_forks'           => 'Forky',
                'gh_watchers'        => 'Sledující',
                'gh_downloads'       => 'Stažení (.exe)',
                'no_data'            => 'Žádná data',
            ],
            'en' => [
                'dashboard'    => 'Dashboard',
                'clients'      => 'Clients',
                'recommended'  => 'Recommended',
                'tray'         => 'Tray tools',
                'servers'      => 'Servers',
                'version'      => 'Version / Update',
                'telemetry'    => 'Telemetry',
                'logged_as'    => 'Logged in as',
                'logout'       => 'Log out',
                'quick_actions'=> 'Quick actions',
                'github_stats' => 'GitHub statistics',
                'telemetry_overview' => 'Telemetry overview',
                'total_launches'     => 'Total launches',
                'unique_users'       => 'Unique users',
                'anonymous'          => 'Anonymous sessions',
                'total_events'       => 'Total events',
                'top_panels'         => 'Top panels',
                'versions_breakdown' => 'Client versions',
                'os_breakdown'       => 'Operating systems',
                'last_30_days'       => 'Last 30 days',
                'fetching'           => 'Loading...',
                'gh_stars'           => 'Stars',
                'gh_forks'           => 'Forks',
                'gh_watchers'        => 'Watchers',
                'gh_downloads'       => 'Downloads (.exe)',
                'no_data'            => 'No data',
            ],
        ];
    }
    $lang = admin_lang();
    return $strings[$lang][$key] ?? $strings['cs'][$key] ?? $key;
}

// ── GitHub stats ──────────────────────────────────────────────────────────────

function get_github_stats(): array {
    // Cache for 30 minutes
    if (file_exists(FILE_GH_CACHE)) {
        $cache = @json_decode(file_get_contents(FILE_GH_CACHE), true);
        if (is_array($cache) && isset($cache['_ts']) && (time() - $cache['_ts']) < 1800) {
            return $cache;
        }
    }

    $repo = GITHUB_REPO;
    $stats = ['_ts' => time(), 'stars' => null, 'forks' => null, 'watchers' => null, 'downloads' => null];

    // Repo info
    $repo_data = _gh_fetch("https://api.github.com/repos/$repo");
    if ($repo_data) {
        $stats['stars']    = (int)($repo_data['stargazers_count'] ?? 0);
        $stats['forks']    = (int)($repo_data['forks_count'] ?? 0);
        $stats['watchers'] = (int)($repo_data['watchers_count'] ?? 0);
    }

    // Download count from releases
    $releases = _gh_fetch("https://api.github.com/repos/$repo/releases");
    if (is_array($releases)) {
        $total = 0;
        foreach ($releases as $rel) {
            foreach ($rel['assets'] ?? [] as $asset) {
                if (str_ends_with_compat(strtolower($asset['name'] ?? ''), '.exe')) {
                    $total += (int)($asset['download_count'] ?? 0);
                }
            }
        }
        $stats['downloads'] = $total;
    }

    @file_put_contents(FILE_GH_CACHE, json_encode($stats));
    return $stats;
}

function str_ends_with_compat(string $hay, string $needle): bool {
    return substr($hay, -strlen($needle)) === $needle;
}

function _gh_fetch(string $url): ?array {
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 8,
            CURLOPT_HTTPHEADER     => ['User-Agent: ZeddiHub-Admin/1.0'],
            CURLOPT_SSL_VERIFYPEER => true,
        ]);
        $body = curl_exec($ch);
        curl_close($ch);
        if ($body) return @json_decode($body, true);
    } elseif (ini_get('allow_url_fopen')) {
        $ctx = stream_context_create(['http' => ['header' => "User-Agent: ZeddiHub-Admin/1.0\r\n", 'timeout' => 8]]);
        $body = @file_get_contents($url, false, $ctx);
        if ($body) return @json_decode($body, true);
    }
    return null;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

function do_login(string $username, string $password): bool {
    $auth = read_json(FILE_AUTH);
    foreach ($auth['users'] ?? [] as $user) {
        if (
            strtolower($user['username'] ?? '') === strtolower($username)
            && ($user['password'] ?? '') === $password
            && ($user['role'] ?? '') === 'admin'
        ) {
            $_SESSION['admin_user'] = $user['username'];
            return true;
        }
    }
    return false;
}

// ── Router ───────────────────────────────────────────────────────────────────

$page    = $_GET['page'] ?? 'dashboard';
$action  = $_POST['_action'] ?? '';

// Public pages
if ($page === 'login') {
    if ($action === 'login') {
        check_csrf();
        $u = trim($_POST['username'] ?? '');
        $p = $_POST['password'] ?? '';
        if (do_login($u, $p)) {
            redirect('?page=dashboard');
        } else {
            flash('error', 'Nesprávné přihlašovací údaje nebo nemáte admin oprávnění.');
            redirect('?page=login');
        }
    }
    render_login();
    exit;
}

if ($page === 'logout') {
    session_destroy();
    redirect('?page=login');
}

// Protected pages
require_login();

// Handle POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    check_csrf();
    handle_action($page, $action);
}

// Render page
render_page($page);

// ── Action handlers ──────────────────────────────────────────────────────────

function handle_action(string $page, string $action): void {
    switch ($page) {
        case 'clients':     handle_clients($action); break;
        case 'recommended': handle_json_save(FILE_RECOMMENDED, 'recommended'); break;
        case 'tray':        handle_json_save(FILE_TRAY, 'tray'); break;
        case 'servers':     handle_json_save(FILE_SERVERS, 'servers'); break;
        case 'version':     handle_json_save(FILE_VERSION, 'version'); break;
    }
}

function handle_clients(string $action): void {
    $auth = read_json(FILE_AUTH);
    if (!isset($auth['users']))        $auth['users'] = [];
    if (!isset($auth['access_codes'])) $auth['access_codes'] = [];

    switch ($action) {
        case 'add_user':
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $role     = in_array($_POST['role'] ?? '', ['admin', 'user']) ? $_POST['role'] : 'user';
            if (!$username || !$password) {
                flash('error', 'Vyplňte uživatelské jméno a heslo.');
                break;
            }
            foreach ($auth['users'] as $u) {
                if (strtolower($u['username']) === strtolower($username)) {
                    flash('error', "Uživatel '$username' již existuje.");
                    redirect('?page=clients');
                }
            }
            $new = ['username' => $username, 'password' => $password];
            if ($role === 'admin') $new['role'] = 'admin';
            $auth['users'][] = $new;
            if (write_json(FILE_AUTH, $auth)) {
                flash('success', "Uživatel '$username' byl přidán.");
            } else {
                flash('error', 'Chyba při ukládání souboru.');
            }
            break;

        case 'delete_user':
            $del = trim($_POST['username'] ?? '');
            if ($del === ($_SESSION['admin_user'] ?? '')) {
                flash('error', 'Nemůžete smazat vlastní účet.');
                break;
            }
            $auth['users'] = array_values(array_filter(
                $auth['users'],
                function($u) use ($del) {
                    return strtolower($u['username'] ?? '') !== strtolower($del);
                }
            ));
            if (write_json(FILE_AUTH, $auth)) {
                flash('success', "Uživatel '$del' byl smazán.");
            } else {
                flash('error', 'Chyba při ukládání souboru.');
            }
            break;

        case 'edit_user':
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $role     = in_array($_POST['role'] ?? '', ['admin', 'user']) ? $_POST['role'] : 'user';
            foreach ($auth['users'] as &$u) {
                if (strtolower($u['username'] ?? '') === strtolower($username)) {
                    if ($password) $u['password'] = $password;
                    if ($role === 'admin') $u['role'] = 'admin';
                    else unset($u['role']);
                    break;
                }
            }
            unset($u);
            if (write_json(FILE_AUTH, $auth)) {
                flash('success', "Uživatel '$username' byl upraven.");
            } else {
                flash('error', 'Chyba při ukládání souboru.');
            }
            break;

        case 'add_code':
            $code = trim($_POST['code'] ?? '');
            if (!$code) {
                flash('error', 'Zadejte přístupový kód.');
                break;
            }
            if (in_array($code, $auth['access_codes'])) {
                flash('error', 'Tento kód již existuje.');
                break;
            }
            $auth['access_codes'][] = $code;
            if (write_json(FILE_AUTH, $auth)) {
                flash('success', "Přístupový kód '$code' byl přidán.");
            } else {
                flash('error', 'Chyba při ukládání souboru.');
            }
            break;

        case 'delete_code':
            $code = trim($_POST['code'] ?? '');
            $auth['access_codes'] = array_values(array_filter(
                $auth['access_codes'],
                function($c) use ($code) { return $c !== $code; }
            ));
            if (write_json(FILE_AUTH, $auth)) {
                flash('success', "Kód '$code' byl smazán.");
            } else {
                flash('error', 'Chyba při ukládání souboru.');
            }
            break;
    }
    redirect('?page=clients');
}

function handle_json_save(string $file, string $redirect_page): void {
    $raw = trim($_POST['json_content'] ?? '');
    $decoded = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        flash('error', 'Neplatný JSON: ' . json_last_error_msg());
        redirect("?page=$redirect_page");
    }
    if (write_json($file, $decoded)) {
        flash('success', 'Uloženo!');
    } else {
        flash('error', 'Chyba při ukládání souboru. Zkontrolujte práva zápisu.');
    }
    redirect("?page=$redirect_page");
}

// ── Render ────────────────────────────────────────────────────────────────────

function render_login(): void {
    $flash = get_flash();
    $csrf  = csrf_token();
    ?>
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Přihlášení – <?= APP_TITLE ?></title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-box">
    <div class="login-logo">
      <h1>🔐 ZeddiHub Admin</h1>
      <p>Správa serverové konfigurace</p>
    </div>
    <?php if ($flash): ?>
    <div class="alert alert-<?= h($flash['type']) ?>">
      <?= $flash['type'] === 'success' ? '✓' : '✗' ?> <?= h($flash['msg']) ?>
    </div>
    <?php endif; ?>
    <form method="post" action="?page=login">
      <input type="hidden" name="_action" value="login">
      <input type="hidden" name="_csrf" value="<?= h($csrf) ?>">
      <div class="form-group">
        <label class="form-label">Uživatelské jméno</label>
        <input type="text" name="username" class="form-input" required autofocus
               value="<?= h($_POST['username'] ?? '') ?>">
      </div>
      <div class="form-group">
        <label class="form-label">Heslo</label>
        <input type="password" name="password" class="form-input" required>
      </div>
      <div class="btn-row" style="margin-top:20px">
        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">
          Přihlásit se
        </button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:11px;color:#555">
      Přihlásit se mohou pouze uživatelé s rolí <strong>admin</strong>
    </p>
  </div>
</div>
</body>
</html>
    <?php
}

function render_page(string $page): void {
    $flash = get_flash();
    $csrf  = csrf_token();
    $user  = $_SESSION['admin_user'] ?? '?';

    admin_lang(); // init language from GET if provided
    $pages = [
        'dashboard'   => ['icon' => '🏠', 'label' => L('dashboard')],
        'clients'     => ['icon' => '👥', 'label' => L('clients')],
        'recommended' => ['icon' => '⭐', 'label' => L('recommended')],
        'tray'        => ['icon' => '📌', 'label' => L('tray')],
        'servers'     => ['icon' => '📡', 'label' => L('servers')],
        'version'     => ['icon' => '🔄', 'label' => L('version')],
        'telemetry'   => ['icon' => '📊', 'label' => L('telemetry')],
    ];
    $title = $pages[$page]['label'] ?? ucfirst($page);
    ?>
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= h($title) ?> – <?= APP_TITLE ?></title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="layout">

  <!-- Sidebar -->
  <nav class="sidebar">
    <div class="sidebar-logo">
      <h2>ZeddiHub Admin</h2>
      <p>v<?= APP_VERSION ?></p>
    </div>
    <div class="sidebar-nav">
      <?php foreach ($pages as $p => $info): ?>
      <a href="?page=<?= h($p) ?>" class="nav-item <?= $page === $p ? 'active' : '' ?>">
        <span class="nav-icon"><?= $info['icon'] ?></span>
        <?= h($info['label']) ?>
      </a>
      <?php endforeach; ?>
    </div>
    <div class="sidebar-footer">
      <?= L('logged_as') ?>: <strong><?= h($user) ?></strong><br>
      <a href="?page=logout" style="color:var(--danger)"><?= L('logout') ?></a>
    </div>
  </nav>

  <!-- Main -->
  <div class="main">
    <div class="topbar">
      <span class="topbar-title">
        <?= $pages[$page]['icon'] ?? '' ?> <?= h($title) ?>
      </span>
      <span class="topbar-user">
        <?php $cur_lang = admin_lang(); $other_lang = $cur_lang === 'cs' ? 'en' : 'cs'; ?>
        <a href="?page=<?= h($page) ?>&lang=<?= $other_lang ?>"
           style="margin-right:12px;font-size:12px;opacity:.7;text-decoration:none">
          <?= $cur_lang === 'cs' ? '🇬🇧 EN' : '🇨🇿 CS' ?>
        </a>
        👤 <?= h($user) ?> &nbsp;·&nbsp;
        <a href="?page=logout"><?= L('logout') ?></a>
      </span>
    </div>

    <div class="content">
      <?php if ($flash): ?>
      <div class="alert alert-<?= h($flash['type']) ?>">
        <?= $flash['type'] === 'success' ? '✓' : '✗' ?> <?= h($flash['msg']) ?>
      </div>
      <?php endif; ?>

      <?php
      switch ($page) {
          case 'dashboard':   render_dashboard(); break;
          case 'clients':     render_clients($csrf); break;
          case 'recommended': render_json_editor(FILE_RECOMMENDED, 'recommended', $csrf,
              'Doporučené nástroje na domovské stránce aplikace.',
              'Array objektů: name, desc, nav_id, color'); break;
          case 'tray':        render_json_editor(FILE_TRAY, 'tray', $csrf,
              'Položky v menu ikony v systémové liště (pravý klik).',
              'Objekt s klíčem "tools": array objektů label, nav_id'); break;
          case 'servers':     render_json_editor(FILE_SERVERS, 'servers', $csrf,
              'Seznam serverů zobrazených na domovské stránce.',
              'Array objektů: name, ip, port, game'); break;
          case 'version':     render_json_editor(FILE_VERSION, 'version', $csrf,
              'Informace o verzi. GitHub Releases je autoritativní zdroj pro aktualizace.',
              'Objekt: version, release_date, changelog, mandatory, download_url'); break;
          case 'telemetry':   render_telemetry(); break;
          default:
              echo '<div class="alert alert-info">ℹ Stránka nenalezena.</div>';
      }
      ?>
    </div>
  </div>
</div>
</body>
</html>
    <?php
}

function render_dashboard(): void {
    $auth   = read_json(FILE_AUTH);
    $users  = $auth['users'] ?? [];
    $codes  = $auth['access_codes'] ?? [];
    $rec    = read_json(FILE_RECOMMENDED);
    $tray   = read_json(FILE_TRAY);
    $srv    = read_json(FILE_SERVERS);
    $ver    = read_json(FILE_VERSION);
    $telem  = read_json(FILE_TELEMETRY);
    $gh     = get_github_stats();
    ?>
    <!-- App overview stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value"><?= count($users) ?></div>
        <div class="stat-label"><?= L('clients') ?></div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= count($codes) ?></div>
        <div class="stat-label">Kódy</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= is_array($rec) ? count($rec) : '—' ?></div>
        <div class="stat-label">Doporučené</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= count($srv) ?></div>
        <div class="stat-label"><?= L('servers') ?></div>
      </div>
      <div class="stat-card">
        <div class="stat-value">v<?= h($ver['version'] ?? '—') ?></div>
        <div class="stat-label">Verze app</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= $telem ? ($telem['total_launches'] ?? 0) : '—' ?></div>
        <div class="stat-label"><?= L('total_launches') ?></div>
      </div>
    </div>

    <!-- GitHub stats -->
    <div class="card">
      <div class="card-title">⭐ <?= L('github_stats') ?>
        <span class="text-dim text-small" style="font-weight:normal;margin-left:8px">
          github.com/<?= GITHUB_REPO ?> · cache 30min
        </span>
      </div>
      <div class="stats-grid" style="margin-top:12px">
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $gh['stars'] !== null ? $gh['stars'] : '—' ?></div>
          <div class="stat-label">⭐ <?= L('gh_stars') ?></div>
        </div>
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $gh['forks'] !== null ? $gh['forks'] : '—' ?></div>
          <div class="stat-label">🔀 <?= L('gh_forks') ?></div>
        </div>
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $gh['watchers'] !== null ? $gh['watchers'] : '—' ?></div>
          <div class="stat-label">👁 <?= L('gh_watchers') ?></div>
        </div>
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $gh['downloads'] !== null ? $gh['downloads'] : '—' ?></div>
          <div class="stat-label">⬇ <?= L('gh_downloads') ?></div>
        </div>
      </div>
    </div>

    <!-- Telemetry overview -->
    <?php if ($telem): ?>
    <div class="card">
      <div class="card-title">📊 <?= L('telemetry_overview') ?>
        <a href="?page=telemetry" style="font-size:11px;margin-left:8px;opacity:.6">
          <?= admin_lang() === 'cs' ? 'Zobrazit vše →' : 'View all →' ?>
        </a>
      </div>
      <div class="stats-grid" style="margin-top:12px">
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $telem['total_launches'] ?? 0 ?></div>
          <div class="stat-label"><?= L('total_launches') ?></div>
        </div>
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= count($telem['unique_users'] ?? []) ?></div>
          <div class="stat-label"><?= L('unique_users') ?></div>
        </div>
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $telem['anonymous_sessions'] ?? 0 ?></div>
          <div class="stat-label"><?= L('anonymous') ?></div>
        </div>
        <div class="stat-card stat-card-sm">
          <div class="stat-value"><?= $telem['total_events'] ?? 0 ?></div>
          <div class="stat-label"><?= L('total_events') ?></div>
        </div>
      </div>

      <?php
      $panels = $telem['panels_opened'] ?? [];
      arsort($panels);
      $top = array_slice($panels, 0, 6, true);
      if ($top): ?>
      <div style="margin-top:14px">
        <div class="text-dim text-small" style="margin-bottom:6px"><?= L('top_panels') ?>:</div>
        <?php foreach ($top as $panel_id => $count):
          $max = max(array_values($top));
          $pct = $max > 0 ? round($count / $max * 100) : 0;
        ?>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;font-size:12px">
          <span style="width:110px;color:var(--text-dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            <?= h($panel_id) ?>
          </span>
          <div style="flex:1;background:#222;border-radius:3px;height:8px;overflow:hidden">
            <div style="width:<?= $pct ?>%;height:100%;background:var(--primary);border-radius:3px"></div>
          </div>
          <span style="width:28px;text-align:right;color:var(--text)"><?= $count ?></span>
        </div>
        <?php endforeach; ?>
      </div>
      <?php endif; ?>
    </div>
    <?php endif; ?>

    <!-- Quick actions -->
    <div class="card">
      <div class="card-title">📋 <?= L('quick_actions') ?></div>
      <div class="btn-row">
        <a href="?page=clients"     class="btn btn-secondary">👥 <?= L('clients') ?></a>
        <a href="?page=recommended" class="btn btn-secondary">⭐ <?= L('recommended') ?></a>
        <a href="?page=tray"        class="btn btn-secondary">📌 <?= L('tray') ?></a>
        <a href="?page=servers"     class="btn btn-secondary">📡 <?= L('servers') ?></a>
        <a href="?page=telemetry"   class="btn btn-secondary">📊 <?= L('telemetry') ?></a>
      </div>
    </div>
    <?php
}

function render_telemetry(): void {
    $telem = read_json(FILE_TELEMETRY);
    if (!$telem) { ?>
    <div class="card">
      <div class="card-title">📊 <?= L('telemetry') ?></div>
      <p class="text-dim"><?= L('no_data') ?> — telemetrie zatím nepřijala žádná data.</p>
    </div>
    <?php return; }

    $daily = $telem['daily'] ?? [];
    ksort($daily);
    $last30 = array_slice($daily, -30, 30, true);
    ?>

    <!-- Summary stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value"><?= $telem['total_launches'] ?? 0 ?></div>
        <div class="stat-label"><?= L('total_launches') ?></div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= count($telem['unique_users'] ?? []) ?></div>
        <div class="stat-label"><?= L('unique_users') ?></div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= $telem['anonymous_sessions'] ?? 0 ?></div>
        <div class="stat-label"><?= L('anonymous') ?></div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= $telem['total_events'] ?? 0 ?></div>
        <div class="stat-label"><?= L('total_events') ?></div>
      </div>
    </div>

    <!-- Daily activity chart (last 30 days) -->
    <?php if ($last30): ?>
    <div class="card">
      <div class="card-title">📅 <?= L('last_30_days') ?></div>
      <div style="display:flex;align-items:flex-end;gap:3px;height:80px;margin-top:8px;padding:0 4px">
        <?php
        $max_launches = max(array_column(array_values($last30), 'launches') ?: [1]);
        foreach ($last30 as $date => $day):
          $launches = $day['launches'] ?? 0;
          $h_pct = $max_launches > 0 ? max(4, round($launches / $max_launches * 100)) : 4;
          $day_abbr = date('d.m', strtotime($date));
        ?>
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px" title="<?= h($date) ?>: <?= $launches ?> spuštění">
          <div style="width:100%;height:<?= $h_pct ?>%;background:var(--primary);border-radius:2px 2px 0 0;min-height:4px"></div>
        </div>
        <?php endforeach; ?>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:9px;color:var(--text-dim);padding:2px 4px;margin-top:2px">
        <span><?= h(array_key_first($last30)) ?></span>
        <span><?= h(array_key_last($last30)) ?></span>
      </div>
    </div>
    <?php endif; ?>

    <!-- Top panels, versions, OS breakdown -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">

    <div class="card">
      <div class="card-title">🖥 <?= L('top_panels') ?></div>
      <?php
      $panels = $telem['panels_opened'] ?? [];
      arsort($panels);
      $top = array_slice($panels, 0, 10, true);
      $pmax = max(array_values($top) ?: [1]);
      foreach ($top as $pid => $cnt):
        $pct = round($cnt / $pmax * 100);
      ?>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:12px">
        <span style="width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text-dim)"><?= h($pid) ?></span>
        <div style="flex:1;background:#222;border-radius:3px;height:8px;overflow:hidden">
          <div style="width:<?= $pct ?>%;height:100%;background:var(--primary)"></div>
        </div>
        <span style="width:24px;text-align:right"><?= $cnt ?></span>
      </div>
      <?php endforeach; if (!$top) echo '<p class="text-dim text-small">'.L('no_data').'</p>'; ?>
    </div>

    <div class="card">
      <div class="card-title">🔢 <?= L('versions_breakdown') ?></div>
      <?php
      $vers = $telem['versions'] ?? [];
      arsort($vers);
      $vmax = max(array_values($vers) ?: [1]);
      foreach ($vers as $v => $cnt):
        $pct = round($cnt / $vmax * 100);
      ?>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:12px">
        <span style="width:50px;color:var(--text-dim)">v<?= h($v) ?></span>
        <div style="flex:1;background:#222;border-radius:3px;height:8px;overflow:hidden">
          <div style="width:<?= $pct ?>%;height:100%;background:#5b9cf6"></div>
        </div>
        <span style="width:24px;text-align:right"><?= $cnt ?></span>
      </div>
      <?php endforeach; if (!$vers) echo '<p class="text-dim text-small">'.L('no_data').'</p>'; ?>

      <div class="card-title" style="margin-top:16px">💻 <?= L('os_breakdown') ?></div>
      <?php
      $os_bd = $telem['os_breakdown'] ?? [];
      arsort($os_bd);
      $omax = max(array_values($os_bd) ?: [1]);
      foreach ($os_bd as $osname => $cnt):
        $pct = round($cnt / $omax * 100);
      ?>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:12px">
        <span style="width:70px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text-dim)"><?= h($osname) ?></span>
        <div style="flex:1;background:#222;border-radius:3px;height:8px;overflow:hidden">
          <div style="width:<?= $pct ?>%;height:100%;background:#f97316"></div>
        </div>
        <span style="width:24px;text-align:right"><?= $cnt ?></span>
      </div>
      <?php endforeach; if (!$os_bd) echo '<p class="text-dim text-small">'.L('no_data').'</p>'; ?>
    </div>

    </div><!-- /grid -->

    <p class="text-dim text-small" style="margin-top:12px">
      Poslední aktualizace: <?= h($telem['last_updated'] ?? '—') ?>
    </p>
    <?php
}

function render_clients(string $csrf): void {
    $auth  = read_json(FILE_AUTH);
    $users = $auth['users'] ?? [];
    $codes = $auth['access_codes'] ?? [];
    $me    = $_SESSION['admin_user'] ?? '';
    ?>
    <!-- Users table -->
    <div class="card">
      <div class="card-title">
        👥 Uživatelé
        <span class="badge"><?= count($users) ?></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Uživatelské jméno</th>
              <th>Role</th>
              <th>Akce</th>
            </tr>
          </thead>
          <tbody>
          <?php foreach ($users as $u):
            $name = $u['username'] ?? '?';
            $role = $u['role'] ?? 'user';
          ?>
            <tr>
              <td>
                <?= h($name) ?>
                <?php if ($name === $me): ?>
                  <span class="tag">vy</span>
                <?php endif; ?>
              </td>
              <td>
                <span class="badge-role badge-<?= $role === 'admin' ? 'admin' : 'user' ?>">
                  <?= $role === 'admin' ? 'Admin' : 'Uživatel' ?>
                </span>
              </td>
              <td>
                <!-- Edit modal trigger -->
                <button class="btn btn-secondary btn-sm"
                  onclick="openEdit('<?= h(addslashes($name)) ?>','<?= $role ?>')">
                  ✏ Upravit
                </button>
                <?php if ($name !== $me): ?>
                <form method="post" action="?page=clients" style="display:inline"
                      onsubmit="return confirm('Smazat <?= h(addslashes($name)) ?>?')">
                  <input type="hidden" name="_action" value="delete_user">
                  <input type="hidden" name="_csrf"   value="<?= h($csrf) ?>">
                  <input type="hidden" name="username" value="<?= h($name) ?>">
                  <button type="submit" class="btn btn-danger btn-sm">🗑 Smazat</button>
                </form>
                <?php endif; ?>
              </td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add user -->
    <div class="card">
      <div class="card-title">➕ Přidat uživatele</div>
      <form method="post" action="?page=clients">
        <input type="hidden" name="_action" value="add_user">
        <input type="hidden" name="_csrf"   value="<?= h($csrf) ?>">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Uživatelské jméno</label>
            <input type="text" name="username" class="form-input" required>
          </div>
          <div class="form-group">
            <label class="form-label">Heslo</label>
            <input type="text" name="password" class="form-input" required>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Role</label>
          <select name="role" class="form-select">
            <option value="user">Uživatel (přístup k Server Tools)</option>
            <option value="admin">Admin (správce + přístup k tomuto panelu)</option>
          </select>
        </div>
        <div class="btn-row">
          <button type="submit" class="btn btn-primary">➕ Přidat</button>
        </div>
      </form>
    </div>

    <!-- Access codes -->
    <div class="card">
      <div class="card-title">
        🔑 Přístupové kódy
        <span class="badge"><?= count($codes) ?></span>
      </div>
      <p class="text-dim text-small" style="margin-bottom:12px">
        Sdílené kódy — kdokoliv s kódem získá přístup k Server Tools.
      </p>
      <div class="table-wrap" style="margin-bottom:16px">
        <table>
          <thead><tr><th>Kód</th><th>Akce</th></tr></thead>
          <tbody>
          <?php foreach ($codes as $code): ?>
            <tr>
              <td><code><?= h($code) ?></code></td>
              <td>
                <form method="post" action="?page=clients" style="display:inline"
                      onsubmit="return confirm('Smazat kód?')">
                  <input type="hidden" name="_action" value="delete_code">
                  <input type="hidden" name="_csrf"   value="<?= h($csrf) ?>">
                  <input type="hidden" name="code"    value="<?= h($code) ?>">
                  <button type="submit" class="btn btn-danger btn-sm">🗑</button>
                </form>
              </td>
            </tr>
          <?php endforeach; ?>
          </tbody>
        </table>
      </div>
      <form method="post" action="?page=clients" style="display:flex;gap:8px;align-items:flex-end">
        <input type="hidden" name="_action" value="add_code">
        <input type="hidden" name="_csrf"   value="<?= h($csrf) ?>">
        <div class="form-group" style="flex:1;margin-bottom:0">
          <label class="form-label">Nový přístupový kód</label>
          <input type="text" name="code" class="form-input" placeholder="ZEDDIHUB-XYZ-2024">
        </div>
        <button type="submit" class="btn btn-primary">➕ Přidat</button>
      </form>
    </div>

    <!-- Edit modal -->
    <div id="edit-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:999;align-items:center;justify-content:center;">
      <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:28px;width:100%;max-width:400px;">
        <h3 style="color:var(--primary);margin-bottom:18px">✏ Upravit uživatele</h3>
        <form method="post" action="?page=clients">
          <input type="hidden" name="_action" value="edit_user">
          <input type="hidden" name="_csrf"   value="<?= h($csrf) ?>">
          <div class="form-group">
            <label class="form-label">Uživatelské jméno</label>
            <input type="text" id="edit-username" name="username" class="form-input" readonly
                   style="opacity:.6">
          </div>
          <div class="form-group">
            <label class="form-label">Nové heslo (prázdné = beze změny)</label>
            <input type="text" name="password" class="form-input" placeholder="nové heslo...">
          </div>
          <div class="form-group">
            <label class="form-label">Role</label>
            <select id="edit-role" name="role" class="form-select">
              <option value="user">Uživatel</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="btn-row">
            <button type="submit" class="btn btn-primary">💾 Uložit</button>
            <button type="button" class="btn btn-secondary" onclick="closeEdit()">Zrušit</button>
          </div>
        </form>
      </div>
    </div>
    <script>
    function openEdit(name, role) {
      document.getElementById('edit-username').value = name;
      document.getElementById('edit-role').value = role;
      var m = document.getElementById('edit-modal');
      m.style.display = 'flex';
    }
    function closeEdit() {
      document.getElementById('edit-modal').style.display = 'none';
    }
    </script>
    <?php
}

function render_json_editor(string $file, string $page_id, string $csrf,
                             string $desc, string $hint): void {
    $raw = file_exists($file)
        ? json_encode(json_decode(file_get_contents($file), true),
                      JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
        : '{}';
    ?>
    <div class="card">
      <div class="card-title">✏ JSON Editor</div>
      <p class="text-dim text-small" style="margin-bottom:10px"><?= h($desc) ?></p>
      <div class="alert alert-info">
        💡 Formát: <?= h($hint) ?>
      </div>
      <form method="post" action="?page=<?= h($page_id) ?>">
        <input type="hidden" name="_csrf" value="<?= h($csrf) ?>">
        <div class="json-editor-wrap">
          <textarea name="json_content" class="form-textarea" rows="22"
                    id="json-input"><?= h($raw) ?></textarea>
          <div class="json-status" id="json-status"></div>
        </div>
        <div class="btn-row">
          <button type="submit" class="btn btn-primary">💾 Uložit</button>
          <button type="button" class="btn btn-secondary" onclick="formatJson()">⟳ Formátovat</button>
          <button type="button" class="btn btn-secondary" onclick="validateJson()">✓ Ověřit JSON</button>
        </div>
      </form>
    </div>

    <?php render_json_reference($page_id); ?>

    <script>
    var ta = document.getElementById('json-input');
    var st = document.getElementById('json-status');

    function validateJson() {
      try { JSON.parse(ta.value); st.textContent = '✓ JSON je validní'; st.className = 'json-status ok'; }
      catch(e) { st.textContent = '✗ ' + e.message; st.className = 'json-status err'; }
    }
    function formatJson() {
      try { ta.value = JSON.stringify(JSON.parse(ta.value), null, 2); st.textContent = '✓ Formátováno'; st.className = 'json-status ok'; }
      catch(e) { st.textContent = '✗ ' + e.message; st.className = 'json-status err'; }
    }
    ta.addEventListener('input', function() {
      try { JSON.parse(ta.value); st.textContent = '✓'; st.className = 'json-status ok'; }
      catch(e) { st.textContent = '✗ ' + e.message; st.className = 'json-status err'; }
    });
    </script>
    <?php
}

function render_json_reference(string $page_id): void {
    $refs = [
        'recommended' => [
            'title' => 'Formát doporučených nástrojů',
            'example' => '[
  {
    "name": "CS2 Crosshair",
    "desc": "Popis nástroje",
    "nav_id": "cs2_player",
    "color": "#5b9cf6"
  }
]',
            'nav_ids' => 'cs2_player, cs2_server, cs2_keybind, csgo_player, csgo_server, csgo_keybind, rust_player, rust_server, rust_keybind, translator, pc_tools, home',
        ],
        'tray' => [
            'title' => 'Formát tray nástrojů',
            'example' => '{
  "tools": [
    { "label": "CS2 Hráčské nástroje", "nav_id": "cs2_player" },
    { "label": "Rust Server CFG",      "nav_id": "rust_server" }
  ]
}',
            'nav_ids' => 'cs2_player, cs2_server, csgo_player, csgo_server, rust_player, rust_server, translator, pc_tools, home, settings',
        ],
        'servers' => [
            'title' => 'Formát serverů',
            'example' => '[
  {
    "name": "ZeddiHub Rust #1",
    "ip": "rust1.zeddihub.eu",
    "port": 28015,
    "game": "rust"
  }
]',
            'nav_ids' => 'game: cs2 | csgo | rust',
        ],
        'version' => [
            'title' => 'Formát version.json',
            'example' => '{
  "version": "1.3.0",
  "release_date": "2026-04-11",
  "changelog": "Co je nového...",
  "mandatory": false,
  "download_url": "https://github.com/ZeddiS/..."
}',
            'nav_ids' => 'Poznámka: aplikace nyní kontroluje GitHub Releases API',
        ],
    ];

    if (!isset($refs[$page_id])) return;
    $ref = $refs[$page_id];
    ?>
    <div class="card">
      <div class="card-title">📖 <?= h($ref['title']) ?></div>
      <pre style="background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:14px;overflow-x:auto;font-size:12px;line-height:1.5;color:#ccc"><?= h($ref['example']) ?></pre>
      <p class="text-dim text-small mt-8">Platné hodnoty nav_id: <code><?= h($ref['nav_ids']) ?></code></p>
    </div>
    <?php
}
