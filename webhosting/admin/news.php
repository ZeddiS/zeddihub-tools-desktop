<?php
/**
 * News editor — edits webhosting/data/news.json.
 * On first load, seeds the file with a sample entry.
 *
 * Format:
 *   [ { id, date, title, body, tag, pinned }, ... ]
 */
require_once __DIR__ . '/_lib.php';
require_login();

$PAGE_ID    = 'news';
$PAGE_TITLE = L('news');

// Seed if missing
if (!file_exists(FILE_NEWS)) {
    $seed = [
        [
            'id'     => 'v1.9.0',
            'date'   => '2026-04-19',
            'title'  => 'ZeddiHub Tools v1.9.0',
            'body'   => 'Novinky 1.9.0: Win11 Dark Gaming téma, přepracovaný admin dashboard, opravený updater, dynamická verze na webu.',
            'tag'    => 'release',
            'pinned' => true,
        ],
    ];
    json_write(FILE_NEWS, $seed);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $action = $_POST['_action'] ?? '';
    $news = json_read(FILE_NEWS, []);
    if (!is_array($news)) $news = [];

    if ($action === 'save_entry') {
        $id     = trim($_POST['id'] ?? '');
        $date   = trim($_POST['date'] ?? date('Y-m-d'));
        $title  = trim($_POST['title'] ?? '');
        $body   = trim($_POST['body'] ?? '');
        $tag    = trim($_POST['tag'] ?? 'update');
        $pinned = !empty($_POST['pinned']);
        $original = trim($_POST['original'] ?? '');

        if (!$title) { flash('error', 'Titulek je povinný.'); redirect('index.php?page=news'); }
        if (!$id) $id = strtolower(preg_replace('/[^a-z0-9]+/i', '-', $title));

        $entry = compact('id', 'date', 'title', 'body', 'tag', 'pinned');

        $found = false;
        foreach ($news as &$e) {
            if (($e['id'] ?? '') === $original && $original !== '') {
                $e = $entry; $found = true; break;
            }
        }
        unset($e);
        if (!$found) array_unshift($news, $entry);

        if (json_write(FILE_NEWS, $news)) {
            audit_log('news_save', ['id' => $id]);
            flash('success', 'Uloženo.');
        } else flash('error', 'Chyba při ukládání.');
    }

    if ($action === 'delete_entry') {
        $id = trim($_POST['id'] ?? '');
        $news = array_values(array_filter($news, fn($e) => ($e['id'] ?? '') !== $id));
        if (json_write(FILE_NEWS, $news)) {
            audit_log('news_delete', ['id' => $id]);
            flash('success', 'Smazáno.');
        } else flash('error', 'Chyba při ukládání.');
    }
    redirect('index.php?page=news');
}

$news = json_read(FILE_NEWS, []);
if (!is_array($news)) $news = [];

$CONTENT = function() use ($news) {
?>
<div class="card">
  <div class="card-title"><?= h(L('news')) ?> <span class="badge"><?= count($news) ?></span></div>
  <?php if (empty($news)): ?>
    <p class="text-dim"><?= h(L('news_empty')) ?></p>
  <?php else: ?>
  <div class="table-wrap">
    <table>
      <thead><tr><th>Datum</th><th>Titulek</th><th>Tag</th><th>Pinned</th><th>Akce</th></tr></thead>
      <tbody>
      <?php foreach ($news as $n): ?>
        <tr>
          <td><span class="text-dim text-small"><?= h($n['date'] ?? '') ?></span></td>
          <td><strong><?= h($n['title'] ?? '') ?></strong><br><span class="text-dim text-small"><?= h(mb_substr($n['body'] ?? '', 0, 110)) ?></span></td>
          <td><span class="badge-role badge-user"><?= h($n['tag'] ?? '') ?></span></td>
          <td><?= !empty($n['pinned']) ? '&#9733;' : '' ?></td>
          <td>
            <button class="btn btn-secondary btn-sm"
              onclick='openNews(<?= json_encode($n, JSON_UNESCAPED_UNICODE|JSON_HEX_APOS|JSON_HEX_QUOT) ?>)'><?= h(L('edit')) ?></button>
            <form method="post" style="display:inline" onsubmit="return confirm('Smazat?')">
              <input type="hidden" name="_action" value="delete_entry">
              <?= csrf_input() ?>
              <input type="hidden" name="id" value="<?= h($n['id'] ?? '') ?>">
              <button type="submit" class="btn btn-danger btn-sm"><?= h(L('delete')) ?></button>
            </form>
          </td>
        </tr>
      <?php endforeach; ?>
      </tbody>
    </table>
  </div>
  <?php endif; ?>
  <div class="btn-row">
    <button type="button" class="btn btn-primary" onclick="openNews(null)">+ <?= h(L('add')) ?></button>
  </div>
</div>

<div id="news-modal" class="modal-overlay">
  <div class="modal-card" style="max-width:560px">
    <h3 style="color:var(--primary);margin-bottom:14px">Novinka</h3>
    <form method="post">
      <input type="hidden" name="_action" value="save_entry">
      <?= csrf_input() ?>
      <input type="hidden" name="original" id="news-original">
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">ID (slug)</label>
          <input type="text" name="id" id="news-id" class="form-input" placeholder="v1.9.0">
        </div>
        <div class="form-group">
          <label class="form-label">Datum</label>
          <input type="date" name="date" id="news-date" class="form-input" value="<?= date('Y-m-d') ?>">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Titulek</label>
        <input type="text" name="title" id="news-title" class="form-input" required>
      </div>
      <div class="form-group">
        <label class="form-label">Text</label>
        <textarea name="body" id="news-body" class="form-textarea" rows="6"></textarea>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Tag</label>
          <select name="tag" id="news-tag" class="form-select">
            <option value="release">release</option>
            <option value="update">update</option>
            <option value="fix">fix</option>
            <option value="info">info</option>
          </select>
        </div>
        <div class="form-group" style="display:flex;align-items:flex-end">
          <label style="display:flex;align-items:center;gap:6px;color:var(--text-dim)">
            <input type="checkbox" name="pinned" id="news-pinned" value="1"> Pinned
          </label>
        </div>
      </div>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary"><?= h(L('save')) ?></button>
        <button type="button" class="btn btn-secondary" onclick="closeNews()"><?= h(L('cancel')) ?></button>
      </div>
    </form>
  </div>
</div>
<script>
function openNews(n) {
  n = n || {};
  document.getElementById('news-original').value = n.id || '';
  document.getElementById('news-id').value    = n.id || '';
  document.getElementById('news-date').value  = n.date || new Date().toISOString().slice(0,10);
  document.getElementById('news-title').value = n.title || '';
  document.getElementById('news-body').value  = n.body || '';
  document.getElementById('news-tag').value   = n.tag || 'update';
  document.getElementById('news-pinned').checked = !!n.pinned;
  document.getElementById('news-modal').classList.add('open');
}
function closeNews() { document.getElementById('news-modal').classList.remove('open'); }
</script>
<?php
};

require __DIR__ . '/_layout.php';
