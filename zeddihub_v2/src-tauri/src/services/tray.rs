//! System tray icon — minimal version, mirrors v1.7.x pystray behaviour:
//! left-click restore, right-click menu (Open / Settings / Quit).

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager,
};

use crate::error::AppResult;

pub fn install(app: &AppHandle) -> AppResult<()> {
    let open_i = MenuItem::with_id(app, "open",     "Otevřít",   true, None::<&str>)
        .map_err(|e| crate::error::AppError::Generic(e.to_string()))?;
    let settings_i = MenuItem::with_id(app, "settings", "Nastavení", true, None::<&str>)
        .map_err(|e| crate::error::AppError::Generic(e.to_string()))?;
    let quit_i = MenuItem::with_id(app, "quit",     "Ukončit",   true, None::<&str>)
        .map_err(|e| crate::error::AppError::Generic(e.to_string()))?;
    let menu = Menu::with_items(app, &[&open_i, &settings_i, &quit_i])
        .map_err(|e| crate::error::AppError::Generic(e.to_string()))?;

    TrayIconBuilder::new()
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "open" => {
                if let Some(w) = app.get_webview_window("main") {
                    let _ = w.show();
                    let _ = w.set_focus();
                }
            }
            "settings" => {
                if let Some(w) = app.get_webview_window("main") {
                    let _ = w.show();
                    let _ = w.set_focus();
                    // Browser-side router: emit event, frontend listens and goto's.
                    let _ = app.emit("zh:navigate", "/settings");
                }
            }
            "quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click { button, .. } = event {
                if matches!(button, MouseButton::Left) {
                    if let Some(w) = tray.app_handle().get_webview_window("main") {
                        let _ = w.show();
                        let _ = w.set_focus();
                    }
                }
            }
        })
        .build(app)
        .map_err(|e| crate::error::AppError::Generic(e.to_string()))?;

    Ok(())
}
