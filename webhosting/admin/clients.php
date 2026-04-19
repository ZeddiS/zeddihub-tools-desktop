<?php
/**
 * Clients page — users + access codes (mirrors old behavior).
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'clients';
$PAGE_TITLE = L('clients');

// POST actions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $action = $_POST['_action'] ?? '';
    $auth = json_read(FILE_AUTH, []);
    if (!isset($auth['users']))        $auth['users'] = [];
    if (!isset($auth['access_codes'])) $auth['access_codes'] = [];

    switch ($action) {
        case 'add_user': {
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $role     = in_array($_POST['role'] ?? '', ['admin', 'user'], true) ? $_POST['role'] : 'user';
            if (!$username || !$password) { flash('error', 'Vyplňte jméno a heslo.'); break; }
            foreach ($auth['users'] as $u) {
                if (strtolower($u['username'] ?? '') === strtolower($username)) {
                    flash('error', "Uživatel '$username' již existuje.");
                    redirect('index.php?page=clients');
                }
            }
            $new = ['username' => $username, 'password' => $password];
            if ($role === 'admin') $new['role'] = 'admin';
            $auth['users'][] = $new;
            if (json_write(FILE_AUTH, $auth)) {
                audit_log('user_add', ['username' => $username, 'role' => $role]);
                flash('success', "Uživatel '$username' přidán.");
            } else flash('error', 'Chyba při ukládání.');
            break;
        }
        case 'delete_user': {
            $del = trim($_POST['username'] ?? '');
            if ($del === ($_SESSION['admin_user'] ?? '')) {
                flash('error', 'Nemůžete smazat vlastní účet.'); break;
            }
            $auth['users'] = array_values(array_filter($auth['users'],
                fn($u) => strtolower($u['username'] ?? '') !== strtolower($del)));
            if (json_write(FILE_AUTH, $auth)) {
                audit_log('user_delete', ['username' => $del]);
                flash('success', "Uživatel '$del' smazán.");
            } else flash('error', 'Chyba při ukládání.');
            break;
        }
        case 'edit_user': {
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $role     = in_array($_POST['role'] ?? '', ['admin', 'user'], true) ? $_POST['role'] : 'user';
            foreach ($auth['users'] as &$u) {
                if (strtolower($u['username'] ?? '') === strtolower($username)) {
                    if ($password) $u['password'] = $password;
                    if ($role === 'admin') $u['role'] = 'admin';
                    else unset($u['role']);
                    break;
                }
            }
            unset($u);
            if (json_write(FILE_AUTH, $auth)) {
                audit_log('user_edit', ['username' => $username, 'role' => $role]);
                flash('success', "Uživatel '$username' upraven.");
            } else flash('error', 'Chyba při ukládání.');
            break;
        }
        case 'add_code': {
            $code = trim($_POST['code'] ?? '');
            if (!$code) { flash('error', 'Zadejte kód.'); break; }
            if (in_array($code, $auth['access_codes'], true)) {
                flash('error', 'Kód již existuje.'); break;
            }
            $auth['access_codes'][] = $code;
            if (json_write(FILE_AUTH, $auth)) {
                audit_log('code_add', ['code' => $code]);
                flash('success', "Kód '$code' přidán.");
            } else flash('error', 'Chyba při ukládání.');
            break;
        }
        case 'delete_code': {
            $code = trim($_POST['code'] ?? '');
            $auth['access_codes'] = array_values(array_filter(
                $auth['access_codes'], fn($c) => $c !== $code));
            if (json_write(FILE_AUTH, $auth)) {
                audit_log('code_delete', ['code' => $code]);
                flash('success', "Kód '$code' smazán.");
            } else flash('error', 'Chyba při ukládání.');
            break;
        }
    }
    redirect('index.php?page=clients');
}

$auth  = json_read(FILE_AUTH, []);
$users = $auth['users'] ?? [];
$codes = $auth['access_codes'] ?? [];
$me    = $_SESSION['admin_user'] ?? '';
$csrf  = csrf_token();

$CONTENT = function() use ($users, $codes, $me, $csrf) {
?>
<!-- Users table -->
<div class="card">
  <div class="card-title"><?= h(L('clients')) ?> <span class="badge"><?= count($users) ?></span></div>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Username</th><th>Role</th><th>Akce</th></tr></thead>
      <tbody>
      <?php foreach ($users as $u):
        $name = $u['username'] ?? '?';
        $role = $u['role'] ?? 'user';
      ?>
        <tr>
          <td><?= h($name) ?><?php if ($name === $me): ?> <span class="tag">vy</span><?php endif; ?></td>
          <td><span class="badge-role badge-<?= $role === 'admin' ? 'admin' : 'user' ?>"><?= h(ucfirst($role)) ?></span></td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="openEdit('<?= h(addslashes($name)) ?>','<?= h($role) ?>')"><?= h(L('edit')) ?></button>
            <?php if ($name !== $me): ?>
            <form method="post" style="display:inline" onsubmit="return confirm('Smazat <?= h(addslashes($name)) ?>?')">
              <input type="hidden" name="_action" value="delete_user">
              <?= csrf_input() ?>
              <input type="hidden" name="username" value="<?= h($name) ?>">
              <button type="submit" class="btn btn-danger btn-sm"><?= h(L('delete')) ?></button>
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
  <div class="card-title"><?= h(L('add')) ?> &mdash; <?= h(L('clients')) ?></div>
  <form method="post">
    <input type="hidden" name="_action" value="add_user">
    <?= csrf_input() ?>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">Username</label>
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
        <option value="user">Uživatel (Server Tools)</option>
        <option value="admin">Admin (+ admin panel)</option>
      </select>
    </div>
    <div class="btn-row">
      <button type="submit" class="btn btn-primary"><?= h(L('add')) ?></button>
    </div>
  </form>
</div>

<!-- Access codes -->
<div class="card">
  <div class="card-title">Přístupové kódy <span class="badge"><?= count($codes) ?></span></div>
  <div class="table-wrap" style="margin-bottom:16px">
    <table>
      <thead><tr><th>Kód</th><th>Akce</th></tr></thead>
      <tbody>
      <?php foreach ($codes as $code): ?>
        <tr>
          <td><code><?= h($code) ?></code></td>
          <td>
            <form method="post" style="display:inline" onsubmit="return confirm('Smazat kód?')">
              <input type="hidden" name="_action" value="delete_code">
              <?= csrf_input() ?>
              <input type="hidden" name="code" value="<?= h($code) ?>">
              <button type="submit" class="btn btn-danger btn-sm"><?= h(L('delete')) ?></button>
            </form>
          </td>
        </tr>
      <?php endforeach; ?>
      </tbody>
    </table>
  </div>
  <form method="post" style="display:flex;gap:8px;align-items:flex-end">
    <input type="hidden" name="_action" value="add_code">
    <?= csrf_input() ?>
    <div class="form-group" style="flex:1;margin-bottom:0">
      <label class="form-label">Nový přístupový kód</label>
      <input type="text" name="code" class="form-input" placeholder="ZEDDIHUB-XYZ-2026">
    </div>
    <button type="submit" class="btn btn-primary"><?= h(L('add')) ?></button>
  </form>
</div>

<!-- Edit modal -->
<div id="edit-modal" class="modal-overlay">
  <div class="modal-card">
    <h3 style="color:var(--primary);margin-bottom:18px">Upravit uživatele</h3>
    <form method="post">
      <input type="hidden" name="_action" value="edit_user">
      <?= csrf_input() ?>
      <div class="form-group">
        <label class="form-label">Username</label>
        <input type="text" id="edit-username" name="username" class="form-input" readonly style="opacity:.6">
      </div>
      <div class="form-group">
        <label class="form-label">Nové heslo (prázdné = beze změny)</label>
        <input type="password" name="password" class="form-input" placeholder="...">
      </div>
      <div class="form-group">
        <label class="form-label">Role</label>
        <select id="edit-role" name="role" class="form-select">
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary"><?= h(L('save')) ?></button>
        <button type="button" class="btn btn-secondary" onclick="closeEdit()"><?= h(L('cancel')) ?></button>
      </div>
    </form>
  </div>
</div>
<script>
function openEdit(n, r) {
  document.getElementById('edit-username').value = n;
  document.getElementById('edit-role').value = r;
  document.getElementById('edit-modal').classList.add('open');
}
function closeEdit() { document.getElementById('edit-modal').classList.remove('open'); }
</script>
<?php
};

require __DIR__ . '/_layout.php';
