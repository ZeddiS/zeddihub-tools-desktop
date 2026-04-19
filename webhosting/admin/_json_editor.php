<?php
/**
 * Shared JSON editor partial.
 *
 * Caller must define before including:
 *   $PAGE_ID, $PAGE_TITLE, $JSON_FILE, $JSON_DESC, $JSON_HINT, $JSON_REF (string|null)
 */
require_once __DIR__ . '/_lib.php';
require_login();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $raw = trim($_POST['json_content'] ?? '');
    $decoded = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        flash('error', 'Neplatný JSON: ' . json_last_error_msg());
        redirect('index.php?page=' . urlencode($PAGE_ID));
    }
    if (json_write($JSON_FILE, $decoded)) {
        audit_log('json_save', ['file' => basename($JSON_FILE)]);
        flash('success', 'Uloženo!');
    } else {
        flash('error', 'Chyba při ukládání. Zkontrolujte práva zápisu.');
    }
    redirect('index.php?page=' . urlencode($PAGE_ID));
}

$raw = file_exists($JSON_FILE)
    ? json_encode(json_decode(file_get_contents($JSON_FILE), true),
                  JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
    : '{}';

$_desc = $JSON_DESC; $_hint = $JSON_HINT; $_ref = $JSON_REF ?? null;
$CONTENT = function() use ($raw, $_desc, $_hint, $_ref, $PAGE_ID) {
?>
<div class="card">
  <div class="card-title">JSON editor</div>
  <p class="text-dim text-small" style="margin-bottom:10px"><?= h($_desc) ?></p>
  <div class="alert alert-info">i Formát: <?= h($_hint) ?></div>
  <form method="post">
    <?= csrf_input() ?>
    <div class="json-editor-wrap">
      <textarea name="json_content" class="form-textarea" rows="22" id="json-input"><?= h($raw) ?></textarea>
      <div class="json-status" id="json-status"></div>
    </div>
    <div class="btn-row">
      <button type="submit" class="btn btn-primary"><?= h(L('save')) ?></button>
      <button type="button" class="btn btn-secondary" onclick="formatJson()">Formátovat</button>
      <button type="button" class="btn btn-secondary" onclick="validateJson()">Validovat</button>
    </div>
  </form>
</div>

<?php if ($_ref): ?>
<div class="card">
  <div class="card-title">Reference</div>
  <pre class="code-block"><?= h($_ref) ?></pre>
</div>
<?php endif; ?>

<script>
var ta = document.getElementById('json-input');
var st = document.getElementById('json-status');
function validateJson(){ try { JSON.parse(ta.value); st.textContent='OK'; st.className='json-status ok'; } catch(e){ st.textContent=e.message; st.className='json-status err'; } }
function formatJson(){ try { ta.value=JSON.stringify(JSON.parse(ta.value),null,2); st.textContent='Formátováno'; st.className='json-status ok'; } catch(e){ st.textContent=e.message; st.className='json-status err'; } }
ta.addEventListener('input', function(){ try { JSON.parse(ta.value); st.textContent='OK'; st.className='json-status ok'; } catch(e){ st.textContent=e.message; st.className='json-status err'; } });
</script>
<?php
};

require __DIR__ . '/_layout.php';
