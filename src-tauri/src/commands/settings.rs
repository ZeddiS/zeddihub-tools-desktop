//! Tauri commands wrapping `services::settings`.

use crate::error::AppResult;
use crate::services::settings::{self, Settings};

#[tauri::command]
pub async fn settings_load() -> AppResult<Settings> {
    settings::load().await
}

#[tauri::command]
pub async fn settings_save(settings: Settings) -> AppResult<()> {
    settings::save(&settings).await
}

#[tauri::command]
pub async fn settings_data_dir() -> AppResult<String> {
    settings::data_dir_string().await
}

#[tauri::command]
pub async fn settings_factory_reset() -> AppResult<usize> {
    settings::factory_reset().await
}

#[tauri::command]
pub async fn settings_mark_first_launch_done() -> AppResult<()> {
    settings::mark_first_launch_done().await
}
