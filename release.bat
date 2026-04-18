@echo off
REM Tento skript je zastaraly. Vsechno je nyni v centralnim zeddihub.bat.
echo Tento skript (release.bat) je nahrazen souborem zeddihub.bat.
echo Spoustim zeddihub.bat - zvolte [5] Auto Release nebo [6] Manual Release.
echo.
cd /d "%~dp0"
call zeddihub.bat
exit /b 0
