<?php
require_once __DIR__ . '/_lib.php';
require_login();
$PAGE_ID    = 'tray';
$PAGE_TITLE = L('tray');
$JSON_FILE  = FILE_TRAY;
$JSON_DESC  = 'Položky v menu ikony v systémové liště (pravý klik).';
$JSON_HINT  = 'Objekt s klíčem "tools": array objektů label, nav_id';
$JSON_REF   = '{
  "tools": [
    { "label": "CS2 Hráčské nástroje", "nav_id": "cs2_player" },
    { "label": "Rust Server CFG",      "nav_id": "rust_server" }
  ]
}';
require __DIR__ . '/_json_editor.php';
