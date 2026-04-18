@echo off
REM =======================================================================
REM  ZEDDIHUB TOOLS DESKTOP - Release Manager v1.7.0
REM  Centralni skript pro konfiguraci, build, test a release.
REM  Spustit z korene projektu: zeddihub.bat
REM =======================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul 2>&1

set "REPO_ROOT=%~dp0"
set "ENV_FILE=%REPO_ROOT%.env"
set "VERSION=1.7.0"
set "TAG=v%VERSION%"

:menu
cls
call :load_env
call :detect_status

echo.
echo  +======================================================================+
echo  ^|   ZEDDIHUB TOOLS DESKTOP - RELEASE MANAGER                           ^|
echo  ^|   Verze: %VERSION%                                                        ^|
echo  +======================================================================+
echo.
echo    STATUS:
echo      .env:          !STATUS_ENV!
echo      GITHUB_TOKEN:  !STATUS_TOKEN!
echo      Python:        !STATUS_PYTHON!
echo      PyInstaller:   !STATUS_PYI!
echo      Git branch:    !STATUS_BRANCH!
echo      Build .exe:    !STATUS_EXE!
echo      Remote tag:    !STATUS_TAG!
echo.
echo  +--[ NASTAVENI ]-------------------------------------------------------+
echo  ^|   [1] Konfigurace .env  (token, owner, repo, git identita)          ^|
echo  ^|   [2] Test GITHUB_TOKEN (ma spravne permissions?)                   ^|
echo  ^|   [3] Zkontrolovat/nainstalovat Python dependencies                 ^|
echo  +--[ BUILD ^& RELEASE ]-------------------------------------------------+
echo  ^|   [4] Build .exe lokalne  (pyinstaller)                             ^|
echo  ^|   [5] Auto Release        (commit+push, GitHub Actions buildne)     ^|
echo  ^|   [6] Manual Release      (vyzaduje [4], upload .exe pres gh CLI)   ^|
echo  +--[ SPRAVA ]----------------------------------------------------------+
echo  ^|   [7] Git status          (zobrazi lokalni zmeny)                   ^|
echo  ^|   [8] Smazat tag %TAG%   (lokalne + na remote - pokud blokuje push)^|
echo  ^|   [9] Otevrit GitHub      (repo / releases / actions v prohlizeci)  ^|
echo  +----------------------------------------------------------------------+
echo  ^|   [0] Konec                                                         ^|
echo  +----------------------------------------------------------------------+
echo.
set /p CHOICE=   Volba:

if "%CHOICE%"=="1" goto configure_env
if "%CHOICE%"=="2" goto test_token
if "%CHOICE%"=="3" goto install_deps
if "%CHOICE%"=="4" goto build_exe
if "%CHOICE%"=="5" goto auto_release
if "%CHOICE%"=="6" goto manual_release
if "%CHOICE%"=="7" goto git_status
if "%CHOICE%"=="8" goto delete_tag
if "%CHOICE%"=="9" goto open_github
if "%CHOICE%"=="0" goto end
goto menu

REM =======================================================================
REM  [HELPERS]
REM =======================================================================
:load_env
set "GITHUB_TOKEN="
set "GITHUB_OWNER=ZeddiS"
set "GITHUB_REPO=zeddihub-tools-desktop"
set "GITHUB_DEFAULT_BRANCH=master"
set "GIT_AUTHOR_NAME=ZeddiS"
set "GIT_AUTHOR_EMAIL="
if not exist "%ENV_FILE%" exit /b 0
for /f "usebackq tokens=1,2 delims==" %%A in ("%ENV_FILE%") do (
    set "LINE=%%A"
    if not "!LINE:~0,1!"=="#" if not "!LINE!"=="" (
        set "%%A=%%B"
    )
)
exit /b 0

