@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

:: ═══════════════════════════════════════════════════════════════
::  ZeddiHub Tools Desktop — Dev & Release Manager
::  Sprava verzi, buildu a GitHub repozitare
:: ═══════════════════════════════════════════════════════════════

:: ── Aktivuj ANSI escape kody (Windows 10+) ────────────────────
reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
for /f %%a in ('powershell -NoProfile -Command "[char]27" 2^>nul') do set "_E=%%a"

if defined _E (
    set "R=!_E![0m"          & set "B=!_E![1m"        & set "DIM=!_E![2m"
    set "RED=!_E![91m"       & set "GRN=!_E![92m"     & set "YEL=!_E![93m"
    set "BLU=!_E![94m"       & set "CYN=!_E![96m"     & set "WHT=!_E![97m"
    set "ORG=!_E![38;5;214m" & set "PRP=!_E![95m"
) else (
    for %%c in (R B DIM RED GRN YEL BLU CYN WHT ORG PRP) do set "%%c="
)

:: ── Nacti .env (pokud existuje) ───────────────────────────────
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%k in (".env") do (
        set "_ln=%%k"
        if not "!_ln:~0,1!"=="#" if not "!_ln!"=="" set "%%k=%%l"
    )
)
if not defined GITHUB_OWNER          set "GITHUB_OWNER=ZeddiS"
if not defined GITHUB_REPO           set "GITHUB_REPO=zeddihub-tools-desktop"
if not defined GITHUB_DEFAULT_BRANCH set "GITHUB_DEFAULT_BRANCH=master"
set "_REPO=https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%"


:: ══════════════════════════════════════════════════════════════
:MAIN_MENU
cls
call :FN_BANNER
call :FN_QUICK_STATUS
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!R!
echo.
echo   !B!!ORG!  1!R!  Stav projektu         !DIM!verze, git, GitHub!R!
echo   !B!!ORG!  2!R!  Novy release          !DIM!pruvodce krok za krokem!R!
echo   !B!!ORG!  3!R!  Build .exe            !DIM!PyInstaller!R!
echo   !B!!ORG!  4!R!  Git operace           !DIM!status, pull, push, log!R!
echo   !B!!ORG!  5!R!  GitHub                !DIM!releases, issues, actions!R!
echo   !B!!ORG!  6!R!  Vycistit artefakty    !DIM!build/, dist/, __pycache__!R!
echo   !B!!ORG!  7!R!  Spustit aplikaci      !DIM!python app.py!R!
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!R!
echo   !RED!  Q!R!  Konec
echo.
set /p "_c=  Volba: "
if /i "!_c!"=="1" ( call :FN_DETAILED_STATUS & goto MAIN_MENU )
if /i "!_c!"=="2" ( call :FN_RELEASE_WIZARD  & goto MAIN_MENU )
if /i "!_c!"=="3" ( call :FN_BUILD_EXE       & goto MAIN_MENU )
if /i "!_c!"=="4" goto GIT_MENU
if /i "!_c!"=="5" goto GITHUB_MENU
if /i "!_c!"=="6" ( call :FN_CLEAN           & goto MAIN_MENU )
if /i "!_c!"=="7" ( call :FN_RUN_APP         & goto MAIN_MENU )
if /i "!_c!"=="q" goto END
goto MAIN_MENU


:: ══════════════════════════════════════════════════════════════
:GIT_MENU
cls
call :FN_BANNER
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━ GIT OPERACE ━━━━━━━━!R!
echo.
echo   !B!!ORG!  1!R!  Git status
echo   !B!!ORG!  2!R!  Git pull
echo   !B!!ORG!  3!R!  Commit + push
echo   !B!!ORG!  4!R!  Poslednich 15 commitu
echo   !B!!ORG!  5!R!  Porovnat s remote     !DIM!fetch + ahead/behind!R!
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!R!
echo   !YEL!  0!R!  Zpet do hlavniho menu
echo.
set /p "_c=  Volba: "
if "!_c!"=="1" (
    echo. & git status & echo. & call :FN_PAUSE & goto GIT_MENU
)
if "!_c!"=="2" (
    echo. & git pull & echo. & call :FN_PAUSE & goto GIT_MENU
)
if "!_c!"=="3" ( call :FN_GIT_PUSH & goto GIT_MENU )
if "!_c!"=="4" (
    echo.
    git log --oneline --graph --color --decorate -15
    echo. & call :FN_PAUSE & goto GIT_MENU
)
if "!_c!"=="5" (
    echo.
    echo   !DIM!Nacitam remote ...!R!
    git fetch >nul 2>&1
    for /f %%a in ('git rev-list --count "origin/%GITHUB_DEFAULT_BRANCH%..HEAD" 2^>nul') do set "_ah=%%a"
    for /f %%b in ('git rev-list --count "HEAD..origin/%GITHUB_DEFAULT_BRANCH%" 2^>nul') do set "_bh=%%b"
    if not defined _ah set "_ah=0"
    if not defined _bh set "_bh=0"
    echo.
    echo   !B!Commits ahead :!R!  !GRN!!_ah!!R!
    echo   !B!Commits behind:!R!  !YEL!!_bh!!R!
    echo.
    git log --oneline --decorate -5
    echo. & call :FN_PAUSE & goto GIT_MENU
)
if "!_c!"=="0" goto MAIN_MENU
goto GIT_MENU


