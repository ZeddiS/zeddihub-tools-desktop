@echo off
REM =======================================================================
REM  ZEDDIHUB TOOLS DESKTOP - Release Manager v2.0.0
REM  Windows 11 compatible, ANSI-colored, FAST (cached status).
REM  Features: ASCII banner, ANSI colors, pre-flight checks, release
REM  wizard, push preview, auto icon regeneration before build.
REM =======================================================================
setlocal EnableDelayedExpansion EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul 2>&1
title ZeddiHub Tools Desktop - Release Manager v2.0.0

REM --- ANSI escape bootstrap (works on Win10 1909+ / Win11) ---
for /f "tokens=*" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

REM --- Color palette (use with !C_...! inside DelayedExpansion) ---
set "C_R=%ESC%[0m"
set "C_B=%ESC%[1m"
set "C_DIM=%ESC%[2m"
set "C_RED=%ESC%[91m"
set "C_GRN=%ESC%[92m"
set "C_YEL=%ESC%[93m"
set "C_BLU=%ESC%[94m"
set "C_MAG=%ESC%[95m"
set "C_CYN=%ESC%[96m"
set "C_WHT=%ESC%[97m"
set "C_GRY=%ESC%[90m"

REM --- Config ---
set "REPO_ROOT=%~dp0"
set "ENV_FILE=%REPO_ROOT%.env"
set "VERSION=2.0.0"
set "TAG=v%VERSION%"

REM --- CLI args ---
if /i "%~1"=="--debug"  set "ZH_DEBUG=1"
if /i "%~1"=="--wizard" set "DIRECT_ACTION=wizard"
if /i "%~1"=="/w"       set "DIRECT_ACTION=wizard"
if /i "%~1"=="/?"       goto show_help
if /i "%~1"=="-h"       goto show_help
if /i "%~1"=="--help"   goto show_help

REM --- Menu definition (12 items, grouped into sections) ---
set "MI_COUNT=12"
set "MI_1=Konfigurace .env"
set "MI_2=Test GITHUB_TOKEN"
set "MI_3=Dependencies (Python + PyInstaller)"
set "MI_4=Build .exe lokalne (+ icon regen)"
set "MI_5=Auto Release (commit+push+Actions)"
set "MI_6=Manual Release (gh CLI upload)"
set "MI_7=Git status"
set "MI_8=Smazat tag %TAG%"
set "MI_9=Otevrit GitHub v prohlizeci"
set "MI_10=Obnovit status (rescan)"
set "MI_11=Rychla push (quick commit)"
set "MI_12=Cleanup: PAT secret v historii (filter-repo)"

set "MS_1=Release"
set "MS_2=Release"
set "MS_3=Build"
set "MS_4=Build"
set "MS_5=Release"
set "MS_6=Release"
set "MS_7=Git"
set "MS_8=Git"
set "MS_9=Git"
set "MS_10=Maint"
set "MS_11=Git"
set "MS_12=Maint"

set "MH_1=Vytvori/prepise .env (token, owner, repo, identita)."
set "MH_2=Overi zda tvuj GITHUB_TOKEN ma spravne permissions."
set "MH_3=Nainstaluje requirements.txt + pyinstaller pres 'python -m pip'."
set "MH_4=Spusti 'python -m PyInstaller' - NEJDRIV regeneruje icon.ico z web_favicon.ico (F-14)."
set "MH_5=Pre-flight kontroly -> push preview -> commit+push+tag %TAG%. GitHub Actions zbuilduje .exe."
set "MH_6=Vytvori release s uz zbuildenym .exe pres gh CLI."
set "MH_7=Zobrazi lokalni git status, vetve a tagy."
set "MH_8=Smaze tag %TAG% lokalne i na GitHubu (pokud blokuje push)."
set "MH_9=Otevre repo/releases/actions/issues v prohlizeci."
set "MH_10=Znovu zjisti stav Pythonu, Gitu, tagu a .env (pomale - siti)."
set "MH_11=Rychly commit + push beze zmeny verze (bez tagu) + preview."
set "MH_12=Prepise git historii a odstrani PAT tokeny - reseni GitHub Push Protection."

set "MENU_POS=1"

REM --- Prvotni detekce statusu ---
call :load_env
call :detect_status_fast
call :detect_status_slow

