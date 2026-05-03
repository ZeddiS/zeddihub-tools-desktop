//! ZeddiHub Tools — Tauri entry point.
//!
//! Wires:
//!   - State: `HttpCache` + `AuthState` (shared across commands)
//!   - Plugins: shell, dialog, fs
//!   - Tray icon (left-click restore, right-click menu)
//!   - Window event: minimize-to-tray on close
//!   - All registered #[tauri::command] handlers

pub mod error;
pub mod commands;
pub mod services;

use tauri::Manager;

use crate::services::auth::AuthState;
use crate::services::http_cache::HttpCache;
use crate::services::rcon::RconState;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .manage(HttpCache::new())
        .manage(AuthState::new())
        .manage(RconState::new())
        .setup(|app| {
            // Tray
            services::tray::install(app.handle())?;

            // Minimize-to-tray on close
            if let Some(window) = app.get_webview_window("main") {
                let win = window.clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = win.hide();
                    }
                });
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // auth
            commands::auth::auth_login,
            commands::auth::auth_register,
            commands::auth::auth_me,
            commands::auth::auth_logout,
            // http
            commands::http::http_fetch_json,
            commands::http::http_cache_age,
            commands::http::http_invalidate,
            // system
            commands::system::system_info,
            // net tools
            commands::net_tools::net_dns_lookup,
            commands::net_tools::net_port_check,
            // settings
            commands::settings::settings_load,
            commands::settings::settings_save,
            commands::settings::settings_data_dir,
            commands::settings::settings_factory_reset,
            commands::settings::settings_mark_first_launch_done,
            // rcon
            commands::rcon::rcon_connect,
            commands::rcon::rcon_send,
            commands::rcon::rcon_disconnect,
        ])
        .run(tauri::generate_context!())
        .expect("Tauri app failed to start");
}
