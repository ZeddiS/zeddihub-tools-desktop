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
