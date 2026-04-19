<?php
/**
 * ZeddiHub Admin - Shared library
 * Helpers: session bootstrap, CSRF, JSON I/O (atomic), flash, GitHub stats,
 * audit log, language, auth guards.
 *
 * PHP 8.x. No composer deps. Safe for cPanel-style shared hosting.
 */

// ── Session (mod_php + FastCGI) ──────────────────────────────────────────────
if (session_status() === PHP_SESSION_NONE) {
    $_session_opts = ['cookie_httponly' => true];
    if (PHP_VERSION_ID >= 70300) {
        $_session_opts['cookie_samesite'] = 'Strict';
    }
    if (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') {
        $_session_opts['cookie_secure'] = true;
    }
    session_start($_session_opts);
}

// ── Configuration ────────────────────────────────────────────────────────────
$_data_path = realpath(__DIR__ . '/../data');
if ($_data_path === false) {
    $_data_path = dirname(__DIR__) . '/data';
}
if (!defined('DATA_DIR'))      define('DATA_DIR', rtrim($_data_path, '/\\') . '/');
if (!defined('APP_TITLE'))     define('APP_TITLE', 'ZeddiHub Admin');
if (!defined('APP_VERSION'))   define('APP_VERSION', '1.9.0');
if (!defined('GITHUB_REPO'))   define('GITHUB_REPO', 'ZeddiS/zeddihub_tools_desktop');

if (!defined('FILE_AUTH'))        define('FILE_AUTH',        DATA_DIR . 'auth.json');
if (!defined('FILE_RECOMMENDED')) define('FILE_RECOMMENDED', DATA_DIR . 'recommended.json');
if (!defined('FILE_TRAY'))        define('FILE_TRAY',        DATA_DIR . 'tray_tools.json');
if (!defined('FILE_SERVERS'))     define('FILE_SERVERS',     DATA_DIR . 'servers.json');
if (!defined('FILE_VERSION'))     define('FILE_VERSION',     DATA_DIR . 'version.json');
if (!defined('FILE_TELEMETRY'))   define('FILE_TELEMETRY',   DATA_DIR . 'telemetry.json');
if (!defined('FILE_NEWS'))        define('FILE_NEWS',        DATA_DIR . 'news.json');
if (!defined('FILE_GH_CACHE'))    define('FILE_GH_CACHE',    DATA_DIR . '.gh_cache.json');
if (!defined('FILE_VERSION_CACHE')) define('FILE_VERSION_CACHE', DATA_DIR . '.version_cache.json');
if (!defined('FILE_MAINTENANCE')) define('FILE_MAINTENANCE', DATA_DIR . '.maintenance');
if (!defined('FILE_AUDIT'))       define('FILE_AUDIT',       DATA_DIR . 'audit.log');
if (!defined('DIR_FILESHARE'))    define('DIR_FILESHARE',    DATA_DIR . 'fileshare');

// ── Startup check ────────────────────────────────────────────────────────────
if (!is_dir(DATA_DIR)) {
    http_response_code(503);
    echo '<!DOCTYPE html><meta charset="UTF-8"><title>Setup error</title>';
    echo '<body style="font-family:Segoe UI;background:#0a0a0f;color:#e8e8e8;padding:40px">';
    echo '<h2 style="color:#0078D4">Data folder missing</h2>';
    echo '<p>Expected path: <code>' . htmlspecialchars(DATA_DIR) . '</code></p>';
    echo '</body>';
    exit;
}

// ── Basic helpers ────────────────────────────────────────────────────────────
function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

function redirect(string $url): void {
    header("Location: $url");
    exit;
}

// ── CSRF ─────────────────────────────────────────────────────────────────────
function csrf_token(): string {
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['csrf'];
}

function csrf_check(): void {
    if (($_POST['_csrf'] ?? '') !== ($_SESSION['csrf'] ?? '')) {
        http_response_code(403);
        die('CSRF check failed.');
    }
}

