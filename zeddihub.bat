@echo off
REM =======================================================================
REM  ZEDDIHUB TOOLS DESKTOP - Release Manager v1.7.0
REM  Windows 11 compatible, ASCII-safe, FAST (cached status).
REM =======================================================================
setlocal EnableDelayedExpansion EnableExtensions
cd /d "%~dp0"

if /i "%~1"=="--debug" set "ZH_DEBUG=1"
if /i "%~1"=="/?" goto show_help
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help

title ZeddiHub Tools Desktop - Release Manager

chcp 65001 >nul 2>&1

set "REPO_ROOT=%~dp0"
set "ENV_FILE=%REPO_ROOT%.env"
set "VERSION=1.9.0"
set "TAG=v%VERSION%"

REM --- Menu definice ---
set "MI_COUNT=12"
set "MI_1=Konfigurace .env"
set "MI_2=Test GITHUB_TOKEN"
set "MI_3=Dependencies (Python + PyInstaller)"
set "MI_4=Build .exe lokalne"
set "MI_5=Auto Release (commit+push+Actions)"
set "MI_6=Manual Release (gh CLI upload)"
set "MI_7=Git status"
set "MI_8=Smazat tag %TAG%"
set "MI_9=Otevrit GitHub v prohlizeci"
set "MI_10=Obnovit status (rescan)"
set "MI_11=Rychla push (quick commit)"
set "MI_12=Cleanup: PAT secret v historii (filter-repo)"

set "MH_1=Vytvori/prepise .env (token, owner, repo, identita)."
set "MH_2=Overi zda tvuj GITHUB_TOKEN ma spravne permissions."
set "MH_3=Nainstaluje requirements.txt + pyinstaller pres 'python -m pip'."
set "MH_4=Spusti 'python -m PyInstaller' na ZeddiHubTools.spec."
set "MH_5=Stage + commit + push + tag %TAG%. GitHub Actions zbuilduje .exe."
set "MH_6=Vytvori release s uz zbuildenym .exe pres gh CLI."
set "MH_7=Zobrazi lokalni git status, vetve a tagy."
set "MH_8=Smaze tag %TAG% lokalne i na GitHubu (pokud blokuje push)."
set "MH_9=Otevre repo/releases/actions/issues v prohlizeci."
set "MH_10=Znovu zjisti stav Pythonu, Gitu, tagu a .env (pomale - siti)."
set "MH_11=Rychly commit + push beze zmeny verze (bez tagu)."
set "MH_12=Prepise git historii a odstrani PAT tokeny - reseni GitHub Push Protection."

set "MENU_POS=1"

REM --- Prvotni detekce statusu (probehne POUZE jednou na startu) ---
call :load_env
call :detect_status_fast
call :detect_status_slow

if defined ZH_DEBUG (
    echo [DEBUG] Initial scan done. Press any key...
    pause >nul
)

:render
REM --- Toto se vola POUZE na kazdy stisk klavesy - musi byt RYCHLE! ---
cls
echo.
echo  +======================================================================+
echo  ^|  ZEDDIHUB TOOLS DESKTOP   Release Manager v%VERSION%                     ^|
echo  +======================================================================+
echo  ^|  Status systemu:
echo  ^|    .env             !STATUS_ENV!
echo  ^|    GITHUB_TOKEN     !STATUS_TOKEN!
echo  ^|    Python           !STATUS_PYTHON!
echo  ^|    PyInstaller      !STATUS_PYI!
echo  ^|    Git branch       !STATUS_BRANCH!
echo  ^|    Lokalni .exe     !STATUS_EXE!
echo  ^|    Remote tag       !STATUS_TAG!
echo  +======================================================================+
echo.
echo   Ovladani:  W/S nahoru/dolu   D/Enter potvrdit   1-9 primo   Q konec
echo.
for /l %%i in (1,1,%MI_COUNT%) do call :print_item %%i
echo.
echo   ----------------------------------------------------------------------
echo   Napoveda:  !MH_%MENU_POS%!
echo.

