# ============================================================
#  ZeddiHub Tools Desktop - Release v1.8.0 (PowerShell)
# ============================================================
#  Jak spustit:
#    1. Otevrete PowerShell v teto slozce (Shift + Pravy klik -> "Open PowerShell here")
#    2. Pokud se stezuje na policy, spustte jednou:
#         Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#    3. Spustte:  .\release_1_8_0.ps1
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "=== ZeddiHub Tools - Release v1.8.0 ===" -ForegroundColor Cyan
Write-Host ""

# --- 0. sanity: git repo ---
if (-not (Test-Path ".git")) {
    Write-Host "[!] Nejste v git repu. Skoncil jsem." -ForegroundColor Red
    exit 1
}

# --- 1. remove any stale index.lock ---
$lock = ".git\index.lock"
if (Test-Path $lock) {
    Write-Host "[1/6] Nasel jsem .git\index.lock - mazu..."
    try {
        Remove-Item $lock -Force -ErrorAction Stop
        Write-Host "      OK"
    } catch {
        Write-Host "      [!] Nelze smazat .git\index.lock - mozna bezi jiny git proces." -ForegroundColor Yellow
        Write-Host "      Zkuste zavrit VS Code, GitHub Desktop, TortoiseGit a spustit znovu."
        exit 1
    }
} else {
    Write-Host "[1/6] Zadny lock nenalezen - OK"
}

# --- 2. verify git binary ---
Write-Host "[2/6] Kontroluji git..."
$gitVer = & git --version 2>&1
Write-Host "      $gitVer"

# --- 3. safety: verify auth.json wont be committed with real passwords ---
Write-Host "[3/6] Stage vsech zmen KROME webhosting\data\auth.json..."
& git add -A | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[!] git add selhalo"; exit 1 }

# Unstage the sensitive file (user's real production creds must not leak)
& git reset HEAD -- webhosting/data/auth.json 2>&1 | Out-Null

# Print what's about to go in
Write-Host ""
Write-Host "Zmeny, ktere se commitnou:" -ForegroundColor Cyan
& git diff --cached --stat
Write-Host ""

$confirm = Read-Host "Pokracovat s commitem + tagem v1.8.0? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Prerusto. Resetuji stage."
    & git reset HEAD | Out-Null
    exit 0
}

# --- 4. commit ---
Write-Host "[4/6] Commit v1.8.0..."
$title = "release: v1.8.0 - Blur redesign + Game Opt + Advanced PC Tools + shortcuts + profile + file share + home cards + web guides + news carousel"
$body  = "Obsahuje tyto TODO: N-02, N-03, N-04, N-06, N-07, N-08, N-09, N-10, N-11, E-01, E-02"
& git commit -m $title -m $body
if ($LASTEXITCODE -ne 0) { Write-Host "[!] git commit selhalo"; exit 1 }

# --- 5. tag ---
Write-Host "[5/6] Tag v1.8.0..."
& git tag -a v1.8.0 -m "ZeddiHub Tools Desktop v1.8.0"
if ($LASTEXITCODE -ne 0) { Write-Host "[!] git tag selhalo"; exit 1 }

# --- 6. push ---
Write-Host "[6/6] Push master + tag v1.8.0..."
& git push origin master
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] push master selhal - zkuste 'git push origin master' rucne."
    exit 1
}
& git push origin v1.8.0
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] push tagu selhal - zkuste 'git push origin v1.8.0' rucne."
    exit 1
}

Write-Host ""
Write-Host "=== HOTOVO ===" -ForegroundColor Green
Write-Host "Tag v1.8.0 pushnut. GitHub Actions nyni zbuildi .exe a prilozi k release."
Write-Host "  Actions : https://github.com/ZeddiS/zeddihub-tools-desktop/actions"
Write-Host "  Releases: https://github.com/ZeddiS/zeddihub-tools-desktop/releases"
Write-Host ""