if defined ZH_DEBUG (
    echo [DEBUG] Initial scan done. Press any key...
    pause >nul
)

REM --- Direct actions via CLI ---
if "%DIRECT_ACTION%"=="wizard" goto release_wizard

:render
cls
call :draw_banner
call :draw_status
echo.
echo   !C_DIM!Ovladani:!C_R!  !C_CYN!W/S!C_R! nahoru/dolu  !C_CYN!D/Enter!C_R! potvrdit  !C_CYN!1-9!C_R! primo  !C_CYN!T!C_R!^>Wizard  !C_CYN!V!C_R!^>Preview  !C_CYN!Q!C_R! konec
echo.
call :draw_menu
echo.
echo   !C_GRY!---------------------------------------------------------------------------!C_R!
call set "_H=%%MH_%MENU_POS%%%"
echo   !C_DIM!Napoveda:!C_R!  !_H!
echo.

REM Accept W/S (nav), A/D (back/confirm), Q (quit), 1-9 (direct),
REM R (refresh), plus new T (wizard) and V (preview).
choice /c WSADQ123456789RTV /n >nul
set "K=!errorlevel!"

if "%K%"=="1" goto key_up
if "%K%"=="2" goto key_down
if "%K%"=="3" goto key_back
if "%K%"=="4" goto key_select
if "%K%"=="5" goto end
if "%K%"=="15" goto key_refresh
if "%K%"=="16" goto release_wizard
if "%K%"=="17" goto push_preview_menu
if %K% geq 6 if %K% leq 14 (
    set /a "N=K-5"
    if !N! leq %MI_COUNT% (
        set "MENU_POS=!N!"
        goto key_select
    )
)
goto render

:key_up
set /a "MENU_POS-=1"
if %MENU_POS% lss 1 set "MENU_POS=%MI_COUNT%"
goto render

:key_down
set /a "MENU_POS+=1"
if %MENU_POS% gtr %MI_COUNT% set "MENU_POS=1"
goto render

:key_back
goto render

:key_refresh
call :refresh_banner "Obnovuji status..."
call :load_env
call :detect_status_fast
call :detect_status_slow
goto render

:key_select
if %MENU_POS%==1 goto configure_env
if %MENU_POS%==2 goto test_token
if %MENU_POS%==3 goto install_deps
if %MENU_POS%==4 goto build_exe
if %MENU_POS%==5 goto auto_release
if %MENU_POS%==6 goto manual_release
if %MENU_POS%==7 goto git_status
if %MENU_POS%==8 goto delete_tag
if %MENU_POS%==9 goto open_github
if %MENU_POS%==10 goto key_refresh
if %MENU_POS%==11 goto quick_push
if %MENU_POS%==12 goto cleanup_secret
goto render

REM =======================================================================
REM  UI HELPERS
REM =======================================================================

:draw_banner
echo.
echo   !C_CYN!+=========================================================================+!C_R!
echo   !C_CYN!^|!C_R!   !C_B!!C_WHT!Z E D D I H U B   T O O L S   D E S K T O P!C_R!    Release Mgr !C_MAG!v%VERSION%!C_R!  !C_CYN!^|!C_R!
echo   !C_CYN!+=========================================================================+!C_R!
exit /b 0

:draw_status
echo   !C_DIM!Status:!C_R!
echo     !C_DIM!.env            !C_R! !STATUS_ENV!
echo     !C_DIM!GITHUB_TOKEN    !C_R! !STATUS_TOKEN!
echo     !C_DIM!Python          !C_R! !STATUS_PYTHON!
echo     !C_DIM!PyInstaller     !C_R! !STATUS_PYI!
echo     !C_DIM!Git branch      !C_R! !STATUS_BRANCH!
echo     !C_DIM!Lokalni .exe    !C_R! !STATUS_EXE!
echo     !C_DIM!Remote tag      !C_R! !STATUS_TAG!
exit /b 0

:draw_menu
set "LAST_SEC="
for /l %%i in (1,1,%MI_COUNT%) do call :print_item %%i
exit /b 0

:print_item
set "IDX=%~1"
call set "LABEL=%%MI_%IDX%%%"
call set "SEC=%%MS_%IDX%%%"
if not "!SEC!"=="!LAST_SEC!" (
    echo.
    echo   !C_YEL!-- !SEC! --!C_R!
    set "LAST_SEC=!SEC!"
)
if "%IDX%"=="%MENU_POS%" (
    echo     !C_GRN!^>^> [%IDX%] !LABEL!!C_R!
) else (
    echo        !C_GRY![%IDX%]!C_R! !LABEL!
)
exit /b 0