choice /c WSADQ123456789R /n >nul
set "K=!errorlevel!"

if "%K%"=="1" goto key_up
if "%K%"=="2" goto key_down
if "%K%"=="3" goto key_back
if "%K%"=="4" goto key_select
if "%K%"=="5" goto end
if "%K%"=="15" goto key_refresh
if %K% geq 6 if %K% leq 14 (
    set /a "N=K-5"
    if !N! leq %MI_COUNT% (
        set "MENU_POS=!N!"
        goto key_select
    )
)
goto render

:key_up
set /a "MENU_POS-=1"
if %MENU_POS% lss 1 set "MENU_POS=%MI_COUNT%"
goto render

:key_down
set /a "MENU_POS+=1"
if %MENU_POS% gtr %MI_COUNT% set "MENU_POS=1"
goto render

:key_back
goto render

:key_refresh
call :refresh_banner "Obnovuji status..."
call :load_env
call :detect_status_fast
call :detect_status_slow
goto render

:key_select
if %MENU_POS%==1 goto configure_env
if %MENU_POS%==2 goto test_token
if %MENU_POS%==3 goto install_deps
if %MENU_POS%==4 goto build_exe
if %MENU_POS%==5 goto auto_release
if %MENU_POS%==6 goto manual_release
if %MENU_POS%==7 goto git_status
if %MENU_POS%==8 goto delete_tag
if %MENU_POS%==9 goto open_github
if %MENU_POS%==10 goto key_refresh
if %MENU_POS%==11 goto quick_push
if %MENU_POS%==12 goto cleanup_secret
goto render

REM =======================================================================
REM  HELPERS - musi byt super rychle!
REM =======================================================================
:print_item
set "IDX=%~1"
call set "LABEL=%%MI_%IDX%%%"
if "%IDX%"=="%MENU_POS%" (
    echo    ^>^> [%IDX%] !LABEL!
) else (
    echo       [%IDX%] !LABEL!
)
exit /b 0

:refresh_banner
cls
echo.
echo   %~1
echo.
exit /b 0

:load_env
REM Parse .env - RYCHLE, bez site.
set "GITHUB_TOKEN="
set "GITHUB_OWNER=ZeddiS"
set "GITHUB_REPO=zeddihub-tools-desktop"
set "GITHUB_DEFAULT_BRANCH=master"
set "GIT_AUTHOR_NAME=ZeddiS"
set "GIT_AUTHOR_EMAIL="
if not exist "%ENV_FILE%" exit /b 0
for /f "usebackq tokens=* delims=" %%L in ("%ENV_FILE%") do (
    set "LINE=%%L"
    if defined LINE (
        set "CHR1=!LINE:~0,1!"
        if not "!CHR1!"=="#" (
            for /f "tokens=1,* delims==" %%A in ("!LINE!") do (
                if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
            )
        )
    )
)
exit /b 0

:detect_status_fast
REM Rychle kontroly (bez siti, bez importu Python knihoven).
if exist "%ENV_FILE%" (
    set "STATUS_ENV=[OK]"
) else (
    set "STATUS_ENV=[CHYBI]"
)
if defined GITHUB_TOKEN (
    set "T1=!GITHUB_TOKEN:~0,15!"
    set "STATUS_TOKEN=[OK] !T1!..."
) else (
    set "STATUS_TOKEN=[CHYBI]"
)
REM Python version: rychle (subprocess, bez importu)
set "STATUS_PYTHON=[CHYBI]"
for /f "tokens=2" %%V in ('python --version 2^>nul') do set "STATUS_PYTHON=[OK] %%V"
REM .exe existence: disk check
if exist "dist\ZeddiHubTools.exe" (
    set "STATUS_EXE=[OK] dist\ZeddiHubTools.exe"
) else if exist "dist\ZeddiHub.Tools.exe" (
    set "STATUS_EXE=[OLD] dist\ZeddiHub.Tools.exe"
) else (
    set "STATUS_EXE=[NENI]"
)
REM Git branch: rychle
set "STATUS_BRANCH=(neni git repo)"
for /f "usebackq" %%B in (`git branch --show-current 2^>nul`) do set "STATUS_BRANCH=%%B"
exit /b 0

