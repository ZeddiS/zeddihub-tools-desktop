//! Tauri commands wrapping `services::rust_rcon`.

use tauri::State;
use crate::error::AppResult;
use crate::services::rust_rcon::{self, RustRconState};

#[tauri::command]
pub async fn rust_rcon_connect(
    state: State<'_, RustRconState>,
    host: String,
    port: u16,
    password: String,
) -> AppResult<String> {
    rust_rcon::connect(&state, &host, port, &password).await
}

#[tauri::command]
pub async fn rust_rcon_send(
    state: State<'_, RustRconState>,
    key: String,
    cmd: String,
) -> AppResult<()> {
    rust_rcon::send(&state, &key, &cmd).await
}

#[tauri::command]
pub async fn rust_rcon_recv(
    state: State<'_, RustRconState>,
    key: String,
) -> AppResult<Vec<String>> {
    rust_rcon::recv(&state, &key).await
}

#[tauri::command]
pub async fn rust_rcon_disconnect(
    state: State<'_, RustRconState>,
    key: String,
) -> AppResult<()> {
    rust_rcon::disconnect(&state, &key).await
}
