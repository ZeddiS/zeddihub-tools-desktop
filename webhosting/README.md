# ZeddiHub Tools – Webhosting soubory

## Struktura

```
webhosting/
  admin/
    index.php   ← Admin panel (nahrát na hosting)
    style.css   ← CSS pro admin panel
    .htaccess   ← Bezpečnostní nastavení
  data/
    auth.json           ← Uživatelé a přístupové kódy
    recommended.json    ← Doporučené nástroje (domovská stránka app)
    tray_tools.json     ← Nástroje v systémové liště app
    servers.json        ← Herní servery (domovská stránka app)
    version.json        ← Informace o verzi (záloha)
    .htaccess           ← Zakazuje spuštění PHP v data/
```

## Jak nahrát na hosting

1. Nahraj složku `admin/` na svůj webhosting (např. `zeddihub.eu/admin/`)
2. Nahraj složku `data/` na `zeddihub.eu/data/` nebo do `files.zeddihub.eu/tools/`
3. Uprav cesty v `admin/index.php` (konstanta `DATA_DIR`) pokud se struktura liší
4. **Změň heslo admina** v `data/auth.json`!

## URL adresy v desktop aplikaci

Aplikace čte z těchto URL (nastav v `gui/updater.py`, `gui/tray.py`, `gui/panels/home.py`):
- `https://files.zeddihub.eu/tools/auth.json`
- `https://files.zeddihub.eu/tools/recommended.json`
- `https://files.zeddihub.eu/tools/tray_tools.json`
- `https://files.zeddihub.eu/tools/servers.json`

## Požadavky hostingu

- PHP 7.4+ (pro admin panel)
- Práva zápisu do složky `data/` pro PHP proces
- HTTPS (doporučeno — auth.json obsahuje hesla)
