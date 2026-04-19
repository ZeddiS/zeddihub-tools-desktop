<?php
/**
 * Login page — no layout wrapper.
 */
require_once __DIR__ . '/_lib.php';

if (($_POST['_action'] ?? '') === 'login') {
    csrf_check();
    $u = trim($_POST['username'] ?? '');
    $p = $_POST['password'] ?? '';
    if (do_login($u, $p)) {
        redirect('index.php?page=dashboard');
    } else {
        flash('error', admin_lang() === 'cs'
            ? 'Nesprávné přihlašovací údaje nebo nemáte admin oprávnění.'
            : 'Invalid credentials or insufficient privileges.');
        redirect('index.php?page=login');
    }
}

$flash = get_flash();
$csrf  = csrf_token();
$lang  = admin_lang();
?>
<!DOCTYPE html>
<html lang="<?= h($lang) ?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login &mdash; <?= h(APP_TITLE) ?></title>
<link rel="stylesheet" href="style.css">
</head>
<body class="zh-app">
<div class="login-wrap">
  <div class="login-box">
    <div class="login-logo">
      <div class="login-badge">ZH</div>
      <h1>ZeddiHub Admin</h1>
      <p><?= $lang === 'cs' ? 'Správa serverové konfigurace' : 'Server configuration management' ?></p>
    </div>
    <?php if ($flash): ?>
    <div class="alert alert-<?= h($flash['type']) ?>">
      <?= $flash['type'] === 'success' ? '&#10003;' : '&#10007;' ?> <?= h($flash['msg']) ?>
    </div>
    <?php endif; ?>
    <form method="post" action="index.php?page=login">
      <input type="hidden" name="_action" value="login">
      <input type="hidden" name="_csrf" value="<?= h($csrf) ?>">
      <div class="form-group">
        <label class="form-label"><?= $lang === 'cs' ? 'Uživatelské jméno' : 'Username' ?></label>
        <input type="text" name="username" class="form-input" required autofocus
               value="<?= h($_POST['username'] ?? '') ?>">
      </div>
      <div class="form-group">
        <label class="form-label"><?= $lang === 'cs' ? 'Heslo' : 'Password' ?></label>
        <input type="password" name="password" class="form-input" required>
      </div>
      <div class="btn-row" style="margin-top:20px">
        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">
          <?= $lang === 'cs' ? 'Přihlásit se' : 'Sign in' ?>
        </button>
      </div>
    </form>
    <p class="login-footer">
      <?= $lang === 'cs' ? 'Přihlásit se mohou pouze uživatelé s rolí' : 'Only users with role' ?>
      <strong>admin</strong>
      <br>
      <a class="lang-switch" href="index.php?page=login&amp;lang=<?= $lang === 'cs' ? 'en' : 'cs' ?>">
        <?= $lang === 'cs' ? 'EN' : 'CS' ?>
      </a>
    </p>
  </div>
</div>
</body>
</html>
