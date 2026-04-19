<?php
require_once __DIR__ . '/_lib.php';
require_login();
$PAGE_ID    = 'version';
$PAGE_TITLE = L('version');
$JSON_FILE  = FILE_VERSION;
$JSON_DESC  = 'Informace o verzi. GitHub Releases je autoritativní zdroj pro aktualizace.';
$JSON_HINT  = 'Objekt: version, release_date, changelog, mandatory, download_url';
$JSON_REF   = '{
  "version": "1.9.0",
  "release_date": "2026-04-19",
  "changelog": "Co je nového...",
  "mandatory": false,
  "download_url": "https://github.com/ZeddiS/zeddihub_tools_desktop/releases/latest"
}';
require __DIR__ . '/_json_editor.php';