:refresh_banner
cls
echo.
echo   !C_CYN!%~1!C_R!
echo.
exit /b 0

:header
echo.
echo   !C_CYN!+------------------------------------------------------------------+!C_R!
echo   !C_CYN!^|!C_R!  !C_B!!C_WHT!%~1!C_R!
echo   !C_CYN!+------------------------------------------------------------------+!C_R!
echo.
exit /b 0

:pause_and_return
echo.
echo   !C_DIM!Stiskni libovolnou klavesu pro navrat do menu...!C_R!
pause >nul
call :load_env
call :detect_status_fast
goto render

:pause_and_return_rescan
echo.
echo   !C_DIM!Stiskni libovolnou klavesu pro navrat do menu...!C_R!
pause >nul
call :load_env
call :detect_status_fast
call :detect_status_slow
goto render

:ok
echo   !C_GRN![OK]!C_R!    %~1
exit /b 0

:err
echo   !C_RED![CHYBA]!C_R! %~1
exit /b 0

:info
echo   !C_CYN![INFO]!C_R!  %~1
exit /b 0

:warn
echo   !C_YEL![POZOR]!C_R! %~1
exit /b 0

:step
REM Step header for wizard mode: :step "1/7" "Bump verze"
echo.
echo   !C_MAG!== Krok %~1 ==!C_R!  !C_B!!C_WHT!%~2!C_R!
echo   !C_GRY!---------------------------------------------------------------!C_R!
exit /b 0

:show_help
cls
call :draw_banner
echo.
echo   !C_B!!C_WHT!Pouziti:!C_R!
echo     !C_CYN!zeddihub.bat!C_R!            spusti interaktivni menu
echo     !C_CYN!zeddihub.bat --wizard!C_R!   spusti Release Wizard primo
echo     !C_CYN!zeddihub.bat /w!C_R!         zkraceny alias pro --wizard
echo     !C_CYN!zeddihub.bat --debug!C_R!    spusti s debug vystupem
echo     !C_CYN!zeddihub.bat /?!C_R!         zobrazi tuto napovedu
echo.
echo   !C_B!!C_WHT!Klavesove zkratky v menu:!C_R!
echo     !C_CYN!W / S!C_R!        pohyb nahoru / dolu
echo     !C_CYN!D / Enter!C_R!    potvrdit volbu
echo     !C_CYN!A!C_R!            zrusit / zpet
echo     !C_CYN!1-9!C_R!          primo skoci na polozku
echo     !C_CYN!R!C_R!            rescan statusu
echo     !C_CYN!T!C_R!            Release Wizard (step-by-step)
echo     !C_CYN!V!C_R!            Push Preview (pred pushem)
echo     !C_CYN!Q!C_R!            konec
echo.
echo   !C_B!!C_WHT!Tipy:!C_R!
echo     * Pred kazdou release/push akci se automaticky spusti pre-flight.
echo     * Build .exe vzdy regeneruje icon.ico z web_favicon.ico (F-14).
echo.
pause
exit /b 0

REM =======================================================================
REM  ENV / STATUS DETECTION
REM =======================================================================

:load_env
set "GITHUB_TOKEN="
set "GITHUB_OWNER=ZeddiS"
set "GITHUB_REPO=zeddihub-tools-desktop"
set "GITHUB_DEFAULT_BRANCH=master"
set "GIT_AUTHOR_NAME=ZeddiS"
set "GIT_AUTHOR_EMAIL="
if not exist "%ENV_FILE%" exit /b 0
for /f "usebackq tokens=* delims=" %%L in ("%ENV_FILE%") do (
    set "LINE=%%L"
    if defined LINE (
        set "CHR1=!LINE:~0,1!"
        if not "!CHR1!"=="#" (
            for /f "tokens=1,* delims==" %%A in ("!LINE!") do (
                if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
            )
        )
    )
)
exit /b 0

