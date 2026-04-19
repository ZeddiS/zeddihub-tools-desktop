<?php
/**
 * Export page — one-click ZIP of all JSON data files.
 * If ?download=1, streams the ZIP and exits; otherwise renders a small page.
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'export';
$PAGE_TITLE = L('export');

if (isset($_GET['download']) && $_GET['download'] === '1') {
    if (!class_exists('ZipArchive')) {
        http_response_code(500);
        die('ZipArchive extension is not available on this server.');
    }

    $files = [
        'auth.json'        => FILE_AUTH,
        'recommended.json' => FILE_RECOMMENDED,
        'tray_tools.json'  => FILE_TRAY,
        'servers.json'     => FILE_SERVERS,
        'version.json'     => FILE_VERSION,
        'telemetry.json'   => FILE_TELEMETRY,
        'news.json'        => FILE_NEWS,
    ];

    $tmp = tempnam(sys_get_temp_dir(), 'zh_export_');
    $zip = new ZipArchive();
    if ($zip->open($tmp, ZipArchive::CREATE | ZipArchive::OVERWRITE) !== true) {
        http_response_code(500);
        die('Cannot create ZIP.');
    }
    foreach ($files as $name => $path) {
        if (file_exists($path)) $zip->addFile($path, $name);
    }
    // Include audit log if present
    if (file_exists(FILE_AUDIT)) $zip->addFile(FILE_AUDIT, 'audit.log');
    $zip->close();

    audit_log('export_download');

    $filename = 'zeddihub-admin-export-' . date('Ymd-His') . '.zip';
    header('Content-Type: application/zip');
    header('Content-Disposition: attachment; filename="' . $filename . '"');
    header('Content-Length: ' . filesize($tmp));
    readfile($tmp);
    @unlink($tmp);
    exit;
}

$have_zip = class_exists('ZipArchive');

$CONTENT = function() use ($have_zip) {
?>
<div class="card">
  <div class="card-title"><?= h(L('export')) ?></div>
  <p class="text-dim" style="margin-bottom:14px"><?= h(L('export_desc')) ?></p>
  <?php if (!$have_zip): ?>
    <div class="alert alert-error">
      &#10007; PHP rozšíření <code>zip</code> není dostupné na tomto serveru.
    </div>
  <?php else: ?>
    <p class="text-dim text-small" style="margin-bottom:14px">
      Balíček obsahuje: auth.json, recommended.json, tray_tools.json, servers.json,
      version.json, telemetry.json, news.json, audit.log.
    </p>
    <div class="btn-row">
      <a href="index.php?page=export&amp;download=1" class="btn btn-primary">
        <?= h(L('export_download')) ?>
      </a>
    </div>
  <?php endif; ?>
</div>
<?php
};

require __DIR__ . '/_layout.php';
