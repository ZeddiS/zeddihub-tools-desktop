// ZeddiHub Tools — Tauri 2 backend (Rust).
//
// Architektura:
//   - Frontend (HTML/CSS/JS) volá Rust funkce přes `invoke("name")`.
//   - Rust funkce mají přístup k OS, sockets, files, atd. — všechno
//     co dělala Python aplikace, jen kompilovaně a paměťově bezpečně.
//   - Tray ikona + minimize-to-tray nativně přes Tauri tray-icon plugin.
//
// Tento PoC ukazuje 2 backend funkce:
//   1. fetch_recommended()  — HTTP GET na zeddihub.eu/tools/data/recommended.json
//   2. get_system_info()    — drobná OS introspekce, demonstruje native access

use serde::{Deserialize, Serialize};
use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager,
};

// ── Data shapes (sdílené s frontendem přes JSON) ──────────────────────
#[derive(Debug, Serialize, Deserialize, Clone)]
struct RecommendedItem {
    name: String,
    desc: String,
    color: Option<String>,
    nav_id: Option<String>,
}

// ── Commands (callable z JS přes `invoke`) ────────────────────────────
#[tauri::command]
async fn fetch_recommended() -> Result<Vec<RecommendedItem>, String> {
    // Spuštěno na Tauri's async runtime — neblokuje UI thread.
    // ureq je sync, ale celý command běží v task pool, takže OK.
    let url = "https://zeddihub.eu/tools/data/recommended.json";
    let body = ureq::get(url)
        .set("User-Agent", "ZeddiHub-Tauri-PoC/0.1")
        .timeout(std::time::Duration::from_secs(6))
        .call()
        .map_err(|e| format!("HTTP error: {}", e))?
        .into_string()
        .map_err(|e| format!("Read error: {}", e))?;

    let items: Vec<RecommendedItem> = serde_json::from_str(&body)
        .map_err(|e| format!("Parse error: {}", e))?;

    Ok(items)
}

#[tauri::command]
fn get_system_info() -> Result<String, String> {
    // Drobná demonstrace native access — Rust si jednoduše sáhne na OS info.
    let os = std::env::consts::OS;
    let arch = std::env::consts::ARCH;
    let exe = std::env::current_exe()
        .map(|p| p.display().to_string())
        .unwrap_or_else(|_| "?".to_string());
    let cores = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(0);
    Ok(format!(
        "OS: {} ({}), CPU cores: {}, exe: {}",
        os, arch, cores, exe
    ))
}

// ── Tauri app entrypoint ──────────────────────────────────────────────
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Tray ikona s menu — nativní integrace, žádný pystray hack.
            let open_i = MenuItem::with_id(app, "open", "Otevřít", true, None::<&str>)?;
            let home_i = MenuItem::with_id(app, "home", "Domů", true, None::<&str>)?;
            let settings_i =
                MenuItem::with_id(app, "settings", "Nastavení", true, None::<&str>)?;
            let quit_i = MenuItem::with_id(app, "quit", "Ukončit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&open_i, &home_i, &settings_i, &quit_i])?;

            let _tray = TrayIconBuilder::new()
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "open" | "home" | "settings" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                            // V plné aplikaci by se „home"/„settings" propagovaly
                            // přes Tauri event bus (`app.emit("navigate", id)`),
                            // frontend by listen-oval. Pro PoC stačí restore.
                        }
                    }
                    "quit" => {
                        app.exit(0);
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    use tauri::tray::TrayIconEvent;
                    if let TrayIconEvent::Click { button, .. } = event {
                        if matches!(button, tauri::tray::MouseButton::Left) {
                            if let Some(w) = tray.app_handle().get_webview_window("main") {
                                let _ = w.show();
                                let _ = w.set_focus();
                            }
                        }
                    }
                })
                .build(app)?;

            // Minimize to tray on close: skryj okno místo ukončení.
            // Žádný "černý obdélník" bug — WebView2 zachová DOM render state
            // přes hide()/show() spolehlivě. To je výhoda web tech vrstvy.
            if let Some(window) = app.get_webview_window("main") {
                let win_clone = window.clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = win_clone.hide();
                    }
                });
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            fetch_recommended,
            get_system_info
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
