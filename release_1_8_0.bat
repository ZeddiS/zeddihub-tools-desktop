@echo off
chcp 65001 > nul
REM ============================================================
REM ZeddiHub Tools Desktop - v1.8.0 release helper
REM ============================================================
REM   Stage vsech zmen KROME webhosting\data\auth.json,
REM   commit, tag v1.8.0, push master + tag -> GitHub Actions
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo === ZeddiHub Tools - Release v1.8.0 ===
echo.

if not exist .git (
    echo [!] Not a git repo. Aborting.
    pause
    exit /b 1
)

REM Remove any stale lock
if exist ".git\index.lock" (
    echo [0/5] Mazu stary .git\index.lock
    del /f /q ".git\index.lock"
)

echo [1/5] Kontrola git...
git --version
if errorlevel 1 (
    echo [!] git neni v PATH.
    pause
    exit /b 1
)

echo.
echo [2/5] Stage all changes except webhosting\data\auth.json...
git add -A
if errorlevel 1 goto :error

REM Odstrani citlivy soubor ze stage (produkcni hesla nesmi jit do public repa)
git reset HEAD -- webhosting/data/auth.json 1>nul 2>nul

echo.
echo Soubory, ktere se commitnou:
git diff --cached --stat
echo.
set /p CONFIRM="Commit + tag v1.8.0 + push? (y/N) "
if /I not "%CONFIRM%"=="y" goto :abort

echo.
echo [3/5] Commit...
git commit -m "release: v1.8.0 - Blur redesign + Game Opt + Advanced PC Tools + shortcuts + profile + file share + home cards + web guides + news carousel" -m "TODO: N-02, N-03, N-04, N-06, N-07, N-08, N-09, N-10, N-11, E-01, E-02"
if errorlevel 1 goto :error

echo.
echo [4/5] Tag v1.8.0...
git tag -a v1.8.0 -m "ZeddiHub Tools Desktop v1.8.0"
if errorlevel 1 goto :error

echo.
echo [5/5] Push master + tag...
git push origin master
if errorlevel 1 goto :push_error
git push origin v1.8.0
if errorlevel 1 goto :push_error

echo.
echo === HOTOVO ===
echo Actions : https://github.com/ZeddiS/zeddihub-tools-desktop/actions
echo Releases: https://github.com/ZeddiS/zeddihub-tools-desktop/releases
echo.
pause
exit /b 0

:abort
echo.
echo Preruseno. Resetuji stage.
git reset HEAD 1>nul 2>nul
pause
exit /b 0

:push_error
echo.
echo [!] Commit a tag jsou hotove lokalne, ale push selhal.
echo    Zkuste: git push origin master  a pak  git push origin v1.8.0
pause
exit /b 1

:error
echo.
echo [!] Chyba. Zkontrolujte vystup.
pause
exit /b 1