:detect_status_slow
REM Pomale kontroly - pouze pri startu nebo rucne (menu polozka 10).
REM PyInstaller: pomale - importuje knihovnu
set "STATUS_PYI=[CHYBI]"
for /f "tokens=2" %%V in ('python -m PyInstaller --version 2^>^&1') do (
    echo %%V | findstr /R "^[0-9]" >nul 2>&1 && set "STATUS_PYI=[OK] %%V"
)
REM Remote tag: pomale - SIT!
set "STATUS_TAG=(neoveren)"
git ls-remote --tags https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git refs/tags/%TAG% 2>nul | findstr /C:"%TAG%" >nul
if not errorlevel 1 (
    set "STATUS_TAG=[PUSHED] %TAG% na GitHubu"
) else (
    set "STATUS_TAG=[PENDING] %TAG% jeste nepushnut"
)
exit /b 0

:header
echo.
echo  ======================================================================
echo    %~1
echo  ======================================================================
echo.
exit /b 0

:pause_and_return
echo.
echo   Stiskni libovolnou klavesu pro navrat do menu...
pause >nul
REM Po akci znovu nacteme .env a rychle checks, pomale preskocime.
call :load_env
call :detect_status_fast
goto render

:pause_and_return_rescan
REM Pouziva se po akcich, ktere zmenily stav (release, tag, build).
echo.
echo   Stiskni libovolnou klavesu pro navrat do menu...
pause >nul
call :load_env
call :detect_status_fast
call :detect_status_slow
goto render

:ok
echo   [OK]  %~1
exit /b 0

:err
echo   [CHYBA] %~1
exit /b 0

:info
echo   [INFO] %~1
exit /b 0

:warn
echo   [POZOR] %~1
exit /b 0

:show_help
echo.
echo  ZeddiHub Release Manager v%VERSION%
echo.
echo  Pouziti:
echo    zeddihub.bat           - spusti interaktivni menu
echo    zeddihub.bat --debug   - spusti s debug vystupem
echo    zeddihub.bat /?        - zobrazi tuto napovedu
echo.
pause
exit /b 0

REM =======================================================================
REM  [1] KONFIGURACE .env
REM =======================================================================
:configure_env
call :header "[1] Konfigurace .env"
if exist "%ENV_FILE%" (
    call :warn ".env jiz existuje. Bude prepsan."
    echo.
)
echo   Zadej hodnoty (Enter = ponechat default):
echo.
set /p "IN_TOKEN=  GITHUB_TOKEN (github_pat_...): "
set /p "IN_OWNER=  GITHUB_OWNER [ZeddiS]: "
set /p "IN_REPO=  GITHUB_REPO [zeddihub-tools-desktop]: "
set /p "IN_BRANCH=  GITHUB_DEFAULT_BRANCH [master]: "
set /p "IN_NAME=  GIT_AUTHOR_NAME [ZeddiS]: "
set /p "IN_EMAIL=  GIT_AUTHOR_EMAIL: "

if "%IN_OWNER%"=="" set "IN_OWNER=ZeddiS"
if "%IN_REPO%"=="" set "IN_REPO=zeddihub-tools-desktop"
if "%IN_BRANCH%"=="" set "IN_BRANCH=master"
if "%IN_NAME%"=="" set "IN_NAME=ZeddiS"

