// ============================================================
//  ZeddiHub Tools — Google Apps Script
//  Propojení Google Tabulky ↔ GitHub Issues
//
//  Repozitář: https://github.com/ZeddiS/zeddihub-tools-desktop
//  Verze: 1.0.0
// ============================================================
//
//  PŘED POUŽITÍM:
//  1. Otevřete Apps Script editor (Rozšíření → Apps Script)
//  2. Nastavte Script Properties (viz návod níže)
//  3. Spusťte funkci  setupTriggers()  jednou ručně
//  4. Spusťte funkci  initializeSheets()  pro vytvoření záhlaví
// ============================================================


// ============================================================
// 1. KONSTANTY — GitHub repozitář
// ============================================================
const GITHUB_OWNER = 'ZeddiS';
const GITHUB_REPO  = 'zeddihub-tools-desktop';
const GITHUB_API   = 'https://api.github.com';


// ============================================================
// 2. MAPOVÁNÍ SLOUPCŮ PRO KAŽDÝ LIST
// ============================================================

// List: Backlog   (A=Název, B=Popis, C=Labels, D=Issue URL, E=Stav)
const BACKLOG_COLS = {
  nazev:    1,   // A — Název úkolu
  popis:    2,   // B — Popis
  labels:   3,   // C — Labels oddělené čárkou (volitelné)
  issueUrl: 4,   // D — GitHub Issue URL (zapíše skript)
  stav:     5    // E — Stav (zapíše skript)
};

// List: Bugs   (A=Název, B=Popis, C=Závažnost, D=Issue URL, E=Stav)
const BUGS_COLS = {
  nazev:    1,   // A — Název bugu
  popis:    2,   // B — Popis / reprodukce
  labels:   3,   // C — Závažnost/Labels (volitelné)
  issueUrl: 4,   // D — GitHub Issue URL (zapíše skript)
  stav:     5    // E — Stav (zapíše skript)
};

// List: Dotazy   (A=Issue URL, B=Dotaz, C=Odpověď, D=Stav)
const DOTAZY_COLS = {
  issueRef: 1,   // A — URL GitHub Issue nebo název úkolu
  dotaz:    2,   // B — Dotaz od Claude (vložíte sem)
  odpoved:  3,   // C — Vaše odpověď
  stav:     4    // D — Stav (mění skript automaticky)
};

// Hodnoty stavu pro list Dotazy
const STAV_DOTAZ_CEKA      = '⏳ Čeká na odpověď';
const STAV_DOTAZ_PRIPRAVENO = '✅ Připraveno k práci';

// Hodnoty stavu pro Backlog / Bugs
const STAV_ISSUE_OTEVRENO = '🔵 Otevřeno';
const STAV_ISSUE_CHYBA    = '❌ Chyba';


// ============================================================
// 3. POMOCNÉ FUNKCE — načtení nastavení
// ============================================================

/**
 * Načte GitHub token ze Script Properties.
 * Vyhodí výjimku, pokud token není nastaven.
 */
function getGitHubToken_() {
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    throw new Error(
      'GitHub token není nastaven!\n' +
      'Přejděte do Apps Script → Nastavení projektu → Vlastnosti skriptu\n' +
      'a přidejte klíč  GITHUB_TOKEN  s vaším Personal Access Tokenem.'
    );
  }
  return token;
}

/**
 * Vrátí instanci aktivní tabulky nebo otevře tabulku podle SPREADSHEET_ID.
 */
function getSpreadsheet_() {
  const id = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
  if (id) {
    return SpreadsheetApp.openById(id);
  }
  // Fallback: skript je přimo v tabulce (container-bound)
  return SpreadsheetApp.getActiveSpreadsheet();
}


// ============================================================
// 4. SETUP — Instalace triggerů (spusťte jednou ručně!)
// ============================================================

/**
 * Nainstaluje onEdit installable trigger.
 * MUSÍ být spuštěno jednou ručně z Apps Script editoru.
 * Bez tohoto kroku skript nemůže volat GitHub API.
 */
function setupTriggers() {
  // Smazat všechny existující triggery tohoto projektu
  ScriptApp.getProjectTriggers().forEach(trigger => {
    ScriptApp.deleteTrigger(trigger);
  });

  const ss = getSpreadsheet_();

  // Installable onEdit trigger — má práva volat UrlFetchApp
  ScriptApp.newTrigger('onSheetEdit')
    .forSpreadsheet(ss)
    .onEdit()
    .create();

  Logger.log('✅ Trigger "onSheetEdit" byl úspěšně nainstalován!');
  Logger.log('   Nyní spusťte funkci initializeSheets() pro přípravu záhlaví listů.');
}


// ============================================================
// 5. INICIALIZACE LISTŮ — Záhlaví a formátování
// ============================================================

/**
 * Vytvoří listy Backlog, Bugs a Dotazy (pokud neexistují)
 * a nastaví záhlaví se správnými názvy sloupců.
 */
function initializeSheets() {
  const ss = getSpreadsheet_();

  createOrFormatSheet_(ss, 'Backlog', [
    'Název úkolu', 'Popis', 'Labels (čárkou)', 'GitHub Issue URL', 'Stav'
  ], '#1565C0');

  createOrFormatSheet_(ss, 'Bugs', [
    'Název bugu', 'Popis', 'Závažnost / Labels', 'GitHub Issue URL', 'Stav'
  ], '#B71C1C');

  createOrFormatSheet_(ss, 'Dotazy', [
    'URL Issue nebo název úkolu', 'Dotaz od Claude', 'Vaše odpověď', 'Stav'
  ], '#1B5E20');

  Logger.log('✅ Listy Backlog, Bugs a Dotazy jsou připraveny!');
}

