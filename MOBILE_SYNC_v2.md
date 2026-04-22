# ZeddiHub — cross-platform sync handoff (mobile ⇄ desktop)

> **Cíl dokumentu:** sjednotit mobilní (Android) a desktop (Windows) klienty
> ZeddiHub Tools tak, aby sdíleli **jeden backend, jeden uživatelský účet,
> jednu session, jedny texty chyb a jeden verzovací mechanismus**.
>
> **Čti jako druhý Claude chat v mobilním repozitáři.** Desktop už je na v1.7.4
> kompletně přepsán podle REST kontraktu z `zeddihub_tools_mobile/website/api/
> auth/CONTRACT.md`. Tento soubor popisuje **to, co desktop reálně dělá**, aby
> mobilní strana mohla zrcadlit stejné chování 1 : 1.
>
> Vygenerováno: 2026-04-21, desktop v1.7.4. Pokud se dokument liší od
> zdrojového kódu (`zeddihub_tools_desktop/gui/api_auth.py` + `gui/auth.py`),
> **zdrojový kód má přednost**.

---

## 0. TL;DR — 10-řádkový shrnutí

1. Jeden `/api/auth/*` endpoint na `https://zeddihub.eu/api/auth/` (PHP + SQLite).
2. Shared `X-App-Secret = 696d63c65a8536637183028e4eecb841cd5b679ce7b2d33c6ef2d4054166e438` – **nerotovat bez koordinace.**
3. Každý klient posílá trojici `X-App-Secret`, `X-Client-Kind`, `X-Client-Version` na **každý** request.
4. `/register` vrací sessionový token okamžitě – uživatel je přihlášen bez druhého kola.
5. `/login` přijímá `identifier` (buď username nebo email). Backwards-compat `username` / `email` aliasy zůstávají.
6. Token je opákní 40-hex string, `auth_tokens` řádek per device. **/logout odhlásí jen toto zařízení.**
7. Expiry slides forward o `ZH_TOKEN_TTL_SECONDS` (180 dní) při každém `/me`.
8. Error-key taxonomie je **zafixovaná** — mobilní strings.xml mapování musí být shodné s desktop `_ERROR_CS` dict (viz §4).
9. Version JSON: desktop čte `/tools/data/version.json`, mobile má mít vlastní `version_android.json` ve stejné složce.
10. Web repo je samostatný: `zeddihub-tools-website` – **veškerý web content tam**, desktop/mobile ho jen konzumují.

---

## 1. Architektura tří repozitářů

```
┌────────────────────────────────┐     ┌────────────────────────────────┐
│  zeddihub_tools_desktop        │     │  zeddihub_tools_mobile         │
│  (Python + customtkinter, v1.7.4) │     │  (Kotlin + Compose)            │
│                                │     │                                │
│  gui/api_auth.py ──────┐       │     │  data/api/AuthApi.kt ───┐      │
│  gui/auth.py           │       │     │  data/AuthRepository.kt │      │
└────────────────────────┼───────┘     └──────────────────────────┼────┘
                         │                                         │
                         │  HTTPS (Bearer + X-App-Secret)          │
                         │                                         │
                         └──────────────┬──────────────────────────┘
                                        ▼
                  ┌──────────────────────────────────────┐
                  │  zeddihub-tools-website              │
                  │  (deployed to zeddihub.eu)           │
                  │                                      │
                  │  /api/auth/   ← REST auth (SQLite)   │
                  │  /api/wifi-map/ ← Wi-Fi map CRUD     │
                  │  /api/_config.php ← APP_SECRET etc.  │
                  │  /tools/admin/ ← PHP admin panel     │
                  │  /tools/data/  ← static JSON feeds   │
                  │  /games/        ← (prázdné, zatím)   │
                  └──────────────────────────────────────┘
```

**Klíčový invariant:** žádný z klientů už **nesmí** obsahovat lokální kopii
webhostingu. Desktop `webhosting/` junction byl odstraněn v v1.7.4. Mobile
repozitář by měl stejně — `mobile/website/` adresář v `zeddihub_tools_mobile`
ponechte jako historický zdroj, ale **autoritativní kopie je teď v
`zeddihub-tools-website`**. Jakékoli PHP edity posílejte tam.

---

## 2. Přesný REST kontrakt — co desktop **reálně** posílá a očekává

Plný kontrakt: `zeddihub-tools-website/api/auth/CONTRACT.md`. Následující je
snapshot toho, co desktop **implementuje** v `gui/api_auth.py` + `gui/auth.py`.