(
    echo # ZeddiHub Tools Desktop - runtime secrets ^(NIKDY NECOMMITUJ^)
    echo # Tento soubor je v .gitignore.
    echo.
    echo GITHUB_TOKEN=%IN_TOKEN%
    echo.
    echo GITHUB_OWNER=%IN_OWNER%
    echo GITHUB_REPO=%IN_REPO%
    echo GITHUB_DEFAULT_BRANCH=%IN_BRANCH%
    echo.
    echo GIT_AUTHOR_NAME=%IN_NAME%
    echo GIT_AUTHOR_EMAIL=%IN_EMAIL%
) > "%ENV_FILE%"

call :ok ".env zapsan do %ENV_FILE%"
goto pause_and_return_rescan

REM =======================================================================
REM  [2] TEST GITHUB_TOKEN
REM =======================================================================
:test_token
call :header "[2] Test GITHUB_TOKEN"
if not defined GITHUB_TOKEN (
    call :err "GITHUB_TOKEN neni nastaven. Spust [1] Konfigurace .env."
    goto pause_and_return
)
echo   Testuji token proti GitHub API...
echo.
echo   /user endpoint:
curl --ssl-no-revoke -s -o nul -w "     HTTP %%{http_code}\n" -H "Authorization: Bearer %GITHUB_TOKEN%" -H "Accept: application/vnd.github+json" "https://api.github.com/user"
echo.
echo   /repos/%GITHUB_OWNER%/%GITHUB_REPO% endpoint:
curl --ssl-no-revoke -s -o nul -w "     HTTP %%{http_code}\n" -H "Authorization: Bearer %GITHUB_TOKEN%" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/%GITHUB_OWNER%/%GITHUB_REPO%"
echo.
echo   Rate limit:
curl --ssl-no-revoke -s -H "Authorization: Bearer %GITHUB_TOKEN%" "https://api.github.com/rate_limit" | findstr /R "limit remaining reset" | findstr /V "core search graphql"
echo.
call :info "HTTP 200 = OK, 401 = spatny token, 404 = chybi permissions"
goto pause_and_return

REM =======================================================================
REM  [3] DEPENDENCIES
REM =======================================================================
:install_deps
call :header "[3] Dependencies (Python + PyInstaller)"
where python >nul 2>&1
if errorlevel 1 (
    call :err "Python neni v PATH. Nainstaluj z https://www.python.org/"
    goto pause_and_return
)
echo   Instaluji requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
echo.
call :ok "Hotovo."
goto pause_and_return_rescan

REM =======================================================================
REM  [4] BUILD .exe
REM =======================================================================
:build_exe
call :header "[4] Build .exe lokalne"
if not exist "ZeddiHubTools.spec" (
    call :err "ZeddiHubTools.spec nenalezen."
    goto pause_and_return
)
echo   Spoustim PyInstaller (muze trvat minutu)...
python -m PyInstaller ZeddiHubTools.spec --clean --noconfirm
echo.
if exist "dist\ZeddiHubTools.exe" (
    call :ok "Build uspesny: dist\ZeddiHubTools.exe"
    for %%A in ("dist\ZeddiHubTools.exe") do echo   Velikost: %%~zA B
) else (
    call :err "Build selhal - .exe nenalezen v dist\"
)
goto pause_and_return_rescan