:: ══════════════════════════════════════════════════════════════
:GITHUB_MENU
cls
call :FN_BANNER
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━━ GITHUB ━━━━━━━━━━━━!R!
echo.
echo   !B!!ORG!  1!R!  Zobrazit releases     !DIM!seznam v terminalu!R!
echo   !B!!ORG!  2!R!  Zobrazit issues       !DIM!otevrene!R!
echo   !B!!ORG!  3!R!  Status CI / Actions   !DIM!posledni workflow!R!
echo   !B!!ORG!  4!R!  Nahrat .exe k release !DIM!gh release upload!R!
echo.
echo   !B!!CYN!  ── Otevrit v prohlizeci ─────────────────!R!
echo.
echo   !B!!BLU!  5!R!  Repozitar
echo   !B!!BLU!  6!R!  Releases
echo   !B!!BLU!  7!R!  Issues
echo   !B!!BLU!  8!R!  Actions / CI
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━!R!
echo   !YEL!  0!R!  Zpet do hlavniho menu
echo.
set /p "_c=  Volba: "
if "!_c!"=="1" (
    echo. & gh release list --limit 10 & echo. & call :FN_PAUSE & goto GITHUB_MENU
)
if "!_c!"=="2" (
    echo. & gh issue list --state open --limit 20 & echo. & call :FN_PAUSE & goto GITHUB_MENU
)
if "!_c!"=="3" (
    echo. & gh run list --limit 8 & echo. & call :FN_PAUSE & goto GITHUB_MENU
)
if "!_c!"=="4" ( call :FN_UPLOAD_EXE & goto GITHUB_MENU )
if "!_c!"=="5" ( start "" "%_REPO%"                & goto GITHUB_MENU )
if "!_c!"=="6" ( start "" "%_REPO%/releases"       & goto GITHUB_MENU )
if "!_c!"=="7" ( start "" "%_REPO%/issues"         & goto GITHUB_MENU )
if "!_c!"=="8" ( start "" "%_REPO%/actions"        & goto GITHUB_MENU )
if "!_c!"=="0" goto MAIN_MENU
goto GITHUB_MENU


:: ══════════════════════════════════════════════════════════════
::   F U N K C E
:: ══════════════════════════════════════════════════════════════

:FN_BANNER
echo.
echo   !B!!ORG!  ╔═════════════════════════════════════════════╗!R!
echo   !B!!ORG!  ║   ZeddiHub Tools Desktop  ·  Dev Manager   ║!R!
echo   !B!!ORG!  ╚═════════════════════════════════════════════╝!R!
echo.
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_QUICK_STATUS
set "_ver=?"
for /f "tokens=3 delims= " %%v in ('findstr /c:"APP_VERSION = " gui\version.py 2^>nul') do (
    set "_ver=%%v" & set "_ver=!_ver:"=!"
)
for /f %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "_br=%%b"
if not defined _br set "_br=?"
git diff --quiet 2>nul && git diff --cached --quiet 2>nul && (
    set "_gs=!GRN!cisty!R!"
) || (
    set "_gs=!YEL!neulozene zmeny!R!"
)
for /f %%h in ('git log -1 --format^=%%h 2^>nul') do set "_sh=%%h"
echo   !DIM!Verze:!R! !B!!ORG!v!_ver!!R!   !DIM!Vetev:!R! !B!!_br!!R!   !DIM!Git:!R! !_gs!   !DIM!SHA:!R! !DIM!!_sh!!R!
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_DETAILED_STATUS
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━ STAV PROJEKTU ━━━━━━━!R!
echo.
set "_ver=?"
for /f "tokens=3 delims= " %%v in ('findstr /c:"APP_VERSION = " gui\version.py 2^>nul') do (
    set "_ver=%%v" & set "_ver=!_ver:"=!"
)
echo   !DIM!Lokalni verze    :!R! !B!!GRN!v!_ver!!R!
echo   !DIM!Nacitam GitHub ...!R!
for /f "tokens=1" %%r in ('gh release list --limit 1 2^>nul') do set "_ghr=%%r"
if defined _ghr (
    echo   !DIM!Nejnovejsi release:!R! !B!!GRN!!_ghr!!R!
) else (
    echo   !DIM!Nejnovejsi release:!R! !YEL!nedostupne!R!
)
echo.
for /f %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "_br=%%b"
echo   !DIM!Git vetev         :!R! !B!!_br!!R!
echo.
echo   !B!Poslednich 5 commitu:!R!
git log --oneline --graph --color --decorate -5
echo.
git fetch >nul 2>&1
for /f %%a in ('git rev-list --count "origin/%GITHUB_DEFAULT_BRANCH%..HEAD" 2^>nul') do set "_ah=%%a"
for /f %%b in ('git rev-list --count "HEAD..origin/%GITHUB_DEFAULT_BRANCH%" 2^>nul') do set "_bh=%%b"
if not defined _ah set "_ah=0"
if not defined _bh set "_bh=0"
echo   !DIM!Commits ahead     :!R! !GRN!!_ah!!R!   !DIM!behind:!R! !YEL!!_bh!!R!
echo.
echo   !B!Zmenene soubory:!R!
git status --short
echo.
call :FN_PAUSE
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_RELEASE_WIZARD
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━ NOVY RELEASE ━━━━━━!R!
echo.
set "_ver=?"
for /f "tokens=3 delims= " %%v in ('findstr /c:"APP_VERSION = " gui\version.py 2^>nul') do (
    set "_ver=%%v" & set "_ver=!_ver:"=!"
)
echo   !DIM!Aktualni verze :!R! !B!!ORG!v!_ver!!R!
echo.
set /p "_nv=  Nova verze (bez 'v', prazdne = zrusit): "
if "!_nv!"=="" ( echo   !YEL!Zruseno.!R! & call :FN_PAUSE & exit /b )
echo.