### 2.1 Base URL + headers (každý request)

```
POST/GET https://zeddihub.eu/api/auth/<endpoint>
Headers:
  User-Agent:         ZeddiHubTools/<APP_VERSION> (desktop)  ← mobile: ZeddiHubTools/<VERSION> (mobile)
  Accept:             application/json
  X-App-Secret:       696d63c65a8536637183028e4eecb841cd5b679ce7b2d33c6ef2d4054166e438
  X-Client-Kind:      desktop                                ← mobile: mobile
  X-Client-Version:   1.7.4                                   ← mobile: BuildConfig.VERSION_NAME
  Authorization:      Bearer <token>                          ← jen pro /me, /logout, /admin_reset
  Content-Type:       application/json                        ← jen u POST s tělem
```

Mobilní OkHttp interceptor **musí** doplňovat tyto headery automaticky,
stejně jak to dělá desktop na Python-urllib úrovni.

### 2.2 Endpointy (přesný wire protocol)

| Endpoint | Metoda | Payload | Success | Key errors |
|---|---|---|---|---|
| `/register` | POST | `{username, email, password}` | `{ok:true, user, token, expires_at}` | `invalid_username`, `invalid_email`, `invalid_password`, `taken`, `too_fast`, `daily_limit` |
| `/login` | POST | `{identifier, password}` | `{ok:true, user, token, expires_at}` | `missing_identifier`, `missing_password`, `bad_credentials`, `disabled`, `too_fast`, `too_many_fails` |
| `/me` | GET | — (jen `Authorization`) | `{ok:true, user, expires_at}` | `auth_required`, `auth_invalid` |
| `/logout` | POST | — | `{ok:true}` (**vždy**, idempotent) | — |
| `/admin_reset` | POST | `{target_username OR target_email, new_password, revoke_all?}` | `{ok:true, target_id, target_username, revoked_tokens}` | `forbidden`, `not_found` |

Desktop považuje **cokoli s `{ok:false}`** za `ApiError(error_key, message,
status)`. Mobile by měl mít analogický sealed class:

```kotlin
sealed class AuthError(val key: String, val message: String, val httpStatus: Int) {
    // např. BadCredentials(message, 401), Taken(message, 409), ...
}
```

### 2.3 User DTO (to, co backend reálně vrací)

```json
{
  "id": 1,
  "username": "zeddi",
  "email": "a@b.cz",
  "role": "user",           // "user" | "premium" | "admin" (case-insensitive)
  "is_admin": false
}
```

Kotlin data class:

```kotlin
@JsonClass(generateAdapter = true)
data class UserDto(
    val id: Long,
    val username: String,
    val email: String,
    val role: String = "user",
    @Json(name = "is_admin") val isAdmin: Boolean = false,
)
```

**Pozor:** desktop odvozuje `current_role` jako `"admin"` pokud `is_admin == true`
**NEBO** `role.lower() == "admin"`. Mobile by měl udělat totéž — `is_admin`
flag je z UX pohledu zdroj pravdy, `role` string je jen label.

---

## 3. Session persistence — co musí mobile zrcadlit

Desktop uchovává v **Fernet-šifrovaném `auth.enc`** v user data dir tento JSON:

```json
{
  "username": "zeddi",
  "password": "…",      // volitelné — slouží k re-loginu po expiraci tokenu
  "token": "a1b2c3…",   // 40 hex, REST session token
  "expires_at": 1712345678
}
```

**Proč i heslo?** Pokud uživatel aplikaci neotevře >180 dnů, token zmrtví.
Desktop pak volá `/login` s uloženým heslem a obnoví session bez toho, aby
uživatel musel znovu ručně zadávat údaje. Mobile má dvě možnosti:

- **(A) Stejná strategie** — uložit password do `EncryptedSharedPreferences`
  (AES-256-GCM, Android Keystore). Jednoduché, ale heslo žije v plaintextu
  po dešifrování v RAM.
- **(B) Jen token** — uživatel po 180 dnech přihlášení znovu. Bezpečnější,
  horší UX. **Pokud zvolíš tuto cestu, přizpůsob i desktop**, ať je chování
  konzistentní.

Desktop používá **(A)**. Doporučuji mobile taky (A) kvůli UX parity.

### 3.1 Startup sekvence (desktop → mirror na mobile)