REM =======================================================================
REM  [5] AUTO RELEASE
REM =======================================================================
:auto_release
call :header "[5] Auto Release (commit+push+Actions)"
if not defined GITHUB_TOKEN (
    call :err "GITHUB_TOKEN neni nastaven."
    goto pause_and_return
)
echo   Probehne:
echo     1. git config user.name/email (pokud nastaveno v .env)
echo     2. git add -A
echo     3. git commit -m "Release %TAG%"
echo     4. git push origin %GITHUB_DEFAULT_BRANCH%
echo     5. git tag %TAG%
echo     6. git push origin %TAG%  ^<- spusti GitHub Actions
echo.
choice /c AN /n /m "  [A]no pokracovat / [N]e zrusit: "
if errorlevel 2 goto render
echo.
git config user.name "%GIT_AUTHOR_NAME%" 2>nul
if defined GIT_AUTHOR_EMAIL git config user.email "%GIT_AUTHOR_EMAIL%" 2>nul
if exist ".git\index.lock" del /f /q ".git\index.lock" 2>nul
git add -A
REM BEZPECNOST: odstage webhosting\data\auth.json, aby se produkcni hesla nedostala do public repa
git reset HEAD -- webhosting/data/auth.json 2>nul
REM BEZPECNOST: odstage .env - nesmi nikdy leaknout token
git reset HEAD -- .env 2>nul
git commit -m "Release %TAG%" || call :info "(nic k commitnuti)"
echo.
echo   Push master (vystup se uklada do .zh_push.log pro detekci chyb)...
git push origin %GITHUB_DEFAULT_BRANCH% > .zh_push.log 2>&1
type .zh_push.log
findstr /C:"Push cannot contain secrets" /C:"GH013" /C:"unblock-secret" .zh_push.log >nul
if not errorlevel 1 goto push_secret_blocked
findstr /R /C:"! .*rejected" /C:"failed to push" .zh_push.log >nul
if not errorlevel 1 goto auto_err
del .zh_push.log 2>nul
git tag %TAG% 2>nul || call :info "(tag uz existuje lokalne)"
echo.
echo   Push tagu %TAG%...
git push origin %TAG% > .zh_push.log 2>&1
type .zh_push.log
findstr /R /C:"! .*rejected" /C:"failed to push" .zh_push.log >nul
if not errorlevel 1 goto auto_err
del .zh_push.log 2>nul
call :ok "Release pushnut. Sleduj build na:"
echo      https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions
goto pause_and_return_rescan

:push_secret_blocked
echo.
call :err "Push zablokoval GitHub Push Protection - v historii je secret (PAT)."
echo.
echo   GitHub detekoval GitHub Personal Access Token v jednom z commitu.
echo   Dve moznosti:
echo.
echo     [A] Allow-list pres GitHub UI (secret zustane v historii, ale push projde)
echo     [B] Prepsat historii pres git filter-repo (cisty - secret zmizi)
echo.
choice /c ABX /n /m "  [A]llow / [B]prepsat / [X] zrusit: "
if errorlevel 3 goto pause_and_return
if errorlevel 2 goto cleanup_secret
REM Cesta A - vytahne unblock URL z logu a otevre ji
for /f "tokens=*" %%U in ('findstr /C:"unblock-secret" .zh_push.log') do (
    set "UNBLOCK_LINE=%%U"
)
if defined UNBLOCK_LINE (
    echo.
    echo   Otevirani unblock URL v prohlizeci...
    for /f "tokens=2 delims= " %%H in ("!UNBLOCK_LINE!") do start "" "%%H"
) else (
    start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/security/secret-scanning"
)
echo.
call :warn "Na webu: vyber duvod 'Used in tests' nebo 'Revoked' a klikni Allow."
call :info "Az schvalis, spust znovu [5] Auto Release."
del .zh_push.log 2>nul
goto pause_and_return

:auto_err
echo.
if exist .zh_push.log (
    echo   Detailni vystup pushe:
    type .zh_push.log
    del .zh_push.log 2>nul
)
call :err "Git push selhal. Zkontroluj pristup a stav."
goto pause_and_return

REM =======================================================================
REM  [6] MANUAL RELEASE
REM =======================================================================
:manual_release
call :header "[6] Manual Release (gh CLI)"
where gh >nul 2>&1
if errorlevel 1 (
    call :err "gh CLI neni v PATH. Nainstaluj z https://cli.github.com/"
    goto pause_and_return
)
if not exist "dist\ZeddiHubTools.exe" (
    call :err "dist\ZeddiHubTools.exe neexistuje. Spust [4] Build."
    goto pause_and_return
)
echo   Vytvarim release %TAG% s .exe...
gh release create %TAG% "dist\ZeddiHubTools.exe" --title "%TAG%" --generate-notes
goto pause_and_return_rescan

