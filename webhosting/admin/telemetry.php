<?php
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'telemetry';
$PAGE_TITLE = L('telemetry');

$telem = json_read(FILE_TELEMETRY, []);

$CONTENT = function() use ($telem) {
    if (!$telem) {
        echo '<div class="card"><div class="card-title">'.h(L('telemetry')).'</div>'
           . '<p class="text-dim">'.h(L('no_data')).'</p></div>';
        return;
    }
    $daily = $telem['daily'] ?? [];
    ksort($daily);
    $last30 = array_slice($daily, -30, 30, true);
?>
<div class="stats-grid">
  <div class="stat-card"><div class="stat-value"><?= $telem['total_launches'] ?? 0 ?></div><div class="stat-label"><?= h(L('total_launches')) ?></div></div>
  <div class="stat-card"><div class="stat-value"><?= count($telem['unique_users'] ?? []) ?></div><div class="stat-label"><?= h(L('unique_users')) ?></div></div>
  <div class="stat-card"><div class="stat-value"><?= $telem['anonymous_sessions'] ?? 0 ?></div><div class="stat-label"><?= h(L('anonymous')) ?></div></div>
  <div class="stat-card"><div class="stat-value"><?= $telem['total_events'] ?? 0 ?></div><div class="stat-label"><?= h(L('total_events')) ?></div></div>
</div>

<?php if ($last30): ?>
<div class="card">
  <div class="card-title"><?= h(L('last_30_days')) ?></div>
  <canvas id="chart-daily" height="120"></canvas>
</div>
<?php endif; ?>

<div class="grid-2">
  <div class="card">
    <div class="card-title"><?= h(L('top_panels')) ?></div>
    <?php
    $panels = $telem['panels_opened'] ?? [];
    arsort($panels);
    $top = array_slice($panels, 0, 10, true);
    $pmax = max(array_values($top) ?: [1]);
    foreach ($top as $pid => $cnt):
      $pct = round($cnt / $pmax * 100);
    ?>
    <div class="bar-row">
      <span class="bar-label"><?= h($pid) ?></span>
      <div class="bar-track"><div class="bar-fill" style="width:<?= $pct ?>%"></div></div>
      <span class="bar-val"><?= $cnt ?></span>
    </div>
    <?php endforeach; if (!$top) echo '<p class="text-dim text-small">'.h(L('no_data')).'</p>'; ?>
  </div>
  <div class="card">
    <div class="card-title"><?= h(L('versions_breakdown')) ?></div>
    <?php
    $vers = $telem['versions'] ?? [];
    arsort($vers);
    $vmax = max(array_values($vers) ?: [1]);
    foreach ($vers as $v => $cnt):
      $pct = round($cnt / $vmax * 100);
    ?>
    <div class="bar-row">
      <span class="bar-label">v<?= h($v) ?></span>
      <div class="bar-track"><div class="bar-fill bar-fill-purple" style="width:<?= $pct ?>%"></div></div>
      <span class="bar-val"><?= $cnt ?></span>
    </div>
    <?php endforeach; if (!$vers) echo '<p class="text-dim text-small">'.h(L('no_data')).'</p>'; ?>

    <div class="card-title" style="margin-top:16px"><?= h(L('os_breakdown')) ?></div>
    <?php
    $os_bd = $telem['os_breakdown'] ?? [];
    arsort($os_bd);
    $omax = max(array_values($os_bd) ?: [1]);
    foreach ($os_bd as $osn => $cnt):
      $pct = round($cnt / $omax * 100);
    ?>
    <div class="bar-row">
      <span class="bar-label"><?= h($osn) ?></span>
      <div class="bar-track"><div class="bar-fill bar-fill-orange" style="width:<?= $pct ?>%"></div></div>
      <span class="bar-val"><?= $cnt ?></span>
    </div>
    <?php endforeach; if (!$os_bd) echo '<p class="text-dim text-small">'.h(L('no_data')).'</p>'; ?>
  </div>
</div>

<p class="text-dim text-small mt-8">
  Poslední aktualizace: <?= h($telem['last_updated'] ?? '—') ?>
</p>

<?php if ($last30): ?>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
(function(){
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = '#a0a0b8';
  new Chart(document.getElementById('chart-daily'), {
    type: 'bar',
    data: {
      labels: <?= json_encode(array_keys($last30)) ?>,
      datasets: [{
        label: '<?= h(L('total_launches')) ?>',
        data: <?= json_encode(array_map(fn($d) => (int)($d['launches'] ?? 0), array_values($last30))) ?>,
        backgroundColor: '#0078D4',
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#1f1f2c' } },
        y: { grid: { color: '#1f1f2c' }, beginAtZero: true }
      }
    }
  });
})();
</script>
<?php endif; ?>
<?php
};

require __DIR__ . '/_layout.php';