function csrf_input(): string {
    return '<input type="hidden" name="_csrf" value="' . h(csrf_token()) . '">';
}

// ── JSON I/O (atomic) ────────────────────────────────────────────────────────
function json_read(string $path, $default = []): mixed {
    if (!file_exists($path)) return $default;
    $raw = @file_get_contents($path);
    if ($raw === false) return $default;
    $data = json_decode($raw, true);
    return $data ?? $default;
}

/**
 * Atomic JSON write: serialize, write to tmp in same dir, rename over target.
 * Returns bool success.
 */
function json_write(string $path, $data): bool {
    $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($json === false) return false;
    $dir = dirname($path);
    if (!is_dir($dir)) return false;
    $tmp = $dir . DIRECTORY_SEPARATOR . '.' . basename($path) . '.tmp.' . bin2hex(random_bytes(4));
    if (@file_put_contents($tmp, $json) === false) return false;
    // Windows rename won't overwrite existing file; remove first.
    if (file_exists($path) && stripos(PHP_OS, 'WIN') === 0) {
        @unlink($path);
    }
    if (!@rename($tmp, $path)) {
        @unlink($tmp);
        return false;
    }
    return true;
}

// Legacy aliases used by the old monolithic index.php handlers.
function read_json(string $path): array {
    $d = json_read($path, []);
    return is_array($d) ? $d : [];
}
function write_json(string $path, $data): bool {
    return json_write($path, $data);
}

// ── Flash ────────────────────────────────────────────────────────────────────
function flash(string $type, string $msg): void {
    $_SESSION['flash'] = ['type' => $type, 'msg' => $msg];
}
function get_flash(): ?array {
    $f = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $f;
}

// ── Auth ─────────────────────────────────────────────────────────────────────
function require_login(): void {
    if (empty($_SESSION['admin_user'])) {
        redirect('index.php?page=login');
    }
}

function do_login(string $username, string $password): bool {
    $auth = json_read(FILE_AUTH, []);
    foreach ($auth['users'] ?? [] as $user) {
        if (
            strtolower($user['username'] ?? '') === strtolower($username)
            && ($user['password'] ?? '') === $password
            && ($user['role'] ?? '') === 'admin'
        ) {
            $_SESSION['admin_user'] = $user['username'];
            audit_log('login', ['user' => $user['username']]);
            return true;
        }
    }
    audit_log('login_failed', ['username' => $username]);
    return false;
}

// ── Language ─────────────────────────────────────────────────────────────────
function admin_lang(): string {
    if (isset($_GET['lang']) && in_array($_GET['lang'], ['cs', 'en'], true)) {
        $_SESSION['admin_lang'] = $_GET['lang'];
    }
    return $_SESSION['admin_lang'] ?? 'cs';
}

