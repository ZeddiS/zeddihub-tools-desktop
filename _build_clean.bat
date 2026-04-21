@echo off
setlocal
cd /d "%~dp0"
echo === KILL PYTHON ===
%WINDIR%\System32\taskkill.exe /F /IM python.exe 2>nul
%WINDIR%\System32\taskkill.exe /F /IM pyinstaller.exe 2>nul
%WINDIR%\System32\PING.EXE -n 3 127.0.0.1 >nul
echo === CLEAN CACHE ===
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q "%LOCALAPPDATA%\pyinstaller" 2>nul
echo === BUILD START ===
python -u -m PyInstaller ZeddiHubTools.spec --noconfirm --log-level=INFO > _build.log 2>&1
set RC=%ERRORLEVEL%
echo === BUILD DONE RC=%RC% ===
if exist dist\ZeddiHubTools.exe (
  echo EXE_OK size:
  for %%A in (dist\ZeddiHubTools.exe) do echo %%~zA
) else (
  echo EXE_MISSING
  echo --- LOG TAIL ---
  powershell -NoProfile -Command "Get-Content _build.log -Tail 40"
)
exit /b %RC%