:: [1/5] gui/version.py
echo   !DIM![1/5]!R! !B!Aktualizuji gui\version.py ...!R!
powershell -NoProfile -Command ^
    "(Get-Content 'gui\version.py' -Encoding UTF8) -replace 'APP_VERSION = ""[^""]*""','APP_VERSION = ""!_nv!""' | Set-Content 'gui\version.py' -Encoding UTF8" >nul 2>&1
echo   !GRN![OK]!R! gui\version.py  ->  v!_nv!

:: [2/5] version.json
echo   !DIM![2/5]!R! !B!Aktualizuji version.json ...!R!
powershell -NoProfile -Command ^
    "$j=(Get-Content 'version.json'|ConvertFrom-Json); $j.version='!_nv!'; ($j|ConvertTo-Json)|Set-Content 'version.json' -Encoding UTF8" >nul 2>&1
echo   !GRN![OK]!R! version.json     ->  v!_nv!

:: [3/5] CHANGELOG.md
echo   !DIM![3/5]!R! !B!Otevri CHANGELOG.md a doplň zaznam pro v!_nv! ...!R!
start "" CHANGELOG.md
echo   !YEL![CEKAM]!R! Uloz soubor a stiskni Enter.
call :FN_PAUSE

:: [4/5] Commit + tag
echo   !DIM![4/5]!R! !B!Pripravuji commit ...!R!
echo.
git status --short
echo.
echo   !YEL!Pokracovat s commitem? (A/n)!R!
set /p "_ok=  "
if /i "!_ok!"=="n" (
    echo   !YEL!Zruseno — soubory jsou zmeneny, ale commit nebyl vytvoren.!R!
    call :FN_PAUSE & exit /b
)
git add gui\version.py version.json CHANGELOG.md
git commit -m "Release v!_nv!"
echo   !GRN![OK]!R! Commit vytvoren
git tag "v!_nv!"
echo   !GRN![OK]!R! Tag v!_nv! vytvoren

:: [5/5] Push
echo.
echo   !DIM![5/5]!R! !B!Push na GitHub:!R!
echo.
git log --oneline -3
echo.
echo   !YEL!Pokracovat s push? (A/n)!R!
set /p "_pp=  "
if /i "!_pp!"=="n" (
    echo   !YEL!Push zrusen. Tag + commit existuji lokalne.!R!
    call :FN_PAUSE & exit /b
)
git push
git push origin "v!_nv!"
if !ERRORLEVEL! neq 0 (
    echo   !RED![CHYBA]!R! Push selhal.
    call :FN_PAUSE & exit /b
)
echo   !GRN![OK]!R! Push dokoncen
echo.