function createOrFormatSheet_(ss, name, headers, headerBgColor) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    Logger.log(`  → List "${name}" byl vytvořen.`);
  }

  // Záhlaví
  const headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setValues([headers]);
  headerRange.setBackground(headerBgColor);
  headerRange.setFontColor('#FFFFFF');
  headerRange.setFontWeight('bold');
  headerRange.setFontSize(11);
  sheet.setFrozenRows(1);

  // Šířky sloupců
  const widths = [260, 360, 220, 320, 160];
  headers.forEach((_, i) => {
    if (widths[i]) sheet.setColumnWidth(i + 1, widths[i]);
  });

  // Zarovnání hlavičky na střed
  headerRange.setHorizontalAlignment('center');

  return sheet;
}


// ============================================================
// 6. HLAVNÍ TRIGGER — onEdit dispatcher
// ============================================================

/**
 * Voláno automaticky při každé editaci tabulky.
 * Rozhoduje, který list byl změněn, a volá příslušný handler.
 *
 * @param {GoogleAppsScript.Events.SheetsOnEdit} e - event objekt
 */
function onSheetEdit(e) {
  if (!e || !e.range) return;

  const sheet     = e.range.getSheet();
  const sheetName = sheet.getName();
  const row       = e.range.getRow();
  const col       = e.range.getColumn();

  // Ignorovat záhlaví (řádek 1)
  if (row <= 1) return;

  if (sheetName === 'Backlog') {
    handleTaskSheet_(sheet, 'Backlog', BACKLOG_COLS, 'backlog', row, col);
    return;
  }

  if (sheetName === 'Bugs') {
    handleTaskSheet_(sheet, 'Bugs', BUGS_COLS, 'bug', row, col);
    return;
  }

  if (sheetName === 'Dotazy') {
    handleDotazySheet_(sheet, row, col);
    return;
  }
}


// ============================================================
// 7. HANDLER — Backlog & Bugs → vytvoření GitHub Issue
// ============================================================

/**
 * Pokud uživatel zapíše název do sloupce A (Backlog nebo Bugs),
 * automaticky vytvoří GitHub Issue a zapíše URL a stav zpět.
 */
function handleTaskSheet_(sheet, sheetName, cols, defaultLabel, row, editedCol) {
  // Reagujeme pouze na editaci sloupce "Název" (A)
  if (editedCol !== cols.nazev) return;

  const nazevCell = sheet.getRange(row, cols.nazev);
  const nazev     = nazevCell.getValue();

  // Přeskočit prázdné buňky
  if (!nazev || nazev.toString().trim() === '') return;

  // Přeskočit řádky, kde issue URL již existuje (zabraňuje duplicitám)
  const existingUrl = sheet.getRange(row, cols.issueUrl).getValue();
  if (existingUrl && existingUrl.toString().startsWith('https://')) return;

  // Načíst volitelná pole
  const popis     = sheet.getRange(row, cols.popis).getValue()  || '';
  const labelsRaw = sheet.getRange(row, cols.labels).getValue() || '';

  // Sestavit pole labels
  let labels = [defaultLabel];
  if (labelsRaw.toString().trim()) {
    const extra = labelsRaw.toString()
      .split(',')
      .map(l => l.trim())
      .filter(l => l.length > 0);
    labels = [...new Set([...labels, ...extra])];
  }

  // Sestavit tělo issue ve formátu Markdown
  const body = buildIssueBody_(sheetName, popis, row);

  // Označit řádek jako zpracovávaný (spinnerová barva)
  sheet.getRange(row, cols.issueUrl).setValue('⏳ Vytváření...');

  try {
    const issue = createGitHubIssue_(nazev.toString().trim(), body, labels);

    // Zapsat výsledky do tabulky
    sheet.getRange(row, cols.issueUrl).setValue(issue.html_url);
    sheet.getRange(row, cols.issueUrl).setFontColor('#1565C0');

    if (cols.stav) {
      sheet.getRange(row, cols.stav).setValue(STAV_ISSUE_OTEVRENO);
    }

    // Zvýraznit řádek světle zelenou
    sheet.getRange(row, 1, 1, 5).setBackground('#E8F5E9');

    Logger.log(`✅ [${sheetName}] Issue #${issue.number} vytvořeno: ${issue.html_url}`);

  } catch (err) {
    Logger.log(`❌ [${sheetName}] Chyba: ${err.message}`);

    sheet.getRange(row, cols.issueUrl).setValue('CHYBA: ' + err.message);
    sheet.getRange(row, cols.issueUrl).setBackground('#FFCDD2');
    sheet.getRange(row, cols.issueUrl).setFontColor('#B71C1C');

    if (cols.stav) {
      sheet.getRange(row, cols.stav).setValue(STAV_ISSUE_CHYBA);
    }
  }
}

/**
 * Sestaví tělo GitHub Issue v Markdownu.
 */
function buildIssueBody_(sheetName, popis, row) {
  const lines = [];

  if (popis && popis.toString().trim()) {
    lines.push('## 📋 Popis');
    lines.push('');
    lines.push(popis.toString().trim());
    lines.push('');
  }

  lines.push('---');
  lines.push('');
  lines.push(`> 🤖 *Issue vytvořeno automaticky ze Google Tabulky*`);
  lines.push(`> List: **${sheetName}** · Řádek: **${row}**`);

  return lines.join('\n');
}


// ============================================================
// 8. HANDLER — Dotazy → sledování stavu
// ============================================================

