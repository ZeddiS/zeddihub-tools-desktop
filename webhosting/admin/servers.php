<?php
require_once __DIR__ . '/_lib.php';
require_login();
$PAGE_ID    = 'servers';
$PAGE_TITLE = L('servers');
$JSON_FILE  = FILE_SERVERS;
$JSON_DESC  = 'Seznam serverů zobrazených na domovské stránce a ve Watchdogu.';
$JSON_HINT  = 'Array objektů: name, ip, port, game (cs2 | csgo | rust)';
$JSON_REF   = '[
  {
    "name": "ZeddiHub Rust #1",
    "ip": "rust1.zeddihub.eu",
    "port": 28015,
    "game": "rust"
  }
]';
require __DIR__ . '/_json_editor.php';