REM =======================================================================
REM  [7] GIT STATUS
REM =======================================================================
:git_status
call :header "[7] Git status"
echo   -- git status --
git status
echo.
echo   -- git branch -vv --
git branch -vv
echo.
echo   -- posledni commity --
git log --oneline -10 2>nul
echo.
echo   -- tagy (poslednich 10) --
git for-each-ref --count=10 --sort=-creatordate --format="%%(refname:short)  %%(creatordate:short)" refs/tags 2>nul
goto pause_and_return

REM =======================================================================
REM  [8] SMAZAT TAG
REM =======================================================================
:delete_tag
call :header "[8] Smazat tag %TAG%"
call :warn "Pouzivat POUZE pokud push selhal a potrebujete zacit znovu."
echo.
choice /c AN /n /m "  [A]no pokracovat / [N]e zrusit: "
if errorlevel 2 goto render
echo.
git tag -d %TAG% 2>nul && call :ok "Lokalni tag %TAG% smazan." || call :info "(lokalni tag neexistoval)"
if defined GITHUB_TOKEN (
    set "REMOTE_URL=https://%GITHUB_TOKEN%@github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git"
    git push "!REMOTE_URL!" --delete %TAG% 2>nul && (
        call :ok "Remote tag smazan."
    ) || (
        call :info "(remote tag neexistoval nebo chyba permissions)"
    )
) else (
    call :warn ".env nema token - remote tag smazte rucne na GitHubu."
)
goto pause_and_return_rescan

REM =======================================================================
REM  [9] OTEVRIT GITHUB
REM =======================================================================
:open_github
call :header "[9] Otevrit GitHub v prohlizeci"
echo   Otevirani stranek...
start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%"
start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/releases"
start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/actions"
call :ok "Otevreno v prohlizeci."
goto pause_and_return

REM =======================================================================
REM  [11] QUICK PUSH (bez tagu, bez verze bumpu)
REM =======================================================================
:quick_push
call :header "[11] Rychla push (quick commit)"
if exist ".git\index.lock" del /f /q ".git\index.lock" 2>nul
git add -A
git reset HEAD -- webhosting/data/auth.json 2>nul
git reset HEAD -- .env 2>nul
echo.
echo   Zmeny, ktere se commitnou:
git diff --cached --stat
echo.
set /p "QMSG=  Commit message: "
if "!QMSG!"=="" (
    call :err "Prazdna zprava - preruseno."
    goto pause_and_return
)
git commit -m "!QMSG!" || (
    call :info "(nic k commitnuti)"
    goto pause_and_return
)
echo.
echo   Push master...
git push origin %GITHUB_DEFAULT_BRANCH% > .zh_push.log 2>&1
type .zh_push.log
findstr /C:"Push cannot contain secrets" /C:"GH013" .zh_push.log >nul
if not errorlevel 1 (
    del .zh_push.log 2>nul
    call :err "Push blokovan push-protection - spust [12] Cleanup: PAT secret v historii."
    goto pause_and_return
)
findstr /R /C:"! .*rejected" /C:"failed to push" .zh_push.log >nul
if not errorlevel 1 (
    del .zh_push.log 2>nul
    call :err "Push selhal."
    goto pause_and_return
)
del .zh_push.log 2>nul
call :ok "Pushnuto."
goto pause_and_return_rescan

REM =======================================================================
REM  [12] CLEANUP: PAT SECRET V HISTORII
REM =======================================================================
:cleanup_secret
call :header "[12] Cleanup: PAT secret v historii (filter-repo)"
echo.
echo   Tato akce TRVALE prepise git historii a odstrani vsechny GitHub
echo   Personal Access Tokeny (vzory: github_pat_..., ghp_..., ghs_...).
echo.
echo   Dva mody:
echo     [A] Allow-list pres GitHub UI (nejrychlejsi, secret vsak zustava)
echo     [B] Automaticke prepsani historie pres git filter-repo (cisty)
echo     [X] Zrusit
echo.
choice /c ABX /n /m "  Volba: "
if errorlevel 3 goto pause_and_return
if errorlevel 2 goto cleanup_filter_repo