function L(string $key): string {
    static $strings = null;
    if ($strings === null) {
        $strings = [
            'cs' => [
                // Sidebar sections
                'sec_overview'   => 'Přehled',
                'sec_content'    => 'Obsah',
                'sec_users'      => 'Uživatelé',
                'sec_system'     => 'Systém',
                // Pages
                'dashboard'      => 'Dashboard',
                'news'           => 'Novinky',
                'recommended'    => 'Doporučené',
                'tray'           => 'Tray menu',
                'servers'        => 'Servery',
                'fileshare'      => 'File Share',
                'clients'        => 'Klienti',
                'users'          => 'Uživatelé (auth)',
                'version'        => 'Verze / Update',
                'telemetry'      => 'Telemetrie',
                'audit'          => 'Audit log',
                'export'         => 'Export dat',
                'maintenance'    => 'Údržba',
                // Common
                'logged_as'      => 'Přihlášen',
                'logout'         => 'Odhlásit',
                'save'           => 'Uložit',
                'cancel'         => 'Zrušit',
                'delete'         => 'Smazat',
                'edit'           => 'Upravit',
                'add'            => 'Přidat',
                'no_data'        => 'Žádná data',
                // Dashboard
                'kpi_active_users'   => 'Aktivní uživatelé',
                'kpi_downloads'      => 'Stažení celkem',
                'kpi_app_version'    => 'Verze aplikace',
                'kpi_open_bugs'      => 'Otevřené chyby',
                'quick_actions'      => 'Rychlé akce',
                'github_stats'       => 'GitHub statistiky',
                'telemetry_overview' => 'Přehled telemetrie',
                'total_launches'     => 'Celkem spuštění',
                'unique_users'       => 'Jedinečných uživatelů',
                'anonymous'          => 'Anonymních relací',
                'total_events'       => 'Celkem událostí',
                'top_panels'         => 'Nejpoužívanější panely',
                'versions_breakdown' => 'Verze klientů',
                'os_breakdown'       => 'Operační systémy',
                'last_30_days'       => 'Posledních 30 dní',
                'events_over_time'   => 'Události v čase',
                'gh_stars'           => 'Hvězdičky',
                'gh_forks'           => 'Forky',
                'gh_watchers'        => 'Sledující',
                'gh_downloads'       => 'Stažení (.exe)',
                // Users page
                'plain_password_warning' => 'Hesla jsou ukládána v čitelné podobě (JSON). Nepoužívejte stejné heslo jako jinde.',
                // Maintenance
                'maintenance_on'     => 'Režim údržby je AKTIVNÍ',
                'maintenance_off'    => 'Režim údržby je vypnutý',
                'cache_clear'        => 'Vymazat cache',
                'cache_cleared'      => 'Cache vymazaná.',
                // News
                'news_empty'         => 'Žádné novinky. Přidejte první záznam.',
                // Fileshare
                'fileshare_empty'    => 'Žádné soubory. File Share zatím nepřijal žádné nahrávky.',
                // Audit
                'audit_empty'        => 'Audit log je prázdný.',
                // Export
                'export_desc'        => 'Stáhnout všechny JSON data soubory jako ZIP.',
                'export_download'    => 'Stáhnout ZIP',
            ],
            'en' => [
                'sec_overview'   => 'Overview',
                'sec_content'    => 'Content',
                'sec_users'      => 'Users',
                'sec_system'     => 'System',
                'dashboard'      => 'Dashboard',
                'news'           => 'News',
                'recommended'    => 'Recommended',
                'tray'           => 'Tray menu',
                'servers'        => 'Servers',
                'fileshare'      => 'File Share',
                'clients'        => 'Clients',
                'users'          => 'Users (auth)',
                'version'        => 'Version / Update',
                'telemetry'      => 'Telemetry',
                'audit'          => 'Audit log',
                'export'         => 'Data export',
                'maintenance'    => 'Maintenance',
                'logged_as'      => 'Logged in as',
                'logout'         => 'Log out',
                'save'           => 'Save',
                'cancel'         => 'Cancel',
                'delete'         => 'Delete',
                'edit'           => 'Edit',
                'add'            => 'Add',
                'no_data'        => 'No data',
                'kpi_active_users'   => 'Active users',
                'kpi_downloads'      => 'Total downloads',
                'kpi_app_version'    => 'App version',
                'kpi_open_bugs'      => 'Open bugs',
                'quick_actions'      => 'Quick actions',
                'github_stats'       => 'GitHub statistics',
                'telemetry_overview' => 'Telemetry overview',
                'total_launches'     => 'Total launches',
                'unique_users'       => 'Unique users',
                'anonymous'          => 'Anonymous sessions',
                'total_events'       => 'Total events',
                'top_panels'         => 'Top panels',
                'versions_breakdown' => 'Client versions',
                'os_breakdown'       => 'Operating systems',
                'last_30_days'       => 'Last 30 days',
                'events_over_time'   => 'Events over time',
                'gh_stars'           => 'Stars',
                'gh_forks'           => 'Forks',
                'gh_watchers'        => 'Watchers',
                'gh_downloads'       => 'Downloads (.exe)',
                'plain_password_warning' => 'Passwords are stored in plaintext (JSON). Do not reuse passwords from elsewhere.',
                'maintenance_on'     => 'Maintenance mode is ACTIVE',
                'maintenance_off'    => 'Maintenance mode is OFF',
                'cache_clear'        => 'Clear cache',
                'cache_cleared'      => 'Cache cleared.',
                'news_empty'         => 'No news yet. Add the first entry.',
                'fileshare_empty'    => 'No files. File Share has not received any uploads.',
                'audit_empty'        => 'Audit log is empty.',
                'export_desc'        => 'Download all JSON data files as a ZIP.',
                'export_download'    => 'Download ZIP',
            ],
        ];
    }
    $lang = admin_lang();
    return $strings[$lang][$key] ?? $strings['cs'][$key] ?? $key;
}

