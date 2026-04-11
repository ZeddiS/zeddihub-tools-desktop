<?php
/**
 * ZeddiHub Tools - Web Admin Panel
 * Správa klientů, doporučených nástrojů, tray funkcí a serverů.
 *
 * Požadavky: PHP 7.4+, práva zápisu do ../data/
 * Nahrát na webhosting do složky /admin/
 * Data soubory musí být v /data/ (o úroveň výše od /admin/)
 */

// Session security — works with both mod_php and FastCGI/php-fpm
ini_set('session.cookie_httponly', '1');
ini_set('session.cookie_samesite', 'Strict');
if (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') {
    ini_set('session.cookie_secure', '1');
}

session_start();

// ── Configuration ────────────────────────────────────────────────────────────
define('DATA_DIR',    realpath(__DIR__ . '/../data') . '/');
define('APP_TITLE',  'ZeddiHub Admin');
define('APP_VERSION','1.3.0');

define('FILE_AUTH',        DATA_DIR . 'auth.json');
define('FILE_RECOMMENDED', DATA_DIR . 'recommended.json');
define('FILE_TRAY',        DATA_DIR . 'tray_tools.json');
define('FILE_SERVERS',     DATA_DIR . 'servers.json');
define('FILE_VERSION',     DATA_DIR . 'version.json');

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
                fn($u) => strtolower($u['username'] ?? '') !== strtolower($del)
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
                fn($c) => $c !== $code
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

    $pages = [
        'dashboard'   => ['icon' => '🏠', 'label' => 'Dashboard'],
        'clients'     => ['icon' => '👥', 'label' => 'Klienti'],
        'recommended' => ['icon' => '⭐', 'label' => 'Doporučené'],
        'tray'        => ['icon' => '📌', 'label' => 'Tray nástroje'],
        'servers'     => ['icon' => '📡', 'label' => 'Servery'],
        'version'     => ['icon' => '🔄', 'label' => 'Verze / Update'],
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
      Přihlášen: <strong><?= h($user) ?></strong><br>
      <a href="?page=logout" style="color:var(--danger)">Odhlásit</a>
    </div>
  </nav>

  <!-- Main -->
  <div class="main">
    <div class="topbar">
      <span class="topbar-title">
        <?= $pages[$page]['icon'] ?? '' ?> <?= h($title) ?>
      </span>
      <span class="topbar-user">
        👤 <?= h($user) ?> &nbsp;·&nbsp;
        <a href="?page=logout">Odhlásit</a>
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
    ?>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value"><?= count($users) ?></div>
        <div class="stat-label">Klientů (uživatelů)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= count($codes) ?></div>
        <div class="stat-label">Přístupových kódů</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= is_array($rec) ? count($rec) : '—' ?></div>
        <div class="stat-label">Doporučených nástrojů</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= count($tray['tools'] ?? []) ?></div>
        <div class="stat-label">Tray položek</div>
      </div>
      <div class="stat-card">
        <div class="stat-value"><?= count($srv) ?></div>
        <div class="stat-label">Serverů</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">v<?= h($ver['version'] ?? '—') ?></div>
        <div class="stat-label">Aktuální verze</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">📋 Rychlé akce</div>
      <div class="btn-row">
        <a href="?page=clients"     class="btn btn-secondary">👥 Spravovat klienty</a>
        <a href="?page=recommended" class="btn btn-secondary">⭐ Upravit doporučené</a>
        <a href="?page=tray"        class="btn btn-secondary">📌 Tray nástroje</a>
        <a href="?page=servers"     class="btn btn-secondary">📡 Servery</a>
      </div>
    </div>

    <div class="card">
      <div class="card-title">ℹ Nápověda</div>
      <p class="text-dim text-small">
        Data soubory jsou v adresáři <code>../data/</code> (o úroveň výše od tohoto admin panelu).<br>
        Aplikace je čte přímo přes HTTP — změny se projeví okamžitě.<br>
        Přihlásit se mohou pouze uživatelé s rolí <strong>admin</strong> v auth.json.
      </p>
    </div>
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