:detect_status
if exist "%ENV_FILE%" (set "STATUS_ENV=[OK]") else (set "STATUS_ENV=[CHYBI]")
if defined GITHUB_TOKEN (
    set "T1=!GITHUB_TOKEN:~0,15!"
    set "STATUS_TOKEN=[OK] !T1!..."
) else (
    set "STATUS_TOKEN=[CHYBI]"
)
python --version >nul 2>&1 && (set "STATUS_PYTHON=[OK]") || (set "STATUS_PYTHON=[CHYBI]")
python -m PyInstaller --version >nul 2>&1 && (set "STATUS_PYI=[OK]") || (set "STATUS_PYI=[CHYBI]")
set "STATUS_BRANCH=(nezjisteno)"
for /f "usebackq" %%B in (`git branch --show-current 2^>nul`) do set "STATUS_BRANCH=%%B"
if exist "dist\ZeddiHubTools.exe" (
    set "STATUS_EXE=[OK] dist\ZeddiHubTools.exe"
) else if exist "dist\ZeddiHub.Tools.exe" (
    set "STATUS_EXE=[OLD] dist\ZeddiHub.Tools.exe"
) else (
    set "STATUS_EXE=[NENI]"
)
set "STATUS_TAG=(nezjisteno)"
git ls-remote --tags https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git %TAG% >nul 2>&1 && (
    for /f "usebackq tokens=1,2" %%T in (`git ls-remote --tags https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git %TAG% 2^>nul`) do (
        if "%%U"=="" set "STATUS_TAG=[MISSING] %TAG% neni pushnut"
    )
)
git ls-remote --tags https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git refs/tags/%TAG% 2>nul | findstr /C:"%TAG%" >nul && (
    set "STATUS_TAG=[PUSHED] %TAG% je na GitHubu"
) || (
    set "STATUS_TAG=[NOT PUSHED] %TAG% jeste neni na GitHubu"
)
exit /b 0

:pause_and_return
echo.
pause
goto menu

REM =======================================================================
REM  [1] KONFIGURACE .env
REM =======================================================================
:configure_env
cls
echo.
echo  ====================================================================
echo   [1] KONFIGURACE .env
echo  ====================================================================
echo.
echo  Tento formular vytvori/prepise soubor .env v korene projektu.
echo  Soubor je chranen .gitignore a NIKDY se nepostne do repozitare.
echo.
if exist "%ENV_FILE%" (
    echo  UPOZORNENI: .env jiz existuje. Pokracovani ho prepise.
    echo.
    choice /c AN /n /m "  Pokracovat? [A]no / [N]e: "
    if errorlevel 2 goto menu
    echo.
)
echo  --- GITHUB_TOKEN (Fine-grained PAT) ---
echo  Vytvor na: https://github.com/settings/personal-access-tokens/new
echo  Repository access: Only selected -^> %GITHUB_OWNER%/%GITHUB_REPO%
echo  Permissions: Contents R/W, Issues R/W, Pull requests R/W, Metadata R-only
echo.
set "NEW_TOKEN="
set /p NEW_TOKEN=  Vloz GITHUB_TOKEN (github_pat_...):
if "!NEW_TOKEN!"=="" (
    echo  CHYBA: Token nemuze byt prazdny.
    goto pause_and_return
)

echo.
echo  --- GITHUB_OWNER ---
set "NEW_OWNER="
set /p NEW_OWNER=  Owner [ZeddiS]:
if "!NEW_OWNER!"=="" set "NEW_OWNER=ZeddiS"

echo.
echo  --- GITHUB_REPO ---
set "NEW_REPO="
set /p NEW_REPO=  Repo [zeddihub-tools-desktop]:
if "!NEW_REPO!"=="" set "NEW_REPO=zeddihub-tools-desktop"

echo.
echo  --- GITHUB_DEFAULT_BRANCH ---
set "NEW_BRANCH="
set /p NEW_BRANCH=  Branch [master]:
if "!NEW_BRANCH!"=="" set "NEW_BRANCH=master"

echo.
echo  --- Git identita ---
set "NEW_GNAME="
set /p NEW_GNAME=  Git author name [ZeddiS]:
if "!NEW_GNAME!"=="" set "NEW_GNAME=ZeddiS"

