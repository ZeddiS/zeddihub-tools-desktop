@echo off
REM =======================================================================
REM  ZeddiHub Tools Desktop - AUTO RELEASE pres GitHub Actions
REM =======================================================================
REM  Co tento skript udela:
REM    1) Nacte GITHUB_TOKEN z .env
REM    2) Nastavi git identitu (ZeddiS / 4story.csorgo@seznam.cz)
REM    3) Staguje vsechny zmeny KROME webhosting/data/auth.json (obsahuje plaintext hesla)
REM    4) Commit s message "release: v1.7.0"
REM    5) Vytvori anotovany tag v1.7.0
REM    6) Push master + tag na GitHub (pres HTTPS s tokenem)
REM    7) GitHub Actions automaticky zbuilduje .exe a vytvori release
REM
REM  Release bude dostupny za ~3-5 minut na:
REM    https://github.com/ZeddiS/zeddihub-tools-desktop/releases/tag/v1.7.0
REM
REM  POZADAVKY:
REM    - git nainstalovan a v PATH
REM    - soubor .env s GITHUB_TOKEN=github_pat_...
REM =======================================================================

setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ================================================
echo  ZeddiHub Tools Desktop - Auto Release v1.7.0
echo ================================================
echo.

REM --- [1] Overit .env ---
if not exist ".env" (
    echo CHYBA: Soubor .env nenalezen. Nastavte GITHUB_TOKEN v .env.
    pause
    exit /b 1
)

REM Nacist .env (pouze GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO)
for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    set "LINE=%%A"
    REM preskocit komentare a prazdne radky
    if not "!LINE:~0,1!"=="#" if not "!LINE!"=="" (
        set "%%A=%%B"
    )
)

if not defined GITHUB_TOKEN (
    echo CHYBA: GITHUB_TOKEN nenalezen v .env
    pause
    exit /b 1
)
if not defined GITHUB_OWNER set "GITHUB_OWNER=ZeddiS"
if not defined GITHUB_REPO set "GITHUB_REPO=zeddihub-tools-desktop"

echo [1/7] Token nacten (prvni znaky: %GITHUB_TOKEN:~0,15%...)

REM --- [1.5] Odstranit pripadny stale git lock (z predchozi session) ---
if exist ".git\index.lock" (
    echo [1.5/7] Odstranuji stale git index.lock...
    del /f /q ".git\index.lock" 2>nul
)

REM --- [2] Git identita ---
echo [2/7] Nastaveni git identity...
git config user.name "ZeddiS" >nul
git config user.email "4story.csorgo@seznam.cz" >nul

REM --- [3] Overit, ze jsme na spravne vetvi ---
for /f %%B in ('git branch --show-current 2^>nul') do set "BRANCH=%%B"
if not "%BRANCH%"=="master" (
    echo UPOZORNENI: Nejste na vetvi 'master', jste na '%BRANCH%'.
    echo Pokracovat? ^(A = ano, N = zrusit^)
    choice /c AN /n /m "Volba: "
    if errorlevel 2 exit /b 1
)

REM --- [3.5] Obnovit omylem smazane tracked assets (icon.ico, logo_icon.png) ---
echo [3/7] Obnovuji omylem smazane tracked soubory...
if not exist "assets\icon.ico" git restore assets/icon.ico >nul 2>&1
if not exist "assets\logo_icon.png" git restore assets/logo_icon.png >nul 2>&1

REM --- [4] Stage vsech zmen KROME auth.json ---
echo [4/7] Staging zmen ^(vynechavam webhosting/data/auth.json - plaintext hesla^)...
git add -A
git reset HEAD -- webhosting/data/auth.json >nul 2>&1

REM --- [5] Commit (povolit prazdny commit, kdyby uz vse bylo zcommitovano drive) ---
echo [5/7] Vytvareni commitu...
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "release: v1.7.0 - N-01/05/12-15 + F-07/F-08 + fixes" || goto error
) else (
    echo ^(zadne nove zmeny ke commitu - pokracuji^)
)

REM --- [6] Vytvorit tag ---
echo [6/7] Vytvareni tagu v1.7.0...
git tag -a v1.7.0 -m "Release v1.7.0" 2>nul
if errorlevel 1 (
    echo ^(tag v1.7.0 uz existuje^)
) else (
    echo ^(tag v1.7.0 vytvoren^)
)

REM --- [7] Push pres HTTPS s tokenem ---
echo [7/7] Push master + tag na GitHub ^(pres HTTPS s tokenem^)...
set "REMOTE_URL=https://%GITHUB_TOKEN%@github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git"

git push "%REMOTE_URL%" master || goto error
git push "%REMOTE_URL%" v1.7.0 || goto error

REM --- [8] Hotovo ---
echo.
echo =========================================
echo  PUSH USPESNY - GITHUB ACTIONS BEZI!
echo =========================================
echo.
echo  Sledujte build a automaticky vytvoreny release:
echo    https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions
echo.
echo  Release bude za 3-5 minut na:
echo    https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/releases/tag/v1.7.0
echo.
echo  Pokud se Actions zasekne na buildu, spustte build.bat lokalne
echo  a release.bat pro rucni upload .exe.
echo.
pause
exit /b 0

:error
echo.
echo =========================================
echo  CHYBA: Push selhal. Viz vystup vyse.
echo =========================================
echo.
echo Mozne priciny:
echo  - Token nema permission 'Contents: Read and write'
echo  - Spatne GITHUB_OWNER/GITHUB_REPO v .env
echo  - Tag v1.7.0 uz pushnuty a nelze prepsat ^(smazte rucne na GitHubu^)
echo.
pause
exit /b 1
