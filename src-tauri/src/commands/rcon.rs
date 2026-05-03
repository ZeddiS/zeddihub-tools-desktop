//! Tauri commands wrapping `services::rcon`.

use tauri::State;
use crate::error::AppResult;
use crate::services::rcon::{self, RconState};

#[tauri::command]
pub async fn rcon_connect(
    state: State<'_, RconState>,
    host: String,
    port: u16,
    password: String,
) -> AppResult<String> {
    rcon::connect(&state, &host, port, &password).await
}

#[tauri::command]
pub async fn rcon_send(
    state: State<'_, RconState>,
    key: String,
    cmd: String,
) -> AppResult<String> {
    rcon::send(&state, &key, &cmd).await
}

#[tauri::command]
pub async fn rcon_disconnect(
    state: State<'_, RconState>,
    key: String,
) -> AppResult<()> {
    rcon::disconnect(&state, &key).await
}