:detect_status_fast
if exist "%ENV_FILE%" (
    set "STATUS_ENV=!C_GRN![OK]!C_R!"
) else (
    set "STATUS_ENV=!C_RED![CHYBI]!C_R!"
)
if defined GITHUB_TOKEN (
    set "T1=!GITHUB_TOKEN:~0,15!"
    set "STATUS_TOKEN=!C_GRN![OK]!C_R! !C_DIM!!T1!...!C_R!"
) else (
    set "STATUS_TOKEN=!C_RED![CHYBI]!C_R!"
)
set "STATUS_PYTHON=!C_RED![CHYBI]!C_R!"
for /f "tokens=2" %%V in ('python --version 2^>nul') do set "STATUS_PYTHON=!C_GRN![OK]!C_R! %%V"
if exist "dist\ZeddiHubTools.exe" (
    set "STATUS_EXE=!C_GRN![OK]!C_R! dist\ZeddiHubTools.exe"
) else if exist "dist\ZeddiHub.Tools.exe" (
    set "STATUS_EXE=!C_YEL![OLD]!C_R! dist\ZeddiHub.Tools.exe"
) else (
    set "STATUS_EXE=!C_DIM![NENI]!C_R!"
)
set "STATUS_BRANCH=!C_DIM!(neni git repo)!C_R!"
for /f "usebackq" %%B in (`git branch --show-current 2^>nul`) do set "STATUS_BRANCH=!C_GRN!%%B!C_R!"
REM Git ahead/behind
for /f "usebackq tokens=1,2" %%A in (`git rev-list --left-right --count HEAD...@{upstream} 2^>nul`) do (
    if not "%%A"=="0" set "STATUS_BRANCH=!STATUS_BRANCH! !C_YEL!(+%%A ahead)!C_R!"
    if not "%%B"=="0" set "STATUS_BRANCH=!STATUS_BRANCH! !C_YEL!(-%%B behind)!C_R!"
)
exit /b 0

:detect_status_slow
set "STATUS_PYI=!C_RED![CHYBI]!C_R!"
for /f "tokens=2" %%V in ('python -m PyInstaller --version 2^>^&1') do (
    echo %%V | findstr /R "^[0-9]" >nul 2>&1 && set "STATUS_PYI=!C_GRN![OK]!C_R! %%V"
)
set "STATUS_TAG=!C_DIM!(neoveren)!C_R!"
git ls-remote --tags https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git refs/tags/%TAG% 2>nul | findstr /C:"%TAG%" >nul
if not errorlevel 1 (
    set "STATUS_TAG=!C_GRN![PUSHED]!C_R! %TAG% na GitHubu"
) else (
    set "STATUS_TAG=!C_YEL![PENDING]!C_R! %TAG% jeste nepushnut"
)
exit /b 0

REM =======================================================================
REM  PRE-FLIGHT CHECKS (spousti se pred release/push akcemi)
REM =======================================================================

:preflight
set "PF_LABEL=%~1"
set "PF_NEEDS_TOKEN=%~2"
set "PF_NEEDS_CLEAN=%~3"
set "PF_FAIL=0"
echo.
echo   !C_CYN!+-- Pre-flight kontroly (%PF_LABEL%) --------------------+!C_R!

if exist "%ENV_FILE%" (
    call :ok ".env nalezen"
) else (
    call :err ".env chybi - spust [1] Konfigurace .env"
    set "PF_FAIL=1"
)

if "%PF_NEEDS_TOKEN%"=="1" (
    if defined GITHUB_TOKEN (
        call :ok "GITHUB_TOKEN je nastaven"
    ) else (
        call :err "GITHUB_TOKEN neni nastaven v .env"
        set "PF_FAIL=1"
    )
)

where python >nul 2>&1
if errorlevel 1 (
    call :err "Python neni v PATH"
    set "PF_FAIL=1"
) else (
    call :ok "Python je dostupny"
)

git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    call :err "Toto neni git repo"
    set "PF_FAIL=1"
) else (
    call :ok "Git repo OK"
)

if "%PF_NEEDS_CLEAN%"=="1" (
    for /f %%C in ('git status --porcelain 2^>nul ^| find /c /v ""') do set "DIRTY=%%C"
    if !DIRTY! gtr 0 (
        call :warn "Strom NENI cisty - !DIRTY! zmen (zahrnou se do commitu)"
    ) else (
        call :ok "Git tree je cisty"
    )
)