// ── GitHub stats (cached 30 min) ─────────────────────────────────────────────
function github_stats(bool $force = false): array {
    if (!$force && file_exists(FILE_GH_CACHE)) {
        $cache = @json_decode(@file_get_contents(FILE_GH_CACHE), true);
        if (is_array($cache) && isset($cache['_ts']) && (time() - $cache['_ts']) < 1800) {
            return $cache;
        }
    }

    $repo = GITHUB_REPO;
    $stats = ['_ts' => time(), 'stars' => null, 'forks' => null, 'watchers' => null,
              'downloads' => null, 'open_issues' => null];

    $repo_data = _gh_fetch("https://api.github.com/repos/$repo");
    if ($repo_data) {
        $stats['stars']       = (int)($repo_data['stargazers_count'] ?? 0);
        $stats['forks']       = (int)($repo_data['forks_count'] ?? 0);
        $stats['watchers']    = (int)($repo_data['watchers_count'] ?? 0);
        $stats['open_issues'] = (int)($repo_data['open_issues_count'] ?? 0);
    }

    $releases = _gh_fetch("https://api.github.com/repos/$repo/releases");
    if (is_array($releases)) {
        $total = 0;
        foreach ($releases as $rel) {
            foreach ($rel['assets'] ?? [] as $asset) {
                $name = strtolower($asset['name'] ?? '');
                if (substr($name, -4) === '.exe') {
                    $total += (int)($asset['download_count'] ?? 0);
                }
            }
        }
        $stats['downloads'] = $total;
    }

    @file_put_contents(FILE_GH_CACHE, json_encode($stats));
    return $stats;
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
        $ctx = stream_context_create([
            'http' => ['header' => "User-Agent: ZeddiHub-Admin/1.0\r\n", 'timeout' => 8]
        ]);
        $body = @file_get_contents($url, false, $ctx);
        if ($body) return @json_decode($body, true);
    }
    return null;
}

