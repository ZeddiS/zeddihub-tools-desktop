@echo off
REM Tento skript je zastaraly. Vsechno je nyni v centralnim zeddihub.bat.
echo Tento skript (build.bat) je nahrazen souborem zeddihub.bat.
echo Spoustim zeddihub.bat s volbou [4] Build...
echo.
cd /d "%~dp0"
call zeddihub.bat
exit /b 0