set "NEW_GEMAIL="
set /p NEW_GEMAIL=  Git author email:
if "!NEW_GEMAIL!"=="" (
    echo  CHYBA: Email nemuze byt prazdny.
    goto pause_and_return
)

REM Zapsat .env
(
    echo # ZeddiHub Tools Desktop - runtime secrets ^(NIKDY NECOMMITUJ^)
    echo # Tento soubor je v .gitignore.
    echo.
    echo GITHUB_TOKEN=!NEW_TOKEN!
    echo.
    echo GITHUB_OWNER=!NEW_OWNER!
    echo GITHUB_REPO=!NEW_REPO!
    echo GITHUB_DEFAULT_BRANCH=!NEW_BRANCH!
    echo.
    echo GIT_AUTHOR_NAME=!NEW_GNAME!
    echo GIT_AUTHOR_EMAIL=!NEW_GEMAIL!
) > "%ENV_FILE%"

echo.
echo  [OK] .env byl ulozen do: %ENV_FILE%
echo  Nastavuji git config...
git config user.name "!NEW_GNAME!" >nul
git config user.email "!NEW_GEMAIL!" >nul
echo  [OK] git config user.name / user.email nastaveno.
goto pause_and_return

REM =======================================================================
REM  [2] TEST TOKENU
REM =======================================================================
:test_token
cls
echo.
echo  ====================================================================
echo   [2] TEST GITHUB_TOKEN
echo  ====================================================================
echo.
if not defined GITHUB_TOKEN (
    echo  CHYBA: GITHUB_TOKEN neni v .env. Spustte volbu [1].
    goto pause_and_return
)
echo  Testuji token (prvnich 15 znaku: !GITHUB_TOKEN:~0,15!...^)
echo.
echo  --- Test 1: GET /user (authentication) ---
curl -sS -H "Accept: application/vnd.github+json" -H "Authorization: Bearer %GITHUB_TOKEN%" https://api.github.com/user | findstr /C:"\"login\":"
echo.
echo  --- Test 2: GET /repos/%GITHUB_OWNER%/%GITHUB_REPO% (repo access) ---
curl -sS -o nul -w "  HTTP: %%{http_code}\n" -H "Accept: application/vnd.github+json" -H "Authorization: Bearer %GITHUB_TOKEN%" https://api.github.com/repos/%GITHUB_OWNER%/%GITHUB_REPO%
echo.
echo  --- Test 3: GET /repos/.../releases (contents permission) ---
curl -sS -o nul -w "  HTTP: %%{http_code}\n" -H "Accept: application/vnd.github+json" -H "Authorization: Bearer %GITHUB_TOKEN%" https://api.github.com/repos/%GITHUB_OWNER%/%GITHUB_REPO%/releases
echo.
echo  Vsechny testy mely vratit "login": "%GITHUB_OWNER%" nebo HTTP 200.
echo  401/403/404 = token nema spravne permissions nebo je expired.
goto pause_and_return

REM =======================================================================
REM  [3] PYTHON DEPENDENCIES
REM =======================================================================
:install_deps
cls
echo.
echo  ====================================================================
echo   [3] PYTHON DEPENDENCIES
echo  ====================================================================
echo.
python --version 2>nul || (
    echo  CHYBA: Python neni nainstalovan nebo neni v PATH.
    echo  Stahnete: https://www.python.org/downloads/
    goto pause_and_return
)
echo.
echo  Instaluji requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || (
    echo  CHYBA pri instalaci requirements.txt
    goto pause_and_return
)
echo.
echo  Instaluji PyInstaller...
python -m pip install --upgrade pyinstaller || (
    echo  CHYBA pri instalaci pyinstaller
    goto pause_and_return
)
echo.
echo  --- Kontrola ---
python -m PyInstaller --version
python -c "import customtkinter, PIL, cryptography, pystray, psutil, pynput, pyautogui; print('Vsechny moduly nacteny OK.')"
goto pause_and_return

