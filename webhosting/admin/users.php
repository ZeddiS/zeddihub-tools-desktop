<?php
/**
 * Users page — focused on the auth.json users array with a plaintext warning.
 *
 * This is mostly a UX wrapper around clients.php: same JSON field, but this
 * page makes the security caveat obvious and exposes password-type inputs.
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'users';
$PAGE_TITLE = L('users');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $action = $_POST['_action'] ?? '';
    $auth = json_read(FILE_AUTH, []);
    if (!isset($auth['users'])) $auth['users'] = [];

    if ($action === 'save_user') {
        $username = trim($_POST['username'] ?? '');
        $password = $_POST['password'] ?? '';
        $role     = in_array($_POST['role'] ?? '', ['admin','user'], true) ? $_POST['role'] : 'user';
        $original = trim($_POST['original'] ?? '');

        if ($username === '') {
            flash('error', 'Username je povinný.');
            redirect('index.php?page=users');
        }

        $found = false;
        foreach ($auth['users'] as &$u) {
            $uname = $u['username'] ?? '';
            if ($original !== '' && strtolower($uname) === strtolower($original)) {
                $u['username'] = $username;
                if ($password !== '') $u['password'] = $password;
                if ($role === 'admin') $u['role'] = 'admin'; else unset($u['role']);
                $found = true;
                break;
            }
        }
        unset($u);

        if (!$found) {
            foreach ($auth['users'] as $u) {
                if (strtolower($u['username'] ?? '') === strtolower($username)) {
                    flash('error', "Uživatel '$username' již existuje.");
                    redirect('index.php?page=users');
                }
            }
            if ($password === '') {
                flash('error', 'Heslo je povinné pro nový účet.');
                redirect('index.php?page=users');
            }
            $new = ['username' => $username, 'password' => $password];
            if ($role === 'admin') $new['role'] = 'admin';
            $auth['users'][] = $new;
        }

        if (json_write(FILE_AUTH, $auth)) {
            audit_log($found ? 'user_edit' : 'user_add',
                      ['username' => $username, 'role' => $role]);
            flash('success', 'Uloženo.');
        } else flash('error', 'Chyba při ukládání.');
    }

    if ($action === 'delete_user') {
        $del = trim($_POST['username'] ?? '');
        if ($del === ($_SESSION['admin_user'] ?? '')) {
            flash('error', 'Nemůžete smazat vlastní účet.');
            redirect('index.php?page=users');
        }
        $auth['users'] = array_values(array_filter($auth['users'],
            fn($u) => strtolower($u['username'] ?? '') !== strtolower($del)));
        if (json_write(FILE_AUTH, $auth)) {
            audit_log('user_delete', ['username' => $del]);
            flash('success', "Uživatel '$del' smazán.");
        } else flash('error', 'Chyba při ukládání.');
    }
    redirect('index.php?page=users');
}

$auth  = json_read(FILE_AUTH, []);
$users = $auth['users'] ?? [];
$me    = $_SESSION['admin_user'] ?? '';

$CONTENT = function() use ($users, $me) {
?>
<div class="alert alert-warning">
  &#9888; <?= h(L('plain_password_warning')) ?>
</div>

<div class="card">
  <div class="card-title"><?= h(L('users')) ?> <span class="badge"><?= count($users) ?></span></div>
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
            <button class="btn btn-secondary btn-sm"
              onclick="openUserModal('<?= h(addslashes($name)) ?>','<?= h($role) ?>')"><?= h(L('edit')) ?></button>
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
  <div class="btn-row">
    <button type="button" class="btn btn-primary" onclick="openUserModal('','user')">
      + <?= h(L('add')) ?>
    </button>
  </div>
</div>

<div id="user-modal" class="modal-overlay">
  <div class="modal-card">
    <h3 style="color:var(--primary);margin-bottom:14px" id="user-modal-title"><?= h(L('edit')) ?></h3>
    <form method="post">
      <input type="hidden" name="_action" value="save_user">
      <?= csrf_input() ?>
      <input type="hidden" name="original" id="user-original">
      <div class="form-group">
        <label class="form-label">Username</label>
        <input type="text" name="username" id="user-name" class="form-input" required>
      </div>
      <div class="form-group">
        <label class="form-label">
          Heslo <span class="text-dim text-small">(prázdné = beze změny, povinné pro nový účet)</span>
        </label>
        <input type="password" name="password" id="user-pass" class="form-input" autocomplete="new-password">
      </div>
      <div class="form-group">
        <label class="form-label">Role</label>
        <select name="role" id="user-role" class="form-select">
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary"><?= h(L('save')) ?></button>
        <button type="button" class="btn btn-secondary" onclick="closeUserModal()"><?= h(L('cancel')) ?></button>
      </div>
    </form>
  </div>
</div>
<script>
function openUserModal(name, role) {
  document.getElementById('user-original').value = name;
  document.getElementById('user-name').value = name;
  document.getElementById('user-pass').value = '';
  document.getElementById('user-role').value = role || 'user';
  document.getElementById('user-modal-title').textContent = name ? 'Upravit: ' + name : 'Nový uživatel';
  document.getElementById('user-modal').classList.add('open');
}
function closeUserModal() { document.getElementById('user-modal').classList.remove('open'); }
</script>
<?php
};

require __DIR__ . '/_layout.php';