```
launchApp()
  ├── loadEncryptedSession()         // auth.enc / EncryptedSharedPreferences
  ├── if session.token exists:
  │     GET /me → 200 { user, expires_at }
  │       → populate in-memory state, slide expires_at forward, persist
  │     → 401 auth_invalid + saved.password:
  │       POST /login { identifier: username, password }
  │       → re-populate + persist
  │     → network error:
  │       if expires_at > now: use cached user offline
  │       else: prompt login
  └── else: prompt login
```

Desktop implementace: `gui/auth.py::resume_session()`. Volá se z hlavního okna
při startu (`MainWindow.__init__`).

### 3.2 Logout

Desktop `logout()`:
1. Pošle `POST /logout` s aktuálním tokenem (best-effort — chyby ignoruje).
2. Vynuluje in-memory session state.
3. **Nemaže `auth.enc`** — to je separátní akce (`clear_credentials()`),
   typicky voláno z tlačítka „Zapomenout mé přihlašovací údaje" v Settings.

Mobile by měl rozlišovat stejně:
- `AuthRepository.logout()` → API call + clear in-memory.
- `AuthRepository.forgetCredentials()` → smaže encrypted store.

---

## 4. Error-key mapping — **shodný textový výstup na obou platformách**

Desktop má v `gui/auth.py::_ERROR_CS` hotové české překlady error-keys.
Zkopíruj je 1 : 1 do mobilu (string resource `strings.xml`):

```xml
<!-- res/values-cs/strings.xml -->
<string name="err_invalid_username">Neplatné uživatelské jméno.</string>
<string name="err_invalid_email">Neplatný email.</string>
<string name="err_invalid_password">Neplatné heslo (min. 8 znaků).</string>
<string name="err_captcha_required">Chybí captcha token (interní chyba klienta).</string>
<string name="err_captcha_failed">Captcha se nepodařilo ověřit.</string>
<string name="err_taken">Uživatelské jméno nebo email už někdo používá.</string>
<string name="err_bad_credentials">Nesprávné přihlašovací údaje.</string>
<string name="err_disabled">Účet je zablokovaný. Kontaktujte administrátora.</string>
<string name="err_too_fast">Moc rychle. Zkuste to znovu za chvíli.</string>
<string name="err_too_many_fails">Příliš mnoho neúspěšných pokusů. Zkuste později.</string>
<string name="err_daily_limit">Dosáhli jste denního limitu registrací.</string>
<string name="err_auth_required">Přihlášení vypršelo, přihlaste se znovu.</string>
<string name="err_auth_invalid">Session vypršela, přihlaste se znovu.</string>
<string name="err_forbidden">Nemáte oprávnění.</string>
<string name="err_not_found">Uživatel nenalezen.</string>
<string name="err_server_error">Chyba serveru, zkuste později.</string>
<string name="err_missing_identifier">Zadejte uživatelské jméno nebo email.</string>
<string name="err_missing_password">Zadejte heslo.</string>
```

Pro `values-en/strings.xml` by stačilo převzít `message` field z API (server
posílá český text defaultně, ale error-key je locale-agnostický — lokalizaci
dělá klient z mapování výše).

**Fallback pravidlo:** pokud error-key není v mapě, zobraz server `message`.
Pokud i `message` je prázdné, zobraz `"Chyba: <error_key>"`.

---

## 5. Fallback strategie — jak desktop volí REST vs. legacy

Jen pro referenci, ať mobile rozhoduje konzistentně:

| Situace | Desktop chování | Doporučení pro mobile |
|---|---|---|
| REST login → `bad_credentials` | **Fail fast.** Neskáče na legacy. UI ukáže chybu. | Same — uživatel zadal špatně, legacy fallback by mate. |
| REST login → `NetworkError` (DNS, timeout, TLS) | Spadne na `GET /tools/data/auth.json` (statický whitelist) | Mobile **může vynechat** legacy JSON — Android má mnohem lepší offline state management. Pokud ho implementuješ, použij stejný URL. |
| REST `/me` → `auth_invalid` + saved password | Tiše zkusí `/login` a obnoví session | Same — transparentně pro uživatele. |
| REST `/me` → network error + cached `expires_at > now` | Pustí uživatele offline s cached user DTO | Same — umožní otevřít Player DB, apod. |

Legacy `auth.json` na `/tools/data/auth.json` je **deprekovaný od v1.7.4**, ale
stále hostovaný pro staré desktop buildy < v1.7.4. Neplánuj write operace —
je to read-only seznam.

---

## 6. Rate limiting — co si mobile musí hlídat

Server konfiguruje v `api/_config.php`:

