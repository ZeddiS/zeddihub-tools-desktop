<?php
require_once __DIR__ . '/_lib.php';
require_login();
$PAGE_ID    = 'recommended';
$PAGE_TITLE = L('recommended');
$JSON_FILE  = FILE_RECOMMENDED;
$JSON_DESC  = 'Doporučené nástroje na domovské stránce aplikace.';
$JSON_HINT  = 'Array objektů: name, desc, nav_id, color';
$JSON_REF   = '[
  {
    "name": "CS2 Crosshair",
    "desc": "Popis nástroje",
    "nav_id": "cs2_player",
    "color": "#0078D4"
  }
]
// Platné nav_id: cs2_player, cs2_server, cs2_keybind, csgo_player, csgo_server,
//                csgo_keybind, rust_player, rust_server, rust_keybind,
//                translator, pc_tools, home';
require __DIR__ . '/_json_editor.php';