if "%PF_NEEDS_TOKEN%"=="1" (
    git ls-remote --exit-code origin HEAD >nul 2>&1
    if errorlevel 1 (
        call :warn "origin nedostupny nebo chybi pristup - push muze selhat"
    ) else (
        call :ok "origin je dostupny"
    )
)

echo   !C_CYN!+--------------------------------------------------------+!C_R!
if "%PF_FAIL%"=="1" (
    echo.
    call :err "Pre-flight selhal - oprav chyby vyse."
    exit /b 1
)
exit /b 0

REM =======================================================================
REM  PUSH PREVIEW (souhrn pred pushem)
REM =======================================================================

:push_preview
set "PV_LABEL=%~1"
echo.
echo   !C_MAG!+=========================================================+!C_R!
echo   !C_MAG!^|!C_R!  !C_B!!C_WHT!PUSH PREVIEW:!C_R! %PV_LABEL%
echo   !C_MAG!+=========================================================+!C_R!
echo.
echo   !C_DIM!Branch:!C_R! !STATUS_BRANCH!
echo   !C_DIM!Remote:!C_R! https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%
echo.
echo   !C_YEL!-- Commity, ktere pujdou na GitHub --!C_R!
git log @{upstream}..HEAD --oneline --decorate 2>nul
if errorlevel 1 (
    echo   !C_DIM!(zadne nove commity proti upstreamu, nebo neni upstream)!C_R!
)
echo.
echo   !C_YEL!-- Zmeny v pracovni kopii (staged+unstaged) --!C_R!
git status --short 2>nul
echo.
echo   !C_YEL!-- Lokalni tagy (poslednich 5) --!C_R!
git for-each-ref --count=5 --sort=-creatordate --format="  %%(refname:short)  %%(creatordate:short)" refs/tags 2>nul
echo.
echo   !C_YEL!-- Build stav --!C_R!
echo     .exe:           !STATUS_EXE!
echo     Remote tag:     !STATUS_TAG!
echo.
echo   !C_MAG!+=========================================================+!C_R!
echo.
set "PV_CONFIRM="
set /p "PV_CONFIRM=  Potvrd akci napsanim !C_GRN!YES!C_R! (cokoli jineho preskoci): "
if /i "!PV_CONFIRM!"=="YES" exit /b 0
call :info "Zruseno uzivatelem."
exit /b 1

:push_preview_menu
call :header "Push Preview (samostatne)"
call :push_preview "Aktualni stav (bez akce)"
call :info "Toto byl jen preview, zadna akce nebyla provedena."
goto pause_and_return

REM =======================================================================
REM  [1] KONFIGURACE .env
REM =======================================================================
:configure_env
call :header "[1] Konfigurace .env"
if exist "%ENV_FILE%" (
    call :warn ".env jiz existuje. Bude prepsan."
    echo.
)
echo   Zadej hodnoty (Enter = ponechat default):
echo.
set /p "IN_TOKEN=  GITHUB_TOKEN (github_pat_...): "
set /p "IN_OWNER=  GITHUB_OWNER [ZeddiS]: "
set /p "IN_REPO=  GITHUB_REPO [zeddihub-tools-desktop]: "
set /p "IN_BRANCH=  GITHUB_DEFAULT_BRANCH [master]: "
set /p "IN_NAME=  GIT_AUTHOR_NAME [ZeddiS]: "
set /p "IN_EMAIL=  GIT_AUTHOR_EMAIL: "

if "%IN_OWNER%"=="" set "IN_OWNER=ZeddiS"
if "%IN_REPO%"=="" set "IN_REPO=zeddihub-tools-desktop"
if "%IN_BRANCH%"=="" set "IN_BRANCH=master"
if "%IN_NAME%"=="" set "IN_NAME=ZeddiS"

(
    echo # ZeddiHub Tools Desktop - runtime secrets ^(NIKDY NECOMMITUJ^)
    echo # Tento soubor je v .gitignore.
    echo.
    echo GITHUB_TOKEN=%IN_TOKEN%
    echo.
    echo GITHUB_OWNER=%IN_OWNER%
    echo GITHUB_REPO=%IN_REPO%
    echo GITHUB_DEFAULT_BRANCH=%IN_BRANCH%
    echo.
    echo GIT_AUTHOR_NAME=%IN_NAME%
    echo GIT_AUTHOR_EMAIL=%IN_EMAIL%
) > "%ENV_FILE%"