| Konstanta | Hodnota | Dopad na klient |
|---|---|---|
| `ZH_LOGIN_COOLDOWN_SECONDS` | 2 | Nedávat rychlé double-tap na tlačítko „Přihlásit" |
| `ZH_LOGIN_MAX_FAILS_PER_HOUR` | 10 | Po 10 fails IP banned na hodinu — mobile ukáže hint „Zkus za chvíli" |
| `ZH_REGISTER_COOLDOWN_SECONDS` | 30 | Po úspěšné registraci z téže IP čekej min. 30 s |
| `ZH_REGISTER_MAX_PER_DAY` | 5 | Pokud testuješ v emulátoru, můžeš narazit — server hashuje IP, ne device ID |

Desktop nevykonává žádné klientské rate-limit hlídání — spoléhá na server.
Mobile to **doporučujeme stejně**, ale můžete disablovat register tlačítko
po úspěchu na 30s lokálně jako UX gesto.

---

## 7. Version model + update check — **jedna změna, dvě platformy**

### 7.1 Desktop

- Single source of truth: `zeddihub_tools_desktop/gui/version.py::APP_VERSION`.
- Mirror: `zeddihub-tools-website/tools/data/version.json` + `version.json` v rootu desktop repa.
- Update check: GitHub Releases API (`ZeddiS/zeddihub-tools-desktop`).

### 7.2 Mobile — doporučený model

- Single source: `BuildConfig.VERSION_NAME` (Gradle).
- Mirror: **`zeddihub-tools-website/tools/data/version_android.json`**
  (ještě neexistuje — první mobile release ho vytvoří).
- Update check: dvoufázově
  1. Zkus `https://zeddihub.eu/tools/data/version_android.json` → if
     `version > BuildConfig.VERSION_NAME`, zobraz prompt s `download_url`.
  2. `download_url` nasměruj buď na Play Store listing, nebo na přímé APK
     (pokud distribuce je side-load).

### 7.3 Formát obou version.json souborů

```json
{
  "version": "1.7.4",
  "release_date": "2026-04-21",
  "changelog": "…stručný český popis novinek…",
  "mandatory": false,
  "download_url": "https://github.com/…/ZeddiHubTools.exe"
}
```

Mobile version.json by měl dodržet **stejná pole**. `mandatory: true` může
spustit blokující dialog.

### 7.4 Version compatibility matrix

| Desktop | Mobile | Backend | Poznámka |
|---|---|---|---|
| ≥ 1.7.4 | jakákoli s `X-App-Secret` | `/api/auth/*` (SQLite) | Sjednocené účty. |
| < 1.7.4 | — | `/tools/data/auth.json` | Read-only, deprekované. |
| — | jakákoli | `/api/auth/*` | Mobile mohl používat `/api/auth/*` už před desktop v1.7.4. |

Rotace `ZH_APP_SECRET` vyřadí **všechny klienty < revize secretu** (dostanou
`captcha_required` na register/login). **Před rotací:**
1. Bump desktop + mobile verze, zapiš nový secret.
2. Vydej nové buildy obou klientů.
3. Teprve pak změň secret na serveru.

---

## 8. Konkrétní TODO checklist pro mobilní chat

Následující úkoly jsou pro nového Claude v mobilním repozitáři. Každý bod
by měl být měřitelný — buď PR, nebo rozhodnutí „wontfix + důvod".

- [ ] **M1.** Porovnat `data/api/AuthApi.kt` s `desktop/gui/api_auth.py`. Doplnit chybějící metody (`adminReset` pokud nemá), sjednotit jména polí.
- [ ] **M2.** Zavést sealed class `AuthError` s jedním case per error-key z §2.2. Doplnit `strings.xml` z §4.
- [ ] **M3.** Ověřit že OkHttp interceptor posílá `X-App-Secret`, `X-Client-Kind: mobile`, `X-Client-Version` na **každý** request (vč. Wi-Fi map).
- [ ] **M4.** Implementovat `AuthRepository.resumeSession()` přesně podle §3.1 (volá `/me`, fallback na `/login`, offline grace period).
- [ ] **M5.** Rozhodnout strategii A/B z §3 (desktop používá A). Zapsat rozhodnutí do mobile README.
- [ ] **M6.** Založit `zeddihub-tools-website/tools/data/version_android.json` (přes PR do website repa). Implementovat update check podle §7.2.
- [ ] **M7.** Smazat / archivovat `zeddihub_tools_mobile/website/` — **autoritativní kopie je teď v `zeddihub-tools-website`**. Každá budoucí PHP změna jde tam.
- [ ] **M8.** Zkontrolovat že registration UI má stejnou validaci jako desktop: username `[A-Za-z0-9_.\-]{3,24}`, password 8–128 znaků, email regex. **Client-side validace musí matchnout server**, jinak bude UX nekonzistentní.
- [ ] **M9.** Přidat `/logout` call při odhlášení (ne jen smazat local token). Desktop dělá best-effort POST a ignoruje chyby.
- [ ] **M10.** Ověřit token lifecycle test: nová registrace → `/me` po 1 s → zavřít appku → znovu otevřít po 5 s → session pokračuje. Pak stejný test s 200denní pauzou (force-setnout `expires_at` do minulosti přes admin panel) → klient by měl tiše re-loginit pomocí uloženého hesla.

