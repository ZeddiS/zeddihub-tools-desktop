<?php
/**
 * ZeddiHub Tools - Telemetry endpoint.
 * Receives app events from desktop client (anonymous and authenticated).
 * Stores aggregated stats in data/telemetry.json (no personal data).
 *
 * POST body (JSON):
 *   event:   string  — "launch" | "login" | "panel_open" | "panel_close" | "export"
 *   panel:   string  — panel/nav id (optional)
 *   user:    string  — hashed username or null for anonymous
 *   version: string  — app version
 *   os:      string  — OS platform
 *
 * GET ?stats=1   → returns current aggregated stats (admin use)
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

define('TELEMETRY_FILE', __DIR__ . '/data/telemetry.json');
define('TELEMETRY_LOG',  __DIR__ . '/data/telemetry_log.json');
define('MAX_LOG_ENTRIES', 500);

function load_json($path, $default = []) {
    if (!file_exists($path)) return $default;
    $data = @json_decode(file_get_contents($path), true);
    return is_array($data) ? $data : $default;
}

function save_json($path, $data) {
    file_put_contents($path, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE), LOCK_EX);
}

// ─── GET stats ────────────────────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['stats'])) {
    $stats = load_json(TELEMETRY_FILE, []);
    echo json_encode($stats);
    exit;
}

// ─── POST event ───────────────────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$body = file_get_contents('php://input');
$payload = @json_decode($body, true);

if (!is_array($payload)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$event   = preg_replace('/[^a-z_]/', '', strtolower($payload['event'] ?? 'unknown'));
$panel   = preg_replace('/[^a-z0-9_]/', '', strtolower($payload['panel'] ?? ''));
$version = preg_replace('/[^0-9.]/', '', $payload['version'] ?? 'unknown');
$os      = preg_replace('/[^a-zA-Z0-9 _.-]/', '', $payload['os'] ?? 'unknown');
$is_anon = empty($payload['user']);
// Hash the username so we can count unique users without storing credentials
$user_hash = $is_anon ? null : substr(hash('sha256', strtolower($payload['user'])), 0, 12);

$today = date('Y-m-d');
$hour  = (int)date('G');

// ─── Update aggregated stats ──────────────────────────────────────────────────
$stats = load_json(TELEMETRY_FILE, [
    'total_events'   => 0,
    'total_launches' => 0,
    'unique_users'   => [],
    'anonymous_sessions' => 0,
    'events_by_type' => [],
    'panels_opened'  => [],
    'versions'       => [],
    'os_breakdown'   => [],
    'daily'          => [],
    'hourly'         => array_fill(0, 24, 0),
    'last_updated'   => null,
]);

$stats['total_events']++;
if (!isset($stats['events_by_type'][$event])) $stats['events_by_type'][$event] = 0;
$stats['events_by_type'][$event]++;

if ($event === 'launch') {
    $stats['total_launches']++;
    if ($is_anon) {
        $stats['anonymous_sessions']++;
    } elseif ($user_hash && !in_array($user_hash, $stats['unique_users'] ?? [])) {
        $stats['unique_users'][] = $user_hash;
    }
}

if ($panel) {
    if (!isset($stats['panels_opened'][$panel])) $stats['panels_opened'][$panel] = 0;
    $stats['panels_opened'][$panel]++;
}

if ($version) {
    if (!isset($stats['versions'][$version])) $stats['versions'][$version] = 0;
    $stats['versions'][$version]++;
}

if ($os) {
    $os_key = strtolower(substr($os, 0, 20));
    if (!isset($stats['os_breakdown'][$os_key])) $stats['os_breakdown'][$os_key] = 0;
    $stats['os_breakdown'][$os_key]++;
}

// Daily stats
if (!isset($stats['daily'][$today])) $stats['daily'][$today] = ['events' => 0, 'launches' => 0];
$stats['daily'][$today]['events']++;
if ($event === 'launch') $stats['daily'][$today]['launches']++;

// Trim daily to last 90 days
if (count($stats['daily']) > 90) {
    ksort($stats['daily']);
    $stats['daily'] = array_slice($stats['daily'], -90, 90, true);
}

// Hourly
if (!isset($stats['hourly']) || !is_array($stats['hourly']) || count($stats['hourly']) !== 24) {
    $stats['hourly'] = array_fill(0, 24, 0);
}
$stats['hourly'][$hour]++;

$stats['last_updated'] = date('c');

save_json(TELEMETRY_FILE, $stats);

// ─── Append to rolling log ────────────────────────────────────────────────────
$log = load_json(TELEMETRY_LOG, []);
$log[] = [
    'ts'      => date('c'),
    'event'   => $event,
    'panel'   => $panel ?: null,
    'version' => $version,
    'os'      => $os,
    'anon'    => $is_anon,
];
// Keep only last MAX_LOG_ENTRIES
if (count($log) > MAX_LOG_ENTRIES) {
    $log = array_slice($log, -MAX_LOG_ENTRIES);
}
save_json(TELEMETRY_LOG, $log);

echo json_encode(['ok' => true]);
