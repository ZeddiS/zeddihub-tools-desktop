@echo off
REM Tento skript je zastaraly. Vsechno je nyni v centralnim zeddihub.bat.
echo Tento skript (test_token.bat) je nahrazen souborem zeddihub.bat.
echo Spoustim zeddihub.bat - zvolte [2] Test GITHUB_TOKEN.
echo.
cd /d "%~dp0"
call zeddihub.bat
exit /b 0