call :ok ".env zapsan do %ENV_FILE%"
goto pause_and_return_rescan

REM =======================================================================
REM  [2] TEST GITHUB_TOKEN
REM =======================================================================
:test_token
call :header "[2] Test GITHUB_TOKEN"
if not defined GITHUB_TOKEN (
    call :err "GITHUB_TOKEN neni nastaven. Spust [1] Konfigurace .env."
    goto pause_and_return
)
echo   Testuji token proti GitHub API...
echo.
echo   !C_DIM!/user endpoint:!C_R!
curl --ssl-no-revoke -s -o nul -w "     HTTP %%{http_code}\n" -H "Authorization: Bearer %GITHUB_TOKEN%" -H "Accept: application/vnd.github+json" "https://api.github.com/user"
echo.
echo   !C_DIM!/repos/%GITHUB_OWNER%/%GITHUB_REPO% endpoint:!C_R!
curl --ssl-no-revoke -s -o nul -w "     HTTP %%{http_code}\n" -H "Authorization: Bearer %GITHUB_TOKEN%" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/%GITHUB_OWNER%/%GITHUB_REPO%"
echo.
echo   !C_DIM!Rate limit:!C_R!
curl --ssl-no-revoke -s -H "Authorization: Bearer %GITHUB_TOKEN%" "https://api.github.com/rate_limit" | findstr /R "limit remaining reset" | findstr /V "core search graphql"
echo.
call :info "HTTP 200 = OK, 401 = spatny token, 404 = chybi permissions"
goto pause_and_return

REM =======================================================================
REM  [3] DEPENDENCIES
REM =======================================================================
:install_deps
call :header "[3] Dependencies (Python + PyInstaller)"
where python >nul 2>&1
if errorlevel 1 (
    call :err "Python neni v PATH. Nainstaluj z https://www.python.org/"
    goto pause_and_return
)
echo   Instaluji requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
echo.
call :ok "Hotovo."
goto pause_and_return_rescan

REM =======================================================================
REM  [4] BUILD .exe (with icon regeneration - F-14)
REM =======================================================================
:build_exe
call :header "[4] Build .exe lokalne"
if not exist "ZeddiHubTools.spec" (
    call :err "ZeddiHubTools.spec nenalezen."
    goto pause_and_return
)

REM -------- F-14: regenerate icon BEFORE PyInstaller runs --------
if exist "assets\web_favicon.ico" (
    echo   !C_CYN![F-14]!C_R! Regeneruji assets\icon.ico z assets\web_favicon.ico...
    copy /Y "assets\web_favicon.ico" "assets\icon.ico" >nul
    if exist "assets\icon.ico" (
        call :ok "icon.ico obnovena (favicon sync)."
    ) else (
        call :warn "Kopie selhala, build pouzije existujici icon.ico."
    )
) else (
    call :warn "assets\web_favicon.ico neexistuje - build pouzije existujici icon.ico."
)
REM -------------------------------------------------------------

echo.
echo   Spoustim PyInstaller (muze trvat minutu)...
python -m PyInstaller ZeddiHubTools.spec --clean --noconfirm
echo.
if exist "dist\ZeddiHubTools.exe" (
    call :ok "Build uspesny: dist\ZeddiHubTools.exe"
    for %%A in ("dist\ZeddiHubTools.exe") do echo   !C_DIM!Velikost: %%~zA B!C_R!
) else (
    call :err "Build selhal - .exe nenalezen v dist\"
)
goto pause_and_return_rescan

REM =======================================================================
REM  [5] AUTO RELEASE (with pre-flight + push preview)
REM =======================================================================
:auto_release
call :header "[5] Auto Release (commit+push+Actions)"
call :preflight "Auto Release %TAG%" 1 0
if errorlevel 1 goto pause_and_return

call :push_preview "Auto Release %TAG% (commit + push + tag)"
if errorlevel 1 goto pause_and_return

