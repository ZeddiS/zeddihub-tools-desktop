<?php
/**
 * ZeddiHub Admin - Shared layout
 * Each page includes this AFTER handling its own POST action.
 * Usage in page file:
 *
 *   require_once __DIR__ . '/_lib.php';
 *   require_login();
 *   // ...POST handling, set $PAGE_TITLE, $PAGE_ID...
 *   $CONTENT = function() { /* echo page content */ };
 *   require __DIR__ . '/_layout.php';
 */

require_once __DIR__ . '/_lib.php';

if (!isset($PAGE_ID))    $PAGE_ID = 'dashboard';
if (!isset($PAGE_TITLE)) $PAGE_TITLE = ucfirst($PAGE_ID);

$flash    = get_flash();
$me       = $_SESSION['admin_user'] ?? '?';
$cur_lang = admin_lang();
$nav_sections = sidebar_nav();

// Sidebar collapsed state (persisted in cookie)
$collapsed = (($_COOKIE['zh_sidebar'] ?? '') === 'collapsed');
?>
<!DOCTYPE html>
<html lang="<?= h($cur_lang) ?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title><?= h($PAGE_TITLE) ?> &mdash; <?= h(APP_TITLE) ?></title>
<link rel="stylesheet" href="style.css">
</head>
<body class="zh-app <?= $collapsed ? 'sidebar-collapsed' : '' ?>">
<div class="layout">

  <!-- Sidebar -->
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-logo">
      <div class="sidebar-logo-full">
        <h2>ZeddiHub</h2>
        <p>admin &middot; v<?= h(APP_VERSION) ?></p>
      </div>
      <div class="sidebar-logo-mini">ZH</div>
    </div>

    <div class="sidebar-nav">
      <?php foreach ($nav_sections as $sec_id => $sec): ?>
      <div class="nav-section-label"><?= h($sec['label']) ?></div>
      <?php foreach ($sec['items'] as $p => $info):
        $active = ($PAGE_ID === $p) ? 'active' : '';
      ?>
      <a href="index.php?page=<?= h($p) ?>" class="nav-item <?= $active ?>"
         title="<?= h($info['label']) ?>">
        <span class="nav-icon"><?= nav_icon($info['icon']) ?></span>
        <span class="nav-label"><?= h($info['label']) ?></span>
      </a>
      <?php endforeach; endforeach; ?>
    </div>

    <div class="sidebar-footer">
      <button type="button" class="sidebar-toggle" id="sidebar-toggle"
              title="Collapse / expand">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round"
             stroke-linejoin="round"><path d="M15 18 9 12l6-6"/></svg>
        <span class="nav-label">Collapse</span>
      </button>
    </div>
  </nav>

  <!-- Main -->
  <div class="main">
    <div class="topbar">
      <div class="topbar-left">
        <span class="topbar-title"><?= h($PAGE_TITLE) ?></span>
      </div>
      <div class="topbar-right">
        <?php $other_lang = $cur_lang === 'cs' ? 'en' : 'cs'; ?>
        <a class="lang-switch"
           href="index.php?page=<?= h($PAGE_ID) ?>&amp;lang=<?= h($other_lang) ?>">
          <?= $cur_lang === 'cs' ? 'EN' : 'CS' ?>
        </a>
        <div class="user-menu" id="user-menu">
          <button type="button" class="user-btn" id="user-btn">
            <span class="user-avatar"><?= h(strtoupper(substr($me, 0, 1))) ?></span>
            <span class="user-name"><?= h($me) ?></span>
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round"
                 stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
          </button>
          <div class="user-dropdown" id="user-dropdown">
            <div class="user-dropdown-header">
              <div class="user-name-big"><?= h($me) ?></div>
              <div class="user-role"><?= h(L('logged_as')) ?></div>
            </div>
            <a href="index.php?page=maintenance" class="user-dropdown-item">
              <?= nav_icon('wrench') ?> <?= h(L('maintenance')) ?>
            </a>
            <a href="index.php?page=logout" class="user-dropdown-item danger">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none"
                   stroke="currentColor" stroke-width="2" stroke-linecap="round"
                   stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/></svg>
              <?= h(L('logout')) ?>
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="content">
      <?php if ($flash): ?>
      <div class="alert alert-<?= h($flash['type']) ?>">
        <?= $flash['type'] === 'success' ? '&#10003;' : ($flash['type'] === 'error' ? '&#10007;' : 'i') ?>
        <?= h($flash['msg']) ?>
      </div>
      <?php endif; ?>

      <?php
      if (isset($CONTENT) && is_callable($CONTENT)) {
          $CONTENT();
      }
      ?>
    </div>
  </div>
</div>

<script>
(function(){
  var body = document.body;
  var toggle = document.getElementById('sidebar-toggle');
  if (toggle) {
    toggle.addEventListener('click', function(){
      body.classList.toggle('sidebar-collapsed');
      var v = body.classList.contains('sidebar-collapsed') ? 'collapsed' : 'expanded';
      document.cookie = 'zh_sidebar=' + v + ';path=/;max-age=31536000;SameSite=Strict';
    });
  }

  // User dropdown
  var ub = document.getElementById('user-btn');
  var um = document.getElementById('user-menu');
  if (ub && um) {
    ub.addEventListener('click', function(e){
      e.stopPropagation();
      um.classList.toggle('open');
    });
    document.addEventListener('click', function(){
      um.classList.remove('open');
    });
  }
})();
</script>
</body>
</html>
