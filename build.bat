@echo off
REM ZeddiHub Tools Desktop - PyInstaller Build Script
REM Run this from the project root directory on Windows

echo ================================================
echo  ZeddiHub Tools Desktop - Build v1.7.0
echo ================================================
echo.

echo [1/4] Installing dependencies from requirements.txt...
pip install -r requirements.txt || goto error

echo.
echo [2/4] Installing PyInstaller...
pip install pyinstaller || goto error

echo.
echo [3/4] Building Windows .exe via .spec file...
pyinstaller --noconfirm ZeddiHubTools.spec || goto error

echo.
echo [4/4] Build complete!
echo Output: dist\ZeddiHubTools.exe
echo.
echo Next step: run release.bat (requires GitHub CLI 'gh' installed and logged in).
echo.
pause
exit /b 0

:error
echo.
echo ERROR: Build failed. See messages above.
echo.
pause
exit /b 1
