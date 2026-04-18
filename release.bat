@echo off
REM ================================================
REM  ZeddiHub Tools Desktop - GitHub Release v1.7.0
REM ================================================
REM  Vyzaduje nainstalovane GitHub CLI: https://cli.github.com/
REM  Pred spustenim:
REM    1) spustte build.bat  (vytvori dist\ZeddiHubTools.exe)
REM    2) `gh auth login`    (pokud jeste nejste prihlaseny)
REM  Pokud jste jeste neposlali commity, proveden bude git commit + tag push.
REM ================================================

setlocal
set TAG=v1.7.0
set TITLE=ZeddiHub Tools Desktop %TAG%
set NOTES=RELEASE_NOTES_v1.7.0.md
set EXE=dist\ZeddiHubTools.exe

echo.
echo [1/5] Overeni existence .exe...
if not exist "%EXE%" (
    echo CHYBA: "%EXE%" nenalezen. Spustte nejdriv build.bat.
    pause
    exit /b 1
)

echo.
echo [2/5] Git add, commit a tag...
git add -A
git commit -m "release: %TAG%" || echo (zadne nove zmeny ke commitu)
git tag -a %TAG% -m "Release %TAG%" || echo (tag mozna uz existuje)

echo.
echo [3/5] Push commitu a tagu na origin...
git push origin HEAD || goto error
git push origin %TAG% || goto error

echo.
echo [4/5] Vytvoreni release pres GitHub CLI...
gh release create %TAG% "%EXE%" ^
    --title "%TITLE%" ^
    --notes-file "%NOTES%" ^
    --latest || goto error

echo.
echo [5/5] Hotovo!
echo Release: https://github.com/ZeddiS/zeddihub-tools-desktop/releases/tag/%TAG%
echo.
pause
exit /b 0

:error
echo.
echo CHYBA: Vytvoreni release selhalo. Viz vystup vyse.
echo.
pause
exit /b 1
