<?php
/**
 * Maintenance page — toggle maintenance flag + clear caches.
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'maintenance';
$PAGE_TITLE = L('maintenance');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $action = $_POST['_action'] ?? '';

    if ($action === 'toggle_maintenance') {
        if (file_exists(FILE_MAINTENANCE)) {
            @unlink(FILE_MAINTENANCE);
            audit_log('maintenance_off');
            flash('success', 'Režim údržby vypnutý.');
        } else {
            $msg = trim($_POST['message'] ?? 'Probíhá údržba. Zkuste to prosím za chvíli.');
            @file_put_contents(FILE_MAINTENANCE, json_encode([
                'since'   => date('c'),
                'by'      => $_SESSION['admin_user'] ?? '-',
                'message' => $msg,
            ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
            audit_log('maintenance_on', ['message' => $msg]);
            flash('success', 'Režim údržby aktivován.');
        }
    }

    if ($action === 'clear_cache') {
        $deleted = 0;
        foreach ([FILE_GH_CACHE, FILE_VERSION_CACHE] as $f) {
            if (file_exists($f) && @unlink($f)) $deleted++;
        }
        audit_log('cache_clear', ['deleted' => $deleted]);
        flash('success', L('cache_cleared') . " ($deleted)");
    }

    redirect('index.php?page=maintenance');
}

$in_maintenance = file_exists(FILE_MAINTENANCE);
$mnt_info = $in_maintenance ? json_read(FILE_MAINTENANCE, []) : [];

$CONTENT = function() use ($in_maintenance, $mnt_info) {
?>
<div class="card">
  <div class="card-title"><?= h(L('maintenance')) ?></div>
  <?php if ($in_maintenance): ?>
    <div class="alert alert-warning">
      &#9888; <strong><?= h(L('maintenance_on')) ?></strong>
      <?php if (!empty($mnt_info['since'])): ?>
        <span class="text-dim text-small">od <?= h($mnt_info['since']) ?></span>
      <?php endif; ?>
    </div>
    <?php if (!empty($mnt_info['message'])): ?>
      <p class="text-dim">Zpráva: <code><?= h($mnt_info['message']) ?></code></p>
    <?php endif; ?>
    <form method="post" style="margin-top:14px">
      <input type="hidden" name="_action" value="toggle_maintenance">
      <?= csrf_input() ?>
      <button type="submit" class="btn btn-primary">Vypnout údržbu</button>
    </form>
  <?php else: ?>
    <div class="alert alert-info">i <?= h(L('maintenance_off')) ?></div>
    <form method="post">
      <input type="hidden" name="_action" value="toggle_maintenance">
      <?= csrf_input() ?>
      <div class="form-group">
        <label class="form-label">Zpráva pro uživatele</label>
        <input type="text" name="message" class="form-input" value="Probíhá údržba. Zkuste to prosím za chvíli.">
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-danger">Zapnout údržbu</button>
      </div>
    </form>
  <?php endif; ?>
</div>

<div class="card">
  <div class="card-title"><?= h(L('cache_clear')) ?></div>
  <p class="text-dim text-small" style="margin-bottom:14px">
    Vymaže <code>.gh_cache.json</code> a <code>.version_cache.json</code>.
    Následující request si data znovu stáhne z GitHub API.
  </p>
  <form method="post">
    <input type="hidden" name="_action" value="clear_cache">
    <?= csrf_input() ?>
    <button type="submit" class="btn btn-secondary"><?= h(L('cache_clear')) ?></button>
  </form>
</div>
<?php
};

require __DIR__ . '/_layout.php';
