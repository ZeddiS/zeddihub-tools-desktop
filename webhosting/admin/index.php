<?php
/**
 * ZeddiHub Tools - Web Admin Panel (router)
 *
 * Entry point. Routes ?page=xxx to the matching file.
 * Auth + sidebar + layout live in _layout.php; helpers in _lib.php.
 *
 * Requirements: PHP 8.x, write access to ../data/
 */

require_once __DIR__ . '/_lib.php';

$page = $_GET['page'] ?? 'dashboard';

// ── Public pages ─────────────────────────────────────────────────────────────
if ($page === 'login') {
    require __DIR__ . '/login.php';
    exit;
}

if ($page === 'logout') {
    audit_log('logout');
    session_destroy();
    redirect('index.php?page=login');
}

// ── Protected pages ──────────────────────────────────────────────────────────
require_login();
admin_lang(); // Consume ?lang= if given

// Map page -> file
$routes = [
    'dashboard'   => 'dashboard.php',
    'news'        => 'news.php',
    'recommended' => 'recommended.php',
    'tray'        => 'tray.php',
    'servers'     => 'servers.php',
    'fileshare'   => 'fileshare.php',
    'clients'     => 'clients.php',
    'users'       => 'users.php',
    'version'     => 'version.php',
    'telemetry'   => 'telemetry.php',
    'audit'       => 'audit.php',
    'export'      => 'export.php',
    'maintenance' => 'maintenance.php',
];

$file = $routes[$page] ?? null;
if ($file === null || !file_exists(__DIR__ . '/' . $file)) {
    http_response_code(404);
    $PAGE_ID = 'dashboard';
    $PAGE_TITLE = 'Not found';
    $CONTENT = function(){
        echo '<div class="alert alert-info">Page not found.</div>';
    };
    require __DIR__ . '/_layout.php';
    exit;
}

require __DIR__ . '/' . $file;
