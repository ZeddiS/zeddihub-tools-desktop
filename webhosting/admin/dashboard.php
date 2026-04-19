<?php
/**
 * Dashboard page — KPI cards + Chart.js graphs.
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'dashboard';
$PAGE_TITLE = L('dashboard');

$auth   = json_read(FILE_AUTH, []);
$users  = $auth['users'] ?? [];
$rec    = json_read(FILE_RECOMMENDED, []);
$tray   = json_read(FILE_TRAY, []);
$srv    = json_read(FILE_SERVERS, []);
$ver    = json_read(FILE_VERSION, []);
$telem  = json_read(FILE_TELEMETRY, []);
$news   = json_read(FILE_NEWS, []);
$gh     = github_stats();

// KPI: active users = unique telem users + registered users (whichever larger)
$active_users = max(count($users), count($telem['unique_users'] ?? []));
$total_dl     = $gh['downloads'] !== null ? $gh['downloads'] : '—';
$app_ver      = $ver['version'] ?? APP_VERSION;
$open_bugs    = $gh['open_issues'] !== null ? $gh['open_issues'] : '—';

// Chart data: events over time (daily.launches, last 30 days)
$daily = $telem['daily'] ?? [];
ksort($daily);
$last30 = array_slice($daily, -30, 30, true);
$chart_dates    = array_keys($last30);
$chart_launches = array_map(fn($d) => (int)($d['launches'] ?? 0), array_values($last30));
$chart_events   = array_map(fn($d) => (int)($d['events'] ?? ($d['launches'] ?? 0)), array_values($last30));

// Panel popularity (top 8)
$panels = $telem['panels_opened'] ?? [];
arsort($panels);
$top_panels = array_slice($panels, 0, 8, true);

// OS distribution
$os_bd = $telem['os_breakdown'] ?? [];
arsort($os_bd);

$CONTENT = function() use ($users, $active_users, $total_dl, $app_ver, $open_bugs,
                          $gh, $rec, $srv, $news, $telem, $chart_dates, $chart_launches,
                          $chart_events, $top_panels, $os_bd) {
?>
<!-- KPI cards -->
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-icon kpi-icon-blue"><?= nav_icon('users') ?></div>
    <div class="kpi-body">
      <div class="kpi-value"><?= h((string)$active_users) ?></div>
      <div class="kpi-label"><?= h(L('kpi_active_users')) ?></div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon kpi-icon-purple"><?= nav_icon('zip') ?></div>
    <div class="kpi-body">
      <div class="kpi-value"><?= h((string)$total_dl) ?></div>
      <div class="kpi-label"><?= h(L('kpi_downloads')) ?></div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon kpi-icon-green"><?= nav_icon('refresh') ?></div>
    <div class="kpi-body">
      <div class="kpi-value">v<?= h((string)$app_ver) ?></div>
      <div class="kpi-label"><?= h(L('kpi_app_version')) ?></div>
    </div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon kpi-icon-orange"><?= nav_icon('bell') ?></div>
    <div class="kpi-body">
      <div class="kpi-value"><?= h((string)$open_bugs) ?></div>
      <div class="kpi-label"><?= h(L('kpi_open_bugs')) ?></div>
    </div>
  </div>
</div>

<!-- Charts row -->
<div class="grid-2">
  <div class="card">
    <div class="card-title"><?= h(L('events_over_time')) ?>
      <span class="badge"><?= h(L('last_30_days')) ?></span>
    </div>
    <canvas id="chart-events" height="180"></canvas>
    <?php if (empty($chart_dates)): ?>
      <p class="text-dim text-small mt-8"><?= h(L('no_data')) ?></p>
    <?php endif; ?>
  </div>
  <div class="card">
    <div class="card-title"><?= h(L('top_panels')) ?></div>
    <canvas id="chart-panels" height="180"></canvas>
    <?php if (empty($top_panels)): ?>
      <p class="text-dim text-small mt-8"><?= h(L('no_data')) ?></p>
    <?php endif; ?>
  </div>
</div>

<div class="grid-2">
  <div class="card">
    <div class="card-title"><?= h(L('os_breakdown')) ?></div>
    <canvas id="chart-os" height="180"></canvas>
    <?php if (empty($os_bd)): ?>
      <p class="text-dim text-small mt-8"><?= h(L('no_data')) ?></p>
    <?php endif; ?>
  </div>
  <div class="card">
    <div class="card-title"><?= h(L('github_stats')) ?>
      <span class="badge">github.com/<?= h(GITHUB_REPO) ?></span>
    </div>
    <div class="mini-stats">
      <div class="mini-stat"><span class="mini-val"><?= $gh['stars'] ?? '—' ?></span><span class="mini-lbl"><?= h(L('gh_stars')) ?></span></div>
      <div class="mini-stat"><span class="mini-val"><?= $gh['forks'] ?? '—' ?></span><span class="mini-lbl"><?= h(L('gh_forks')) ?></span></div>
      <div class="mini-stat"><span class="mini-val"><?= $gh['watchers'] ?? '—' ?></span><span class="mini-lbl"><?= h(L('gh_watchers')) ?></span></div>
      <div class="mini-stat"><span class="mini-val"><?= $gh['downloads'] ?? '—' ?></span><span class="mini-lbl"><?= h(L('gh_downloads')) ?></span></div>
    </div>
  </div>
</div>

<!-- Quick actions -->
<div class="card">
  <div class="card-title"><?= h(L('quick_actions')) ?></div>
  <div class="btn-row">
    <a href="index.php?page=news" class="btn btn-secondary"><?= h(L('news')) ?></a>
    <a href="index.php?page=clients" class="btn btn-secondary"><?= h(L('clients')) ?></a>
    <a href="index.php?page=recommended" class="btn btn-secondary"><?= h(L('recommended')) ?></a>
    <a href="index.php?page=telemetry" class="btn btn-secondary"><?= h(L('telemetry')) ?></a>
    <a href="index.php?page=export" class="btn btn-secondary"><?= h(L('export')) ?></a>
    <a href="index.php?page=maintenance" class="btn btn-secondary"><?= h(L('maintenance')) ?></a>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
(function(){
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = '#a0a0b8';
  Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
  Chart.defaults.borderColor = '#2a2a3a';

  var dates    = <?= json_encode(array_values($chart_dates)) ?>;
  var launches = <?= json_encode($chart_launches) ?>;
  var events   = <?= json_encode($chart_events) ?>;
  var panelsLbl = <?= json_encode(array_keys($top_panels)) ?>;
  var panelsVal = <?= json_encode(array_values($top_panels)) ?>;
  var osLbl = <?= json_encode(array_keys($os_bd)) ?>;
  var osVal = <?= json_encode(array_values($os_bd)) ?>;

  if (dates.length) {
    new Chart(document.getElementById('chart-events'), {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: '<?= h(L('total_launches')) ?>',
          data: launches,
          borderColor: '#0078D4',
          backgroundColor: 'rgba(0,120,212,0.18)',
          fill: true,
          tension: 0.35,
          pointRadius: 2,
        }, {
          label: '<?= h(L('total_events')) ?>',
          data: events,
          borderColor: '#6B46C1',
          backgroundColor: 'rgba(107,70,193,0.10)',
          fill: false,
          tension: 0.35,
          pointRadius: 2,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } },
        scales: {
          x: { grid: { color: '#1f1f2c' } },
          y: { grid: { color: '#1f1f2c' }, beginAtZero: true }
        }
      }
    });
  }

  if (panelsLbl.length) {
    new Chart(document.getElementById('chart-panels'), {
      type: 'bar',
      data: {
        labels: panelsLbl,
        datasets: [{
          label: '<?= h(L('top_panels')) ?>',
          data: panelsVal,
          backgroundColor: '#0078D4',
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#1f1f2c' }, beginAtZero: true },
          y: { grid: { color: '#1f1f2c' } }
        }
      }
    });
  }

  if (osLbl.length) {
    new Chart(document.getElementById('chart-os'), {
      type: 'doughnut',
      data: {
        labels: osLbl,
        datasets: [{
          data: osVal,
          backgroundColor: ['#0078D4','#6B46C1','#22c55e','#f59e0b','#ef4444','#06b6d4','#ec4899'],
          borderColor: '#1a1a26',
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'right' } },
      }
    });
  }
})();
</script>
<?php
};

require __DIR__ . '/_layout.php';
