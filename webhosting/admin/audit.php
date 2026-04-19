<?php
/**
 * Audit log viewer — tail audit.log (newest first).
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'audit';
$PAGE_TITLE = L('audit');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    if (($_POST['_action'] ?? '') === 'clear_log') {
        @file_put_contents(FILE_AUDIT, '');
        audit_log('audit_clear');
        flash('success', 'Audit log vyprázdněn.');
    }
    redirect('index.php?page=audit');
}

$entries = audit_tail(500);

$CONTENT = function() use ($entries) {
?>
<div class="card">
  <div class="card-title"><?= h(L('audit')) ?> <span class="badge"><?= count($entries) ?></span></div>
  <?php if (empty($entries)): ?>
    <p class="text-dim"><?= h(L('audit_empty')) ?></p>
  <?php else: ?>
    <div class="table-wrap" style="max-height:560px;overflow:auto">
      <table>
        <thead><tr><th>Čas</th><th>Uživatel</th><th>IP</th><th>Akce</th><th>Meta</th></tr></thead>
        <tbody>
        <?php foreach ($entries as $e): ?>
          <tr>
            <td><span class="text-dim text-small"><?= h($e['ts'] ?? '') ?></span></td>
            <td><?= h($e['user'] ?? '-') ?></td>
            <td><span class="text-dim text-small"><?= h($e['ip'] ?? '-') ?></span></td>
            <td><code><?= h($e['action'] ?? '-') ?></code></td>
            <td><span class="text-dim text-small"><?= h(json_encode($e['meta'] ?? [], JSON_UNESCAPED_UNICODE)) ?></span></td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <form method="post" onsubmit="return confirm('Opravdu vyprázdnit audit log?')" style="margin-top:12px">
      <input type="hidden" name="_action" value="clear_log">
      <?= csrf_input() ?>
      <button type="submit" class="btn btn-danger btn-sm">Vyprázdnit log</button>
    </form>
  <?php endif; ?>
</div>
<?php
};

require __DIR__ . '/_layout.php';