// ── Audit log ────────────────────────────────────────────────────────────────
function audit_log(string $action, array $meta = []): void {
    $entry = [
        'ts'     => date('c'),
        'user'   => $_SESSION['admin_user'] ?? '-',
        'ip'     => $_SERVER['REMOTE_ADDR'] ?? '-',
        'action' => $action,
        'meta'   => $meta,
    ];
    $line = json_encode($entry, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n";
    @file_put_contents(FILE_AUDIT, $line, FILE_APPEND | LOCK_EX);
}

function audit_tail(int $lines = 200): array {
    if (!file_exists(FILE_AUDIT)) return [];
    $size = filesize(FILE_AUDIT);
    if ($size === 0) return [];
    // Simple tail: read whole file for small logs (cPanel constraint).
    // Safe up to several MB.
    $raw = @file_get_contents(FILE_AUDIT);
    if ($raw === false) return [];
    $parts = preg_split('/\r?\n/', trim($raw));
    $parts = array_slice($parts, -$lines);
    $out = [];
    foreach ($parts as $p) {
        if ($p === '') continue;
        $d = json_decode($p, true);
        if ($d) $out[] = $d;
    }
    return array_reverse($out);
}

// ── Sidebar nav definition (used by _layout.php) ─────────────────────────────
function sidebar_nav(): array {
    return [
        'overview' => [
            'label' => L('sec_overview'),
            'items' => [
                'dashboard' => ['icon' => 'home',   'label' => L('dashboard')],
            ],
        ],
        'content' => [
            'label' => L('sec_content'),
            'items' => [
                'news'        => ['icon' => 'bell',    'label' => L('news')],
                'recommended' => ['icon' => 'star',    'label' => L('recommended')],
                'tray'        => ['icon' => 'pin',     'label' => L('tray')],
                'servers'     => ['icon' => 'server',  'label' => L('servers')],
                'fileshare'   => ['icon' => 'folder',  'label' => L('fileshare')],
            ],
        ],
        'users' => [
            'label' => L('sec_users'),
            'items' => [
                'clients' => ['icon' => 'users',  'label' => L('clients')],
                'users'   => ['icon' => 'key',    'label' => L('users')],
            ],
        ],
        'system' => [
            'label' => L('sec_system'),
            'items' => [
                'version'     => ['icon' => 'refresh', 'label' => L('version')],
                'telemetry'   => ['icon' => 'chart',   'label' => L('telemetry')],
                'audit'       => ['icon' => 'log',     'label' => L('audit')],
                'export'      => ['icon' => 'zip',     'label' => L('export')],
                'maintenance' => ['icon' => 'wrench',  'label' => L('maintenance')],
            ],
        ],
    ];
}

// SVG sidebar icons (monochrome, currentColor) — no external font/image deps.
function nav_icon(string $name): string {
    $icons = [
        'home'    => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z"/></svg>',
        'bell'    => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 16v-5a6 6 0 1 0-12 0v5l-2 2h16z"/><path d="M10 20a2 2 0 0 0 4 0"/></svg>',
        'star'    => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="m12 3 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.8 6.2 20.9l1.1-6.5L2.6 9.8l6.5-.9z"/></svg>',
        'pin'     => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"/><path d="M5 3h14l-2 7 3 3H4l3-3z"/></svg>',
        'server'  => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><circle cx="7" cy="7.5" r=".6" fill="currentColor"/><circle cx="7" cy="16.5" r=".6" fill="currentColor"/></svg>',
        'folder'  => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2h9A1.5 1.5 0 0 1 21 8.5v10A1.5 1.5 0 0 1 19.5 20h-15A1.5 1.5 0 0 1 3 18.5z"/></svg>',
        'users'   => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.5-5.5 6.5-5.5s5.7 2 6.5 5.5"/><circle cx="17" cy="9" r="2.8"/><path d="M15 14.5c3 .2 5.3 2 6 5.5"/></svg>',
        'key'     => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="14" r="4"/><path d="m11 11 9-9m-4 4 3 3m-5-1 3 3"/></svg>',
        'refresh' => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 13.7-5.7L20 9"/><path d="M20 4v5h-5"/><path d="M20 12a8 8 0 0 1-13.7 5.7L4 15"/><path d="M4 20v-5h5"/></svg>',
        'chart'   => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/></svg>',
        'log'     => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h11l3 3v15H5z"/><path d="M8 9h8M8 13h8M8 17h5"/></svg>',
        'zip'     => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h9l5 5v13H5z"/><path d="M14 3v5h5"/><path d="M10 11v2M10 15v2M10 19v1"/></svg>',
        'wrench'  => '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a4 4 0 0 1 5 5l-9.7 9.7-4-1-1-4z"/><path d="m7 17 2 2"/></svg>',
    ];
    return $icons[$name] ?? '<span></span>';
}