/**
 * Logika pro list Dotazy:
 *
 *   a) Uživatel vloží dotaz do sloupce B:
 *      → Stav = "⏳ Čeká na odpověď" (žlutá)
 *      → Dotaz se přidá jako komentář k GitHub Issue (pokud je URL v A)
 *
 *   b) Uživatel vyplní odpověď do sloupce C:
 *      → Stav = "✅ Připraveno k práci" (zelená)
 *      → Odpověď se přidá jako komentář k GitHub Issue
 */
function handleDotazySheet_(sheet, row, editedCol) {
  const dotaz   = sheet.getRange(row, DOTAZY_COLS.dotaz).getValue();
  const odpoved = sheet.getRange(row, DOTAZY_COLS.odpoved).getValue();
  const stavCell = sheet.getRange(row, DOTAZY_COLS.stav);
  const stavAktualni = stavCell.getValue();
  const issueRef = sheet.getRange(row, DOTAZY_COLS.issueRef).getValue();

  // --- PŘÍPAD A: byl vložen dotaz (sloupec B) ---
  if (editedCol === DOTAZY_COLS.dotaz) {
    if (!dotaz || dotaz.toString().trim() === '') return;

    // Nastavit stav čekání
    stavCell.setValue(STAV_DOTAZ_CEKA);
    stavCell.setBackground('#FFF9C4');  // světle žlutá
    stavCell.setFontColor('#F57F17');

    // Přidat dotaz jako komentář k issue (pokud máme URL)
    if (issueRef && isGitHubUrl_(issueRef.toString())) {
      try {
        const komentarText =
          `## ❓ Dotaz k úkolu\n\n${dotaz.toString().trim()}\n\n` +
          `---\n*Dotaz zadán přes Google Tabulku — list **Dotazy**, řádek ${row}*`;

        addCommentToIssue_(issueRef.toString(), komentarText);
        Logger.log(`✅ [Dotazy] Dotaz přidán jako komentář k issue.`);
      } catch (err) {
        Logger.log(`⚠️  [Dotazy] Komentář se nepodařilo přidat: ${err.message}`);
      }
    }
    return;
  }

  // --- PŘÍPAD B: byla vložena odpověď (sloupec C) ---
  if (editedCol === DOTAZY_COLS.odpoved) {
    if (!odpoved || odpoved.toString().trim() === '') return;

    // Měnit stav pouze pokud byl předtím v režimu čekání
    if (stavAktualni !== STAV_DOTAZ_CEKA) return;

    // Nastavit stav připravenosti
    stavCell.setValue(STAV_DOTAZ_PRIPRAVENO);
    stavCell.setBackground('#C8E6C9');  // světle zelená
    stavCell.setFontColor('#1B5E20');

    // Přidat odpověď jako komentář k issue
    if (issueRef && isGitHubUrl_(issueRef.toString())) {
      try {
        const komentarText =
          `## 💬 Odpověď uživatele\n\n${odpoved.toString().trim()}\n\n` +
          `---\n✅ *Stav úkolu byl změněn na **Připraveno k práci***`;

        addCommentToIssue_(issueRef.toString(), komentarText);
        Logger.log(`✅ [Dotazy] Odpověď přidána jako komentář k issue.`);
      } catch (err) {
        Logger.log(`⚠️  [Dotazy] Odpověď se nepodařilo přidat: ${err.message}`);
      }
    }

    Logger.log(`✅ [Dotazy] Řádek ${row} — stav změněn na "Připraveno k práci".`);
    return;
  }
}

/**
 * Zkontroluje, zda je řetězec platná GitHub URL.
 */
function isGitHubUrl_(str) {
  return str.startsWith('https://github.com/') && str.includes('/issues/');
}


// ============================================================
// 9. GITHUB API — Vytvoření Issue
// ============================================================

/**
 * Vytvoří nové Issue na GitHubu.
 *
 * @param {string} title   - Název issue
 * @param {string} body    - Tělo issue (Markdown)
 * @param {string[]} labels - Pole labelů (musí existovat v repozitáři)
 * @returns {object} Odpověď GitHub API (obsahuje html_url, number, ...)
 */
