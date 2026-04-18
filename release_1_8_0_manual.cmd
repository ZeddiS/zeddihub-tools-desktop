@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo.
echo === KROK 0: kontrola git ===
git --version
if errorlevel 1 (echo [!] git neni v PATH & pause & exit /b 1)
echo.
echo === KROK 1: stale lock check ===
if exist ".git\index.lock" (
    echo    Mazu .git\index.lock ...
    del /f /q ".git\index.lock"
)
echo.
echo === KROK 2: status ===
git status --short
echo.
pause
echo.
echo === KROK 3: stage vseho KROME auth.json ===
git add -A
git reset HEAD -- webhosting/data/auth.json
echo.
echo === KROK 4: co se commitne ===
git diff --cached --stat
echo.
pause
echo.
echo === KROK 5: commit ===
git commit -m "release: v1.8.0 - Blur redesign + Game Opt + Advanced PC Tools + shortcuts + profile + file share + home cards + web guides + news carousel" -m "TODO: N-02, N-03, N-04, N-06, N-07, N-08, N-09, N-10, N-11, E-01, E-02"
if errorlevel 1 (echo [!] commit selhal & pause & exit /b 1)
echo.
echo === KROK 6: tag ===
git tag -a v1.8.0 -m "ZeddiHub Tools Desktop v1.8.0"
if errorlevel 1 (echo [!] tag selhal & pause & exit /b 1)
echo.
echo === KROK 7: push master ===
git push origin master
if errorlevel 1 (echo [!] push master selhal & pause & exit /b 1)
echo.
echo === KROK 8: push tag ===
git push origin v1.8.0
if errorlevel 1 (echo [!] push tag selhal & pause & exit /b 1)
echo.
echo === HOTOVO ===
echo Actions: https://github.com/ZeddiS/zeddihub-tools-desktop/actions
pause