:: GitHub release
echo   !YEL!Vytvorit GitHub release v!_nv!? (A/n)!R!
set /p "_gr=  "
if /i "!_gr!"=="n" ( call :FN_PAUSE & exit /b )
set "_nf=release_notes_v!_nv!.md"
if exist "!_nf!" (
    gh release create "v!_nv!" --title "ZeddiHub Tools Desktop v!_nv!" --notes-file "!_nf!"
) else (
    set /p "_rn=  Kratky popis (nebo Enter pro vychozi): "
    if "!_rn!"=="" set "_rn=Release v!_nv!"
    gh release create "v!_nv!" --title "ZeddiHub Tools Desktop v!_nv!" --notes "!_rn!"
)
if !ERRORLEVEL! equ 0 (
    echo   !GRN![OK]!R! GitHub release v!_nv! vytvoren
    start "" "%_REPO%/releases/tag/v!_nv!"
) else (
    echo   !RED![CHYBA]!R! Nepodarilo se vytvorit release.
)
echo.
call :FN_PAUSE
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_BUILD_EXE
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━━ BUILD .EXE ━━━━━━━!R!
echo.
if not exist "ZeddiHubTools.spec" (
    echo   !RED![CHYBA]!R! ZeddiHubTools.spec nenalezen!
    call :FN_PAUSE & exit /b
)
echo   !YEL![INFO]!R! Spoustim PyInstaller ...
echo.
pyinstaller --noconfirm ZeddiHubTools.spec
echo.
if exist "dist\ZeddiHubTools.exe" (
    for %%f in ("dist\ZeddiHubTools.exe") do set /a "_mb=%%~zf / 1048576"
    echo   !GRN![OK]!R! Build uspesny  (!_mb! MB)
    echo.
    echo   !YEL!Nahrat .exe k existujicimu GitHub release? (A/n)!R!
    set /p "_up=  "
    if /i not "!_up!"=="n" call :FN_UPLOAD_EXE
) else (
    echo   !RED![CHYBA]!R! Build selhal — ZeddiHubTools.exe nenalezen.
)
echo.
call :FN_PAUSE
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_UPLOAD_EXE
echo.
if not exist "dist\ZeddiHubTools.exe" (
    echo   !RED![CHYBA]!R! dist\ZeddiHubTools.exe neexistuje. Sestav nejdrive .exe.
    call :FN_PAUSE & exit /b
)
echo   !B!Dostupne releases:!R!
gh release list --limit 5 2>&1
echo.
set /p "_rt=  Tag release (napr. v2.0.0, prazdne = zrusit): "
if "!_rt!"=="" ( echo   !YEL!Zruseno.!R! & exit /b )
gh release upload "!_rt!" "dist\ZeddiHubTools.exe" --clobber
if !ERRORLEVEL! equ 0 (
    echo   !GRN![OK]!R! ZeddiHubTools.exe nahran k release !_rt!
) else (
    echo   !RED![CHYBA]!R! Nahravani selhalo.
)
echo.
call :FN_PAUSE
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_GIT_PUSH
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━ COMMIT + PUSH ━━━━━━!R!
echo.
git status --short
echo.
set /p "_msg=  Zprava commitu (prazdne = zrusit): "
if "!_msg!"=="" ( echo   !YEL!Zruseno.!R! & call :FN_PAUSE & exit /b )
git add -A
git commit -m "!_msg!"
if !ERRORLEVEL! equ 0 (
    echo   !GRN![OK]!R! Commit vytvoren
    git push
    if !ERRORLEVEL! equ 0 ( echo   !GRN![OK]!R! Push dokoncen ) else ( echo   !RED![CHYBA]!R! Push selhal. )
) else (
    echo   !RED![CHYBA]!R! Commit selhal (nic ke commitovani?).
)
echo.
call :FN_PAUSE
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_CLEAN
echo.
echo   !B!!CYN!  ━━━━━━━━━━━━━━━━━━━━ CISTENI ━━━━━━━━━━━━!R!
echo.
echo   !B!Budou smazany:!R!
if exist "build\"  echo   !DIM!  · build\!R!
if exist "dist\"   echo   !DIM!  · dist\!R!
echo   !DIM!  · __pycache__ (rekurzivne)!R!
echo.
echo   !YEL!Pokracovat? (A/n)!R!
set /p "_cc=  "
if /i "!_cc!"=="n" exit /b
if exist "build\"  ( rmdir /s /q "build\"  & echo   !GRN![OK]!R! build\ smazan )
if exist "dist\"   ( rmdir /s /q "dist\"   & echo   !GRN![OK]!R! dist\ smazan )
for /d /r %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
echo   !GRN![OK]!R! __pycache__ smazan
echo.
call :FN_PAUSE
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_RUN_APP
echo.
echo   !B!Spoustim ZeddiHub Tools Desktop ...!R!
start "" python app.py
echo   !GRN![OK]!R! Aplikace spustena
timeout /t 2 /nobreak >nul
exit /b

:: ─────────────────────────────────────────────────────────────
:FN_PAUSE
echo   !DIM!Stiskni Enter pro pokracovani ...!R!
pause >nul
exit /b

:: ══════════════════════════════════════════════════════════════
:END
echo.
echo   !DIM!Nashledanou.!R!
echo.
endlocal
exit /b