function createGitHubIssue_(title, body, labels) {
  const url = `${GITHUB_API}/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues`;

  const payload = {
    title:  title,
    body:   body,
    labels: labels
  };

  const options = {
    method:           'POST',
    headers:          buildHeaders_(),
    payload:          JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  return handleApiResponse_(response, 201, 'Vytvoření issue');
}


// ============================================================
// 10. GITHUB API — Přidání komentáře k Issue
// ============================================================

/**
 * Přidá komentář k existujícímu GitHub Issue.
 *
 * @param {string} issueUrl - Plná URL issue (https://github.com/.../issues/N)
 * @param {string} body     - Text komentáře (Markdown)
 */
function addCommentToIssue_(issueUrl, body) {
  const issueNumber = extractIssueNumber_(issueUrl);
  const url = `${GITHUB_API}/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issueNumber}/comments`;

  const options = {
    method:           'POST',
    headers:          buildHeaders_(),
    payload:          JSON.stringify({ body }),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  return handleApiResponse_(response, 201, 'Přidání komentáře');
}


// ============================================================
// 11. GITHUB API — Aktualizace stavu Issue (open / closed)
// ============================================================

/**
 * Změní stav issue na GitHubu na 'open' nebo 'closed'.
 *
 * @param {string} issueUrl - Plná URL issue
 * @param {'open'|'closed'} state - Nový stav
 */
function updateIssueState_(issueUrl, state) {
  const issueNumber = extractIssueNumber_(issueUrl);
  const url = `${GITHUB_API}/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues/${issueNumber}`;

  const options = {
    method:           'PATCH',
    headers:          buildHeaders_(),
    payload:          JSON.stringify({ state }),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  return handleApiResponse_(response, 200, 'Aktualizace stavu issue');
}


// ============================================================
// 12. GITHUB API — Sdílené pomocné funkce
// ============================================================

function buildHeaders_() {
  return {
    'Authorization':        `Bearer ${getGitHubToken_()}`,
    'Accept':               'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'Content-Type':         'application/json'
  };
}

function handleApiResponse_(response, expectedCode, operationName) {
  const code = response.getResponseCode();
  const body = response.getContentText();
  let data;

  try {
    data = JSON.parse(body);
  } catch (_) {
    data = { message: body };
  }

  if (code !== expectedCode) {
    const msg = data.message || `HTTP ${code}`;
    throw new Error(`${operationName} selhalo: ${msg} (HTTP ${code})`);
  }

  return data;
}

function extractIssueNumber_(issueUrl) {
  const match = issueUrl.match(/\/issues\/(\d+)/);
  if (!match) {
    throw new Error(`Neplatná GitHub Issue URL: "${issueUrl}"`);
  }
  return match[1];
}


// ============================================================
// 13. TESTOVACÍ FUNKCE — Spouštějte z Apps Script editoru
// ============================================================

/**
 * Test: Ověří připojení k GitHub API a práva tokenu.
 * Spusťte jako první po nastavení GITHUB_TOKEN.
 */
function testConnection() {
  Logger.log('=== Test připojení k GitHub API ===');
  try {
    const url = `${GITHUB_API}/repos/${GITHUB_OWNER}/${GITHUB_REPO}`;
    const response = UrlFetchApp.fetch(url, {
      headers: buildHeaders_(),
      muteHttpExceptions: true
    });
    const code = response.getResponseCode();

    if (code === 200) {
      const data = JSON.parse(response.getContentText());
      Logger.log(`✅ Připojení OK!`);
      Logger.log(`   Repozitář: ${data.full_name}`);
      Logger.log(`   Popis: ${data.description}`);
      Logger.log(`   Počet open issues: ${data.open_issues_count}`);
    } else if (code === 401) {
      Logger.log('❌ Chyba autentizace — zkontrolujte GITHUB_TOKEN.');
    } else if (code === 404) {
      Logger.log('❌ Repozitář nenalezen — zkontrolujte GITHUB_OWNER a GITHUB_REPO.');
    } else {
      Logger.log(`❌ Neočekávaná odpověď: HTTP ${code}`);
      Logger.log(response.getContentText());
    }
  } catch (err) {
    Logger.log(`❌ Chyba: ${err.message}`);
  }
}

/**
 * Test: Vytvoří jedno testovací issue v Backlogu.
 */
function testCreateIssue() {
  Logger.log('=== Test vytvoření GitHub Issue ===');
  try {
    const issue = createGitHubIssue_(
      '🧪 [TEST] Testovací issue ze skriptu',
      '## 📋 Popis\n\nToto je automaticky vytvořené testovací issue.\n\n> Bezpečné smazat po ověření funkcionality.',
      ['backlog']
    );
    Logger.log(`✅ Issue vytvořeno!`);
    Logger.log(`   Číslo:  #${issue.number}`);
    Logger.log(`   URL:    ${issue.html_url}`);
    Logger.log(`   Název:  ${issue.title}`);
  } catch (err) {
    Logger.log(`❌ Chyba: ${err.message}`);
  }
}

/**
 * Test: Zobrazí aktuální Script Properties (bez hodnot tokenu).
 */
function testShowProperties() {
  Logger.log('=== Aktuální Script Properties ===');
  const props = PropertiesService.getScriptProperties().getProperties();
  Object.keys(props).forEach(key => {
    const value = key === 'GITHUB_TOKEN'
      ? '***' + props[key].slice(-4)   // Skrýt token, zobrazit jen poslední 4 znaky
      : props[key];
    Logger.log(`  ${key} = ${value}`);
  });
}


// ============================================================
// 14. SEED — Přidání nových úkolů 2026-04-19 (spusťte jednou!)
// ============================================================

/**
 * Přidá nové úkoly z analýzy 2026-04-19 do listů Backlog, Bugs a Dotazy.
 * SPUSŤTE JEDNOU z Apps Script editoru → poté smažte nebo zakomentujte.
 */
function seedNewTasks_April19() {
  const ss = getSpreadsheet_();
  const backlog = ss.getSheetByName('Backlog');
  const bugs    = ss.getSheetByName('Bugs');
  const dotazy  = ss.getSheetByName('Dotazy');

  if (!backlog || !bugs || !dotazy) {
    Logger.log('❌ Listy nenalezeny — nejprve spusťte initializeSheets().');
    return;
  }

  // ── BACKLOG: EDIT úkoly ─────────────────────────────────────
  const backlogRows = [
    [
      'E-04 — Admin Dashboard: vizuální vylepšení + nové funkce',
      'Vylepšit webhosting/admin/index.php a style.css.\n'
      + 'Vizuálně přehlednější rozhraní: karty, statistiky, moderní dark theme.\n'
      + 'Přidat vhodné nové funkce — viz dotaz v listu Dotazy.',
      'EDIT, střední komplexita, web, admin, dashboard',
      '',
      'TODO'
    ],
    [
      'E-05 — UI identita aplikace: políčka splývají',
      'Všechna pole (CTkEntry, CTkButton, CTkFrame) vypadají genericky.\n'
      + 'Úprava themes.py: přidat border_color, entry_border, button_gradient klíče.\n'
      + 'Helper funkce _btn(), _entry_row() dostanou custom styling.\n'
      + 'Přidat corner_radius, border_width customizaci.\n'
      + 'Soubory: gui/themes.py, gui/panels/*.py\n'
      + 'Vztah k E-02 (kompletní redesign) — viz dotaz.',
      'EDIT, střední komplexita, ui, themes, desktop',
      '',
      'TODO'
    ]
  ];

  // ── BUGS: FIX úkoly ─────────────────────────────────────────
  const bugsRows = [
    [
      'F-09 — Synchronizace verzí (App, GitHub, Web, Admin)',
      'TD-001 z CLAUDE.md: gui/updater.py=1.6.3, gui/telemetry.py=1.6.0, version.json (root)=1.3.0.\n'
      + 'Nově přidat: webhosting/data/version.json a webhosting/index.php.\n'
      + 'Řešení: centralizovat do gui/version.py (APP_VERSION = "x.x.x") — jeden zdroj pravdy.\n'
      + 'Soubory: gui/updater.py, gui/telemetry.py, version.json, webhosting/data/version.json, nový gui/version.py',
      'FIX, nízká závažnost, versions, web, desktop',
      '',
      'TODO'
    ],
    [
      'F-10 — Web: verze vždy zobrazuje nejnovější z GitHubu',
      'Webhosting index.php zobrazuje statickou verzi (1.6.3).\n'
      + 'Řešení: PHP funkce fetchLatestVersion() s cache 30 min volá GitHub Releases API.\n'
      + 'Soubory: webhosting/index.php',
      'FIX, nízká závažnost, web, versions, github',
      '',
      'TODO'
    ],
    [
      'F-11 — Web "Co aplikace umí": max 9–12 položek + nové tagy',
      'Stávající sekce má příliš mnoho položek a nevhodné tagy.\n'
      + 'Zredukovat na 9–12 položek.\n'
      + 'Odstranit tagy "NEW v1.7" — nahradit: CS2, CS:GO, Rust, Gaming, PC Tool, Server.\n'
      + 'Soubory: webhosting/index.php',
      'FIX, nízká závažnost, web, content',
      '',
      'TODO'
    ],
    [
      'F-12 — Ikona aplikace: použít assets/web_favicon.ico',
      'Aplikace aktuálně generuje icon.ico z logo_transparent.png při prvním spuštění.\n'
      + 'Řešení: přeskočit generování, použít přímo assets/web_favicon.ico.\n'
      + 'Soubory: root app.py (funkce _generate_icon), gui/main_window.py (wm_iconbitmap volání)',
      'FIX, nízká závažnost, ui, icon, desktop',
      '',
      'TODO'
    ]
  ];

  // ── DOTAZY ───────────────────────────────────────────────────
  const dotazyRows = [
    [
      'F-09',
      'Jaká je správná "master" verze aplikace, na kterou vše synchronizujeme? Je to 1.6.3 (updater.py), nebo plánuješ vydání nové verze?',
      '',
      STAV_DOTAZ_CEKA
    ],
    [
      'E-04',
      'Admin dashboard — jaké konkrétní nové funkce chceš přidat? (Příklady: správa uživatelů přes UI, bulk operace, exporty CSV, interaktivní grafy telemetrie, správa Guides, správa File Share, live server status...)',
      '',
      STAV_DOTAZ_CEKA
    ],
    [
      'E-05',
      'Preferuješ konkrétní vizuální styl pro UI políček? (Windows 11 mica/acrylic sklo, dark minimalist s ostrými hranami, neon gaming glow, nebo jiný). A má se E-05 implementovat PŘED nebo SOUBĚŽNĚ s E-02 (kompletní redesign)?',
      '',
      STAV_DOTAZ_CEKA
    ]
  ];

  // ── Zápis do tabulky ─────────────────────────────────────────
  backlogRows.forEach(row => backlog.appendRow(row));
  bugsRows.forEach(row => bugs.appendRow(row));
  dotazyRows.forEach(row => {
    const lastRow = dotazy.getLastRow() + 1;
    dotazy.appendRow(row);
    // Barevně označit stav čekání
    dotazy.getRange(lastRow, DOTAZY_COLS.stav).setBackground('#FFF9C4').setFontColor('#F57F17');
  });

  Logger.log('✅ seedNewTasks_April19: úkoly přidány do tabulky!');
  Logger.log('   Backlog: ' + backlogRows.length + ' nové řádky (E-04, E-05)');
  Logger.log('   Bugs:    ' + bugsRows.length + ' nové řádky (F-09, F-10, F-11, F-12)');
  Logger.log('   Dotazy:  ' + dotazyRows.length + ' nové řádky');
  Logger.log('   ➜ Po ověření funkci smažte nebo zakomentujte.');
}


// ============================================================
// 15. UPDATE — Aktualizace popisů + nový bug F-13 (spusťte jednou!)
// ============================================================

/**
 * Aktualizuje popisy existujících úkolů na základě odpovědí z Dotazy
 * a přidává nový bug F-13 (nefunkční updater).
 * SPUSŤTE JEDNOU z Apps Script editoru → poté smažte nebo zakomentujte.
 */
function updateTaskDescriptions_April19() {
  const ss      = getSpreadsheet_();
  const backlog = ss.getSheetByName('Backlog');
  const bugs    = ss.getSheetByName('Bugs');

  if (!backlog || !bugs) {
    Logger.log('❌ Listy nenalezeny — nejprve spusťte initializeSheets().');
    return;
  }

  // ── Helper: najde řádek podle prefixu v sloupci A ──────────
  function findRow(sheet, prefix) {
    const data = sheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] && data[i][0].toString().startsWith(prefix)) return i + 1;
    }
    return -1;
  }

  // ── Helper: aktualizuje Popis (sloupec B) ──────────────────
  function update(sheet, prefix, desc) {
    const row = findRow(sheet, prefix);
    if (row > 0) {
      sheet.getRange(row, 2).setValue(desc);
      Logger.log('  ✅ ' + prefix + ' — aktualizován (řádek ' + row + ')');
    } else {
      Logger.log('  ⚠️  ' + prefix + ' — řádek nenalezen, přeskočen');
    }
  }

  // ── BACKLOG — aktualizace popisů ───────────────────────────

  update(backlog, 'N-01',
    'Panel PC Tools — tři nové nástroje:\n\n'
    + '1. AUTOCLICKER\n'
    + 'Funguje globálně (i při minimalizaci do tray) přes background thread.\n'
    + 'Nastavitelné: interval klikání (ms), počet opakování nebo nekonečný režim, tlačítko myši (levé/pravé/střední).\n'
    + 'Start/stop klávesová zkratka konfigurovatelná uživatelem. Bezpečnostní limit maximálního CPS.\n'
    + 'Závislosti: pyautogui nebo win32api + threading\n\n'
    + '2. STICKY NOTES\n'
    + 'Plovoucí okna (CTkToplevel, always-on-top) nad plochou.\n'
    + 'Persistentní přes restart — data uložena v sticky_notes.json v datovém adresáři.\n'
    + 'Volitelný čas automatického smazání: bez omezení / 1h / 6h / 24h / vlastní.\n'
    + 'Operace: přidat, smazat, minimalizovat, změnit barvu, přetáhnout pozici.\n\n'
    + '3. YOUTUBE DOWNLOADER\n'
    + 'Výchozí stav: neaktivní. Tlačítko "Aktivovat" → dialog s upozorněním (~50 MB).\n'
    + 'Po potvrzení: stáhne yt-dlp externě do datového adresáře (ne do .exe bundlu).\n'
    + 'UI: pole URL, výběr kvality (best/1080p/720p/audio MP3), výběr výstupní složky, progress bar, log.\n\n'
    + 'Soubory: gui/panels/pc_tools.py, requirements.txt (pyautogui)'
  );

  update(backlog, 'E-01',
    'Úprava navigační struktury v main_window.py.\n'
    + 'Hlavní panel sekce "Nástroje" zobrazí pouze PC Tools (pc_tools.py).\n'
    + 'Odebrat z tohoto panelu: serverové a hráčské nástroje — ty zůstávají ve svých sekcích (CS2, CS:GO, Rust).\n'
    + 'Změna v NAV_SECTIONS a NAV_GAME_MAP.\n\n'
    + 'Soubory: gui/main_window.py'
  );

  update(backlog, 'E-02',
    'Kompletní odstranění výchozích Windows dekorací — nahrazení vlastním rámečkem:\n\n'
    + 'TITLEBAR: Logo + název aplikace. Vlastní tlačítka minimalizovat/maximalizovat/zavřít.\n'
    + 'Drag & drop pohyb přetažením titlebar. Double-click = maximize/restore.\n\n'
    + 'TVAR A OKRAJ: Zaoblené rohy (~12px) přes overrideredirect(True) + průhledné root window.\n'
    + 'Shadow efekt. Resize handles (přetahování okraje). Při maximalizaci: hranaté rohy.\n\n'
    + 'KOMPATIBILITA: tray.py komunikuje přes app.after(0, ...) — ověřit po změně.\n'
    + 'Minimize to tray musí fungovat přes withdraw(), ne destroy().\n\n'
    + 'Soubory: gui/main_window.py, app.py, gui/tray.py'
  );

  update(backlog, 'N-05',
    'Nový panel pro monitoring vlastního GitHub repozitáře.\n\n'
    + 'FUNKCE:\n'
    + '— Přehled repozitáře: hvězdičky, forks, watchers, open issues, open PR, poslední commit\n'
    + '— Open Issues: seznam, filtrování podle labels, klik = otevře v prohlížeči\n'
    + '— Pull Requests: seznam, autor\n'
    + '— Releases & Downloads: release notes preview, počet stažení per asset\n'
    + '— README ↔ Releases: parsuje verzi z README.md, porovná s nejnovějším release tagem, upozorní při neshodě\n'
    + '— Synchronizace Novinek: detekuje release bez novinky, tlačítko "Synchronizovat"\n'
    + '— Auto-refresh: 5/15 min nebo manuálně. Badge s počtem open issues v sidebar.\n\n'
    + 'Soubory: nový gui/panels/github_checker.py, gui/main_window.py, sdílená logika z gui/updater.py'
  );

  update(backlog, 'N-07',
    'Sdílení souborů integrované v desktop aplikaci — backend na zeddihub.eu.\n\n'
    + 'DESKTOP PANEL:\n'
    + 'Drag & drop nebo výběr souboru. Upload progress bar (HTTP POST na zeddihub.eu/tools/upload.php).\n'
    + 'Po uploadu: unikátní share URL s tlačítkem "Kopírovat". Historie uploadů v JSON.\n'
    + 'Sekce ke stažení: seznam souborů ze serveru, download progress bar, výběr složky.\n\n'
    + 'WEBHOSTING BACKEND (nové soubory):\n'
    + 'upload.php — přijímá multipart POST, ukládá soubory, vrací share URL. Max 50 MB.\n'
    + 'Auth: upload pouze pro přihlášené (token v POST headeru).\n'
    + 'download.php — slouží soubory. shared_files.json — index souborů.\n'
    + 'Admin panel: správa souborů (přehled, smazání, expirace).\n\n'
    + 'Soubory: nový gui/panels/fileshare.py, webhosting/upload.php, webhosting/download.php, webhosting/data/shared_files.json'
  );

  update(backlog, 'N-08',
    'Nový panel — přístupný pouze přihlášeným uživatelům (_auth_verified).\n'
    + 'Admin práva: POUZE při spuštění konkrétní funkce (subprocess runas) — ne při startu aplikace.\n\n'
    + 'TWEAKY — Herní výkon:\n'
    + '1. Game Mode: HKCU\\Software\\Microsoft\\GameBar → AllowAutoGameMode=1, AutoGameModeEnabled=1\n'
    + '2. HAGS (GPU Scheduling): HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers → HwSchMode=2 (vyžaduje restart)\n'
    + '3. Zakázat Fullscreen Optimizations: HKCU\\System\\GameConfigStore → GameDVR_FSEBehaviorMode=2\n'
    + '4. CPU Priority: HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl → Win32PrioritySeparation=38\n'
    + '5. Multimedia Scheduler: ...SystemProfile → NetworkThrottlingIndex=0xffffffff, SystemResponsiveness=0\n'
    + '6. Gaming Scheduler Profile: ...Tasks\\Games → Priority=6, Scheduling Category=High\n\n'
    + 'TWEAKY — Myš:\n'
    + '7. Zakázat Mouse Acceleration: HKCU\\Control Panel\\Mouse → MouseSpeed=0, MouseThreshold1=0, MouseThreshold2=0\n\n'
    + 'TWEAKY — Síť:\n'
    + "8. Zakázat Nagle's Algorithm: Tcpip\\Parameters\\Interfaces\\{GUID} → TcpAckFrequency=1, TCPNoDelay=1\n\n"
    + 'TWEAKY — Systém:\n'
    + '9. Zakázat Windows Telemetry: HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection → AllowTelemetry=0\n'
    + '10. Vizuální efekty (výkon): HKCU\\...\\VisualEffects → VisualFXSetting=2\n'
    + '11. Zakázat Xbox Game Bar: HKCU\\...\\GameDVR → AppCaptureEnabled=0\n\n'
    + 'TWEAKY — Aktivace Windows:\n'
    + '12. Odebrat watermark: slmgr.vbs /rearm nebo SkipRearm=1\n'
    + '    ⚠️ PRÁVNÍ UPOZORNĚNÍ: zobrazit uživateli — bez platné licence porušuje Microsoft EULA\n\n'
    + 'UI: každý tweak = karta (název, popis, aktuální stav z registru, Aplikovat/Vrátit). Log s timestampem.\n\n'
    + 'Soubory: nový gui/panels/advanced_pc.py, gui/main_window.py (NAV_SECTIONS), gui/auth.py'
  );

  update(backlog, 'E-04',
    'Kompletní přepracování webhosting/admin/index.php a style.css.\n\n'
    + 'VIZUÁLNÍ REDESIGN: dark theme (#0d1117 pozadí, #161b22 karty), sidebar navigace místo tabů,\n'
    + 'KPI karty, Chart.js grafy, status indikátory, responsive grid, box-shadow + border-radius.\n\n'
    + 'DASHBOARD — widgety:\n'
    + '— KPI karty: unikátní uživatelé, stažení za 30 dní, aktivní sessions (24h), open GitHub Issues\n'
    + '— GitHub: stars/forks/watchers, downloads per release, graf stažení v čase (Chart.js)\n'
    + '— Telemetrie: top 5 panelů, graf aktivit 7/30 dní, OS distribuce (pie), distribuce verzí\n'
    + '— Live Server Status: ping na herní servery ze servers.json\n\n'
    + 'NOVÉ STRÁNKY:\n'
    + '— Správa uživatelů: přidat/smazat/deaktivovat přes UI, poslední aktivita\n'
    + '— Správa Guides: CRUD editor (Markdown, kategorie, tagy, preview)\n'
    + '— Správa File Share: přehled souborů, počet stažení, smazání, expirace\n'
    + '— Správa Novinek: CRUD, tlačítko "Načíst z GitHub Releases"\n'
    + '— Audit Log: kdo, co, kdy\n'
    + '— Export: telemetrie CSV, backup konfiguračních JSON\n'
    + '— Maintenance Mode: toggle → hláška uživatelům při spuštění aplikace\n\n'
    + 'Soubory: webhosting/admin/index.php, style.css, nové: users.php, guides.php, fileshare.php, news.php'
  );

  update(backlog, 'E-05',
    'Redesign vizuální identity — Windows 11 Dark Gaming styl.\n\n'
    + 'BAREVNÁ PALETA (nový default theme v themes.py):\n'
    + 'Background #0a0a0f | Sidebar #0f0f17 | Header #0d0d16 | Content #111119 | Card #1a1a26\n'
    + 'Akcent #0078D4 (W11 blue) nebo #6B46C1 (gaming purple) | Border #2a2a3a\n'
    + 'Text #e8e8f0 | Text dim #8080a0 | Success #22c55e | Error #ef4444 | Warning #f59e0b\n\n'
    + 'STYLOVÁNÍ PRVKŮ:\n'
    + 'CTkEntry: border_width=1, border_color=#2a2a3a, corner_radius=8, focus = akcent → řeší splývání\n'
    + 'CTkButton: corner_radius=8, hover glow efekt\n'
    + 'CTkFrame (karty): corner_radius=10, border_width=1, border_color=#1e1e2e\n'
    + 'CTkTabview: aktivní tab = akcentová spodní linka\n\n'
    + 'SIDEBAR: aktivní button = levý barevný pruh + zvýraznění. Nadpisy: uppercase, dim.\n'
    + 'HEADER: gradient top border. Game badge: pill design s akcentovou barvou hry.\n'
    + 'ANIMACE: hover transition, fade-in při přepínání panelů přes after().\n\n'
    + 'PREREQUISITE — TD-002: helper funkce duplikovány v cs2.py/csgo.py/rust.py.\n'
    + 'Doporučeno refactor do gui/widgets.py PŘED nebo SOUBĚŽNĚ s E-02.\n\n'
    + 'Soubory: gui/themes.py, gui/panels/cs2.py, csgo.py, rust.py, pc_tools.py,\n'
    + 'game_tools.py, settings.py, home.py, keybind.py, gui/main_window.py'
  );

  // ── BUGS — aktualizace popisů ──────────────────────────────

  update(bugs, 'F-07',
    'Dva problémy k vyřešení:\n\n'
    + '1. NEFUNKČNÍ WINDOWS NOTIFIKACE\n'
    + 'tray.py má show_notification() ale není volána z WM_DELETE_WINDOW handleru.\n'
    + 'Opravit: volat tray.show_notification() při prvním skrytí do tray.\n'
    + 'Zobrazit pouze jednou — příznak tray_hint_shown=true uložit do settings.json.\n\n'
    + '2. NOVÉ NASTAVENÍ "Chování při zavření"\n'
    + 'SettingsPanel: nová volba "Chování při zavření okna"\n'
    + '  — Možnost A: Minimalizovat do tray (výchozí)\n'
    + '  — Možnost B: Ukončit aplikaci\n'
    + 'Uložit do settings.json → close_behavior.\n'
    + 'main_window.py: WM_DELETE_WINDOW čte nastavení → withdraw() nebo destroy().\n'
    + 'Přidat překlad do locale/cs.json a locale/en.json.\n\n'
    + 'Soubory: gui/tray.py, gui/main_window.py, gui/panels/settings.py, locale/cs.json, locale/en.json'
  );

  update(bugs, 'F-09',
    'GitHub Release tag = jediný autoritativní zdroj verze. Všechny komponenty čtou verzi dynamicky.\n\n'
    + 'DESKTOP:\n'
    + 'Vytvořit gui/version.py s APP_VERSION jako jediným zdrojem pravdy.\n'
    + 'Synchronizovat gui/telemetry.py (_APP_VERSION) a gui/updater.py (CURRENT_VERSION) → 1.6.3.\n'
    + 'Při novém buildu: aktualizovat pouze gui/version.py.\n\n'
    + 'WEBHOSTING (index.php):\n'
    + 'Nahradit statickou verzi dynamickým PHP voláním GitHub Releases API.\n'
    + 'Cache 30 min. Fallback: version.json pokud API nedostupné.\n\n'
    + 'ADMIN PANEL: ověřit čtení verze z .gh_cache.json — sjednotit cache soubor.\n\n'
    + 'VERSION.JSON: gui/version.json + webhosting/data/version.json = záloha, aktualizovat při buildu.\n\n'
    + 'Soubory: gui/updater.py, gui/telemetry.py, nový gui/version.py,\n'
    + 'version.json (root), webhosting/index.php, webhosting/data/version.json'
  );

  // ── BUGS — nový řádek F-13 ─────────────────────────────────
  bugs.appendRow([
    'F-13 — Updater: nefunkční upozornění a aktualizace',
    'BUG 1 — Chybějící upozornění na novou verzi:\n'
    + 'Při spuštění starší verze se nezobrazí žádná notifikace o dostupnosti novější verze.\n'
    + 'gui/updater.py má check_for_update(callback) — callback pravděpodobně není připojen\n'
    + 'k UI notifikaci v main_window.py nebo settings.py.\n'
    + 'Nutno ověřit kde se check_for_update volá a zda callback správně předává data do UI.\n\n'
    + 'BUG 2 — Prázdné okno při aktualizaci:\n'
    + 'Při spuštění aktualizace se zobrazí prázdné okno místo progress dialogu.\n'
    + 'Pravděpodobná příčina: CTkToplevel dialog je vytvořen, ale jeho obsah\n'
    + '(progress bar, tlačítka, text) není vykreslen — threading issue nebo\n'
    + 'chyba při sestavování widgetů v download_update() nebo apply_update().\n\n'
    + 'KROKY K DEBUGOVÁNÍ:\n'
    + '1. Zkontrolovat gui/updater.py — jak je volán check_for_update() callback\n'
    + '2. Ověřit gui/main_window.py a gui/panels/settings.py — zpracování výsledku kontroly verze\n'
    + '3. Zkontrolovat dialog download_update() — zda jsou widgety přidány před mainloop\n'
    + '4. Ověřit thread safety — UI aktualizace musí jít přes after()\n\n'
    + 'Soubory: gui/updater.py, gui/main_window.py, gui/panels/settings.py',
    'FIX, střední závažnost, updater, desktop',
    '',
    'TODO'
  ]);
  Logger.log('  ✅ Přidán nový bug: F-13');

  Logger.log('');
  Logger.log('✅ updateTaskDescriptions_April19: dokončeno!');
  Logger.log('   ➜ Ověřte aktualizované řádky v tabulce.');
}