REM --- Cesta A: otevre GitHub secret-scanning stranku
echo.
echo   Otevirani GitHub Secret Scanning stranky...
start "" "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%/security/secret-scanning"
echo.
call :info "Na webu: najdi blokovany secret, klikni Allow a vyber duvod."
call :info "Typicke duvody: 'Used in tests' / 'Revoked'."
echo.
call :warn "DOPORUCENI: pred Allow zneplatni token na https://github.com/settings/tokens"
goto pause_and_return

:cleanup_filter_repo
echo.
call :warn "Toto PREPISE historii. Budes muset force-pushnout."
call :warn "Pokud je repo sdileny s jinymi lidmi, koordinuj s nimi!"
echo.
choice /c AN /n /m "  [A]no pokracovat / [N]e zrusit: "
if errorlevel 2 goto pause_and_return
echo.
echo   Kontrola git-filter-repo...
where git-filter-repo >nul 2>&1
if errorlevel 1 (
    echo   Neni nainstalovan. Instaluji pres pip...
    python -m pip install git-filter-repo
    if errorlevel 1 (
        call :err "Instalace selhala. Zkus rucne: python -m pip install git-filter-repo"
        goto pause_and_return
    )
)
echo.
echo   Vytvarim .zh_replacements.txt s token patterny...
(
    echo regex:github_pat_[A-Za-z0-9_]+==^>***REMOVED_PAT***
    echo regex:ghp_[A-Za-z0-9]+==^>***REMOVED_PAT***
    echo regex:ghs_[A-Za-z0-9]+==^>***REMOVED_PAT***
    echo regex:gho_[A-Za-z0-9]+==^>***REMOVED_PAT***
    echo regex:ghu_[A-Za-z0-9]+==^>***REMOVED_PAT***
    echo regex:ghr_[A-Za-z0-9]+==^>***REMOVED_PAT***
) > .zh_replacements.txt
echo.
echo   Spoustim git filter-repo...
git-filter-repo --replace-text .zh_replacements.txt --force
if errorlevel 1 (
    del .zh_replacements.txt 2>nul
    call :err "filter-repo selhalo. Overit: python -m git_filter_repo --help"
    goto pause_and_return
)
del .zh_replacements.txt 2>nul
echo.
call :ok "Historie prepsana. Tokeny nahrazeny ***REMOVED_PAT***."
echo.
echo   Obnovuji remote origin (filter-repo ho odstranuje)...
git remote add origin "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git" 2>nul
git remote set-url origin "https://github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git"
echo.
call :warn "Nyni musis FORCE PUSH: git push origin %GITHUB_DEFAULT_BRANCH% --force"
echo.
choice /c AN /n /m "  Provest force push HNED? [A]no / [N]e zrusit: "
if errorlevel 2 (
    call :info "Force push preskocen. Spust rucne, az budes pripraven."
    goto pause_and_return
)
echo.
git push origin %GITHUB_DEFAULT_BRANCH% --force > .zh_push.log 2>&1
type .zh_push.log
findstr /R /C:"! .*rejected" /C:"failed to push" .zh_push.log >nul
if not errorlevel 1 (
    del .zh_push.log 2>nul
    call :err "Force push selhal. Zkontroluj branch protection rules."
    goto pause_and_return
)
del .zh_push.log 2>nul
call :ok "Force push hotov. Historie na GitHubu je cista."
call :info "Nyni muzes znovu spustit [5] Auto Release pro tagovani v1.9.0."
goto pause_and_return_rescan