echo.
echo   !C_DIM!Probehne:!C_R!
echo     1. git config user.name/email
echo     2. git add -A  (auth.json a .env budou vyloucene)
echo     3. git commit -m "Release %TAG%"
echo     4. git push origin %GITHUB_DEFAULT_BRANCH%
echo     5. git tag %TAG%
echo     6. git push origin %TAG%  (spusti GitHub Actions)
echo.
git config user.name "%GIT_AUTHOR_NAME%" 2>nul
if defined GIT_AUTHOR_EMAIL git config user.email "%GIT_AUTHOR_EMAIL%" 2>nul
if exist ".git\index.lock" del /f /q ".git\index.lock" 2>nul
git add -A
git reset HEAD -- webhosting/data/auth.json 2>nul
git reset HEAD -- .env 2>nul
git commit -m "Release %TAG%" || call :info "(nic k commitnuti)"
echo.
echo   Push master (vystup se uklada do .zh_push.log pro detekci chyb)...
git push origin %GITHUB_DEFAULT_BRANCH% > .zh_push.log 2>&1
type .zh_push.log
findstr /C:"Push cannot contain secrets" /C:"GH013" /C:"unblock-secret" .zh_push.log >nul
if not errorlevel 1 goto push_secret_blocked
findstr /R /C:"! .*rejected" /C:"failed to push" .zh_push.log >nul
if not errorlevel 1 goto auto_err
del .zh_push.log 2>nul
git tag %TAG% 2>nul || call :info "(tag uz existuje lokalne)"
echo.
echo   Push tagu %TAG%...
git push origin %TAG% > .zh_push.log 2>&1
type .zh_push.log
findstr /R /C:"! .*rejected" /C:"failed to push" .zh_push.log >nul
if not errorlevel 1 goto auto_err
del .zh_push.log 2>nul
call :ok "Release pushnut. Sleduj build na:"
echo      !C_CYN!https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions!C_R!
goto pause_and_return_rescan

:push_secret_blocked
echo.
call :err "Push zablokoval GitHub Push Protection - v historii je secret (PAT)."
echo.
echo   GitHub detekoval GitHub Personal Access Token v jednom z commitu.
echo   Dve moznosti:
echo.
echo     !C_GRN![A]!C_R! Allow-list pres GitHub UI (secret zustane v historii, push projde)
echo     !C_YEL![B]!C_R! Prepsat historii pres git filter-repo (cisty - secret zmizi)
echo.
choice /c ABX /n /m "  [A]llow / [B]prepsat / [X] zrusit: "
if errorlevel 3 goto pause_and_return
if errorlevel 2 goto cleanup_secret
for /f "tokens=*" %%U in ('findstr /C:"unblock-secret" .zh_push.log') do (
    set "UNBLOCK_LINE=%%U"
)
if defined UNBLOCK_LINE (
    echo.
    echo   Otevirani unblock URL v prohlizeci...
    for /f "tokens=2 delims= " %%H in ("!UNBLOCK_LINE!") do start "" "%%H"
) else (
    start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/security/secret-scanning"
)
echo.
call :warn "Na webu: vyber duvod 'Used in tests' nebo 'Revoked' a klikni Allow."
call :info "Az schvalis, spust znovu [5] Auto Release."
del .zh_push.log 2>nul
goto pause_and_return

:auto_err
echo.
if exist .zh_push.log (
    echo   Detailni vystup pushe:
    type .zh_push.log
    del .zh_push.log 2>nul
)
call :err "Git push selhal. Zkontroluj pristup a stav."
goto pause_and_return

REM =======================================================================
REM  [6] MANUAL RELEASE
REM =======================================================================
:manual_release
call :header "[6] Manual Release (gh CLI)"
where gh >nul 2>&1
if errorlevel 1 (
    call :err "gh CLI neni v PATH. Nainstaluj z https://cli.github.com/"
    goto pause_and_return
)
if not exist "dist\ZeddiHubTools.exe" (
    call :err "dist\ZeddiHubTools.exe neexistuje. Spust [4] Build."
    goto pause_and_return
)
set "RN_FILE=release_notes_%TAG%.md"
echo   Vytvarim release %TAG% s .exe...
if exist "%RN_FILE%" (
    call :info "Nalezen %RN_FILE% - pouziji jako release body."
    gh release create %TAG% "dist\ZeddiHubTools.exe" --title "%TAG%" --notes-file "%RN_FILE%"
) else (
    call :warn "%RN_FILE% nenalezen - pouziji --generate-notes z commits."
    gh release create %TAG% "dist\ZeddiHubTools.exe" --title "%TAG%" --generate-notes
)
goto pause_and_return_rescan

REM =======================================================================
REM  [7] GIT STATUS
REM ========================================