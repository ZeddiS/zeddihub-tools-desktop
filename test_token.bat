@echo off
REM ====================================================================
REM  Rychly test: Ma muj GITHUB_TOKEN spravne permissions?
REM  Pouziva curl (soucast Windows 10/11) - neni treba nic instalovat.
REM ====================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not exist ".env" (
    echo CHYBA: .env neexistuje.
    pause
    exit /b 1
)

for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    set "LINE=%%A"
    if not "!LINE:~0,1!"=="#" if not "!LINE!"=="" (
        set "%%A=%%B"
    )
)

if not defined GITHUB_TOKEN (
    echo CHYBA: GITHUB_TOKEN neni v .env
    pause
    exit /b 1
)

echo.
echo Testuji token (prvnich 15 znaku: %GITHUB_TOKEN:~0,15%...)
echo.

echo --- Test 1: GET /user (overuje authentication) ---
curl -sS ^
  -H "Accept: application/vnd.github+json" ^
  -H "Authorization: Bearer %GITHUB_TOKEN%" ^
  -H "X-GitHub-Api-Version: 2022-11-28" ^
  https://api.github.com/user
echo.
echo.

echo --- Test 2: GET /repos/ZeddiS/zeddihub-tools-desktop (overuje access to repo) ---
curl -sS -o nul -w "HTTP Status: %%{http_code}\n" ^
  -H "Accept: application/vnd.github+json" ^
  -H "Authorization: Bearer %GITHUB_TOKEN%" ^
  https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop
echo.

echo --- Test 3: GET /repos/.../releases (overuje permission: contents) ---
curl -sS -o nul -w "HTTP Status: %%{http_code}\n" ^
  -H "Accept: application/vnd.github+json" ^
  -H "Authorization: Bearer %GITHUB_TOKEN%" ^
  https://api.github.com/repos/ZeddiS/zeddihub-tools-desktop/releases
echo.
echo.
echo Pokud test 1 zobrazil JSON s "login": "ZeddiS" a testy 2-3 vratily 200, token je v poradku.
echo Pokud nektery test vratil 401/403, token ma spatne permissions nebo expiroval.
pause