---

## 9. Shared design decisions (už padlo, nevracet se k tomu)

Tyto body jsou **uzavřené** — mobilní chat je bere jako daná fakta:

1. **APP_SECRET je sdílený** mezi mobile a desktop. Stejná hodnota.
   Rotace = koordinovaný release všech klientů.
2. **Admin panel zůstává PHP** (v `zeddihub-tools-website/tools/admin/`). Žádná
   mobilní varianta admin UI se neplánuje — admin flow je webový.
3. **Player DB (lokální SQLite per-uživatel)** zůstává v obou appkách
   lokální. **Nesdílí se přes server** — každý klient má vlastní, session
   tokeny se nepřenášejí. Pokud chceš cross-device sync, vyžaduje to nový
   `/api/players/*` endpoint — otevřený, nenaplánovaný.
4. **Telemetry endpoint**: `https://zeddihub.eu/tools/telemetry.php` (ten
   samý pro obě appky). `X-Client-Kind` rozlišuje origin.
5. **Wi-Fi map**: `/api/wifi-map/list` + `/api/wifi-map/submit`. Zatím jen
   mobile používá. Desktop nemá důvod zasahovat — nech implementaci mobilu.
6. **hCaptcha se neposílá** z native klientů — výhradně web. Native klient
   posílá `X-App-Secret` a tím captcha kompletně přeskakuje.
7. **Session token je per-device.** Login z mobilu neodhlásí desktop a vice
   versa. Admin může revokovat všechny tokeny přes `/admin_reset?revoke_all=true`.

---

## 10. Otevřené otázky → nutno rozhodnout mezi oběma stranami

Zapiš k těmto bodům odpovědi — pak je společně promazej.

| Otázka | Desktop pozice | Mobile pozice? |
|---|---|---|
| Mají se **telemetry events** sjednotit (stejný event name-space)? | Ano — `event = "panel_open" / "login" / "launch" / "export"` | ? |
| Má mít mobile **tray_tools** equivalent? | N/A — Android notification channels? | ? |
| Má mobile přebrat **desktop theme system** (cs2 / csgo / rust / default)? | Desktop ano — Material 3 schémata | ? |
| **Module download** (desktop má `admin_apps.json` katalog) — má mít mobile taky? | Otevřené — mobilní appky typicky nestahují pluginy | ? |
| Register z mobilu → **auto-login na desktop**? Cross-device session "magic link"? | Technicky možné (admin_reset endpoint), ale UX-složité | ? |

---

## 11. Jak otestovat mobile build proti produkčnímu backendu

Zdrojový kód endpointů: `zeddihub-tools-website/api/auth/*.php`.
Production URL: `https://zeddihub.eu/api/auth/…` (existuje od mobile v0.x).

Smoke test curl (funguje i z mobile CI):

```bash
# Register
curl -X POST https://zeddihub.eu/api/auth/register \
  -H "Content-Type: application/json" \
  -H "X-App-Secret: 696d63c65a8536637183028e4eecb841cd5b679ce7b2d33c6ef2d4054166e438" \
  -H "X-Client-Kind: mobile" \
  -H "X-Client-Version: 0.5.0-smoketest" \
  -d '{"username":"zh_test_$(date +%s)","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST https://zeddihub.eu/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-App-Secret: 696…" \
  -H "X-Client-Kind: mobile" \
  -H "X-Client-Version: 0.5.0-smoketest" \
  -d '{"identifier":"zh_test_…","password":"testpass123"}'

# /me s vráceným tokenem
curl https://zeddihub.eu/api/auth/me \
  -H "Authorization: Bearer <token>" \
  -H "X-App-Secret: 696…" \
  -H "X-Client-Kind: mobile" \
  -H "X-Client-Version: 0.5.0-smoketest"
```