REM =======================================================================
REM  [4] BUILD .EXE
REM =======================================================================
:build_exe
cls
echo.
echo  ====================================================================
echo   [4] BUILD Windows .exe
echo  ====================================================================
echo.
if not exist "ZeddiHubTools.spec" (
    echo  CHYBA: ZeddiHubTools.spec nenalezen.
    goto pause_and_return
)
python -m PyInstaller --version >nul 2>&1 || (
    echo  UPOZORNENI: PyInstaller neni nainstalovan. Spoustim [3] nejdriv...
    call :install_deps_inline
)
echo.
echo  Spoustim pyinstaller...
python -m PyInstaller --noconfirm ZeddiHubTools.spec || (
    echo  CHYBA: Build selhal.
    goto pause_and_return
)
echo.
if exist "dist\ZeddiHubTools.exe" (
    echo  [OK] Build hotov: dist\ZeddiHubTools.exe
    for %%I in (dist\ZeddiHubTools.exe) do echo  Velikost: %%~zI bajtu
) else (
    echo  CHYBA: dist\ZeddiHubTools.exe nevytvoren.
)
goto pause_and_return

:install_deps_inline
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
python -m pip install --upgrade pyinstaller
exit /b 0

REM =======================================================================
REM  [5] AUTO RELEASE (push -> GitHub Actions buildne)
REM =======================================================================
:auto_release
cls
echo.
echo  ====================================================================
echo   [5] AUTO RELEASE - commit + push + Actions
echo  ====================================================================
echo.
if not defined GITHUB_TOKEN (
    echo  CHYBA: GITHUB_TOKEN neni v .env. Spustte [1].
    goto pause_and_return
)

REM Odstranit stale lock
if exist ".git\index.lock" del /f /q ".git\index.lock" 2>nul

REM Git identita
git config user.name "%GIT_AUTHOR_NAME%" >nul 2>&1
git config user.email "%GIT_AUTHOR_EMAIL%" >nul 2>&1

REM Obnovit omylem smazane tracked soubory
if not exist "assets\icon.ico"      git restore assets/icon.ico       >nul 2>&1
if not exist "assets\logo_icon.png" git restore assets/logo_icon.png  >nul 2>&1

REM Stage vsech zmen KROME webhosting/data/auth.json (plaintext hesla!)
echo  [1/5] Staging...
git add -A
git reset HEAD -- webhosting/data/auth.json >nul 2>&1

echo.
echo  [2/5] Vytvareni commitu...
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "release: %TAG% - N-01/05/12-15 + F-07/F-08 + fixes" || goto auto_err
) else (
    echo   (zadne nove staged zmeny - pokracuji)
)

echo.
echo  [3/5] Vytvareni tagu %TAG%...
git tag -a %TAG% -m "Release %TAG%" 2>nul && (
    echo   (tag %TAG% vytvoren)
) || (
    echo   (tag %TAG% uz existuje lokalne)
)

echo.
echo  [4/5] Push pres HTTPS s tokenem...
set "REMOTE_URL=https://%GITHUB_TOKEN%@github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git"
git push "%REMOTE_URL%" %GITHUB_DEFAULT_BRANCH% || goto auto_err
git push "%REMOTE_URL%" %TAG% || goto auto_err

echo.
echo  [5/5] +========================================+
echo        ^|  PUSH USPESNY - GITHUB ACTIONS BEZI!  ^|
echo        +========================================+
echo.
echo  Sledujte build:  https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions
echo  Release bude za ~3-5 minut na:
echo    https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/releases/tag/%TAG%
goto pause_and_return

:auto_err
echo.
echo  CHYBA: Push selhal. Mozne priciny:
echo   - Push Protection detekoval tajemstvi v commitu (token v .gitignore?)
echo   - Token nema permission 'Contents: Read and write'
echo   - Tag %TAG% jiz existuje na remote - pouzijte [8] pro smazani
echo   - Konflikt s remote - spustte 'git pull' rucne
goto pause_and_return

