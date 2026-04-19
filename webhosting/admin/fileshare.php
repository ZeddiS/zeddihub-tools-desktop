<?php
/**
 * File Share browser — read-only listing of DIR_FILESHARE.
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'fileshare';
$PAGE_TITLE = L('fileshare');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    if (($_POST['_action'] ?? '') === 'delete_file') {
        $name = basename($_POST['name'] ?? '');
        if ($name !== '' && strpos($name, '..') === false) {
            $path = DIR_FILESHARE . DIRECTORY_SEPARATOR . $name;
            if (is_file($path) && @unlink($path)) {
                audit_log('fileshare_delete', ['file' => $name]);
                flash('success', "Smazáno: $name");
            } else {
                flash('error', 'Nelze smazat.');
            }
        }
    }
    redirect('index.php?page=fileshare');
}

$files = [];
if (is_dir(DIR_FILESHARE)) {
    foreach (scandir(DIR_FILESHARE) as $f) {
        if ($f === '.' || $f === '..' || $f[0] === '.') continue;
        $path = DIR_FILESHARE . DIRECTORY_SEPARATOR . $f;
        if (is_file($path)) {
            $files[] = [
                'name' => $f,
                'size' => filesize($path),
                'mtime'=> filemtime($path),
            ];
        }
    }
    usort($files, fn($a, $b) => $b['mtime'] <=> $a['mtime']);
}

function _fmt_size(int $b): string {
    if ($b < 1024) return $b . ' B';
    if ($b < 1048576) return round($b / 1024, 1) . ' KB';
    if ($b < 1073741824) return round($b / 1048576, 1) . ' MB';
    return round($b / 1073741824, 2) . ' GB';
}

$CONTENT = function() use ($files) {
?>
<div class="card">
  <div class="card-title"><?= h(L('fileshare')) ?> <span class="badge"><?= count($files) ?></span></div>
  <p class="text-dim text-small" style="margin-bottom:10px">
    Složka: <code><?= h(DIR_FILESHARE) ?></code>
  </p>
  <?php if (!is_dir(DIR_FILESHARE)): ?>
    <div class="alert alert-info">
      i Složka <code>fileshare/</code> neexistuje. Bude vytvořena automaticky, jakmile File Share zpracuje první upload.
    </div>
  <?php elseif (empty($files)): ?>
    <p class="text-dim"><?= h(L('fileshare_empty')) ?></p>
  <?php else: ?>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Soubor</th><th>Velikost</th><th>Nahráno</th><th>Akce</th></tr></thead>
        <tbody>
        <?php foreach ($files as $f): ?>
          <tr>
            <td><?= h($f['name']) ?></td>
            <td><?= _fmt_size($f['size']) ?></td>
            <td><span class="text-dim text-small"><?= h(date('Y-m-d H:i', $f['mtime'])) ?></span></td>
            <td>
              <form method="post" style="display:inline" onsubmit="return confirm('Smazat <?= h(addslashes($f['name'])) ?>?')">
                <input type="hidden" name="_action" value="delete_file">
                <?= csrf_input() ?>
                <input type="hidden" name="name" value="<?= h($f['name']) ?>">
                <button type="submit" class="btn btn-danger btn-sm"><?= h(L('delete')) ?></button>
              </form>
            </td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
    </div>
  <?php endif; ?>
</div>
<?php
};

require __DIR__ . '/_layout.php';