Pokud curl vrátí `{ok:true, user:{…}, token:"40hex", expires_at:…}`, vše
funguje a mobile může reprodukovat přesně tentýž flow přes Retrofit.

---

## 12. Kanonické zdroje pravdy — kam koukat když se něco liší

| Téma | Zdroj pravdy | Cesta |
|---|---|---|
| REST kontrakt | `CONTRACT.md` | `zeddihub-tools-website/api/auth/CONTRACT.md` |
| PHP implementace | `*.php` v `api/auth/` | `zeddihub-tools-website/api/auth/` |
| Shared secrets | `_config.php` | `zeddihub-tools-website/api/_config.php` |
| Policy konstanty (length limits, rate limits) | `_config.php` | tamtéž, §6 |
| Desktop klient — low-level | `gui/api_auth.py` | `zeddihub_tools_desktop/gui/api_auth.py` |
| Desktop klient — session management | `gui/auth.py` | `zeddihub_tools_desktop/gui/auth.py` |
| Mobile klient — low-level | `data/api/AuthApi.kt` | `zeddihub_tools_mobile/app/src/main/java/.../` |
| Error strings (CZ) | `_ERROR_CS` dict | `zeddihub_tools_desktop/gui/auth.py` (zdroj pro `strings.xml`) |

Pokud CONTRACT.md řekne A a PHP implementace řekne B, **PHP vyhrává**
(protože ho reálně volají klienti). Opravte CONTRACT.md.

Pokud desktop klient a mobile klient se liší v interpretaci response, **server
JSON wire format vyhrává**. Opravte klient, který má chybu.

---

## 13. Mini-FAQ pro mobilní chat

**Q: Můžu změnit error-key taxonomii?**
A: Ne. Error-keys jsou stable API. Pokud potřebuješ nový error, přidej
nový key (např. `too_long_username`) — server musí být bumpán paralelně.

**Q: Můžu přidat nový HTTP header?**
A: Ano, ale sjednoť s desktopem. Nejdřív napiš do tohoto dokumentu jako
„navrhovaný header" a vyřeš přes pull request do desktop a website repa.

**Q: Mohu změnit endpoint path?**
A: **Ne** v rámci v1.x. Break přes `/api/v2/auth/…` a publikuj migrace.

**Q: Co dělá `X-App-Secret` pokud je špatný?**
A: Server dostane request jako kdyby klient byl web — `captcha_token` se
stane povinný. Pokud není, vrátí `captcha_required`. **To je signál že
klient má stale APP_SECRET a vyžaduje update.**

**Q: Server vrací neznámý error-key, co s tím?**
A: Fallback na `message` field, pokud je neprázdný; jinak `"Chyba: <key>"`.
Přidej key do `_ERROR_CS` mapy + `strings.xml` v další release.

**Q: Jak synchronizovat version bump mezi mobile a desktop?**
A: Nemusíš. Verze jsou nezávislé (desktop 1.7.4, mobile může být 0.5.2).
Jen **APP_SECRET rotace** vyžaduje koordinaci.

---

## 14. Kontakty pro koordinaci

- **Desktop repo:** `C:\Users\12voj\Documents\zeddihub_tools_desktop`
- **Mobile repo:** `C:\Users\12voj\Documents\zeddihub_tools_mobile`
- **Website repo:** `C:\Users\12voj\Documents\zeddihub-tools-website`
- **Production URL:** `https://zeddihub.eu/api/` + `https://zeddihub.eu/tools/`
- **Admin panel:** `https://zeddihub.eu/tools/admin/`
- **Owner:** ZeddiS (GitHub: `ZeddiS`)

---

## 15. Prompt-template pro prvního nového Claude v mobilním chatu

> „Přečti si `MOBILE_SYNC_v2.md` v kořeni mobilního repa. Potom zkontroluj,
> které z TODO bodů v §8 (M1–M10) ještě nejsou hotové. Začni M1 — porovnej
> `data/api/AuthApi.kt` s desktop referencí v §2.2 a napiš diff. Neimplementuj
> nic bez potvrzení. Ptej se klikatelnými otázkami."

---

*Soubor vygenerován: 2026-04-21 pro pár desktop v1.7.4 ⇄ mobile v?.?*
*Autor: Claude (Anthropic) na základě reálného zdrojáku `gui/api_auth.py`,
`gui/auth.py` a `zeddihub-tools-website/api/auth/*.php`.*