REM =======================================================================
REM  [6] MANUAL RELEASE (gh CLI upload lokalni .exe)
REM =======================================================================
:manual_release
cls
echo.
echo  ====================================================================
echo   [6] MANUAL RELEASE - upload .exe pres gh CLI
echo  ====================================================================
echo.
if not exist "dist\ZeddiHubTools.exe" (
    echo  CHYBA: dist\ZeddiHubTools.exe neni. Spustte nejdriv [4].
    goto pause_and_return
)
where gh >nul 2>&1 || (
    echo  CHYBA: GitHub CLI 'gh' neni nainstalovan.
    echo  Stahnete: https://cli.github.com/
    echo.
    echo  NEBO: pouzijte [5] Auto Release - ten nepotrebuje gh.
    goto pause_and_return
)
echo  Overeni gh autentizace...
gh auth status >nul 2>&1 || (
    echo  CHYBA: gh neni prihlaseny. Spustte 'gh auth login' rucne.
    goto pause_and_return
)
echo.
echo  Vytvarim release %TAG% s .exe...
gh release create %TAG% "dist\ZeddiHubTools.exe" ^
    --repo %GITHUB_OWNER%/%GITHUB_REPO% ^
    --title "ZeddiHub Tools Desktop %TAG%" ^
    --notes-file "RELEASE_NOTES_%TAG%.md" ^
    --latest || (
    echo  CHYBA pri vytvareni release (mozna uz existuje).
    goto pause_and_return
)
echo.
echo  [OK] Release vytvoren:
echo    https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/releases/tag/%TAG%
goto pause_and_return

REM =======================================================================
REM  [7] GIT STATUS
REM =======================================================================
:git_status
cls
echo.
echo  ====================================================================
echo   [7] GIT STATUS
echo  ====================================================================
echo.
echo  --- Branch ---
git branch --show-current
echo.
echo  --- Last commit ---
git log -1 --oneline
echo.
echo  --- Changes ---
git status --short
echo.
echo  --- Local tags ---
git tag -l
echo.
echo  --- Remote tags ---
git ls-remote --tags origin 2>nul | findstr /V "{}" | findstr /C:"refs/tags"
goto pause_and_return

REM =======================================================================
REM  [8] SMAZAT TAG
REM =======================================================================
:delete_tag
cls
echo.
echo  ====================================================================
echo   [8] SMAZAT TAG %TAG%
echo  ====================================================================
echo.
echo  Tento krok smaze tag %TAG% LOKALNE i na GitHubu.
echo  Pouzivat POUZE pokud push selhal a potrebujete zacit znovu.
echo.
choice /c AN /n /m "  Pokracovat? [A]no / [N]e: "
if errorlevel 2 goto menu
echo.
git tag -d %TAG% 2>nul && echo   (lokalni tag %TAG% smazan) || echo   (lokalni tag neexistoval)
if defined GITHUB_TOKEN (
    echo.
    echo  Mazu remote tag...
    set "REMOTE_URL=https://%GITHUB_TOKEN%@github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git"
    git push "!REMOTE_URL!" --delete %TAG% 2>nul && (
        echo   [OK] remote tag smazan
    ) || (
        echo   (remote tag neexistoval, nebo chybi permissions)
    )
) else (
    echo  .env nema token - remote tag smazte rucne na GitHubu.
)
goto pause_and_return

REM =======================================================================
REM  [9] OTEVRIT GITHUB
REM =======================================================================
:open_github
cls
echo.
echo  ====================================================================
echo   [9] OTEVRIT GITHUB
echo  ====================================================================
echo.
echo    [a] Repo home      https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%
echo    [b] Releases       https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/releases
echo    [c] Actions        https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions
echo    [d] Issues         https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/issues
echo    [e] Settings PAT   https://github.com/settings/personal-access-tokens
echo    [0] zpet
echo.
set /p GHCHOICE=  Volba:
if /i "%GHCHOICE%"=="a" start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%"
if /i "%GHCHOICE%"=="b" start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/releases"
if /i "%GHCHOICE%"=="c" start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions"
if /i "%GHCHOICE%"=="d" start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/issues"
if /i "%GHCHOICE%"=="e" start "" "https://github.com/settings/personal-access-tokens"
goto menu

REM =======================================================================
:end
echo.
echo  Nashledanou!
endlocal
exit /b 0
