//! Tauri commands — thin wrappers around `services::auth`.

use tauri::State;
use crate::error::AppResult;
use crate::services::auth::{AuthState, UserDto, UserSession};

#[tauri::command]
pub async fn auth_login(
    state: State<'_, AuthState>,
    identifier: String,
    password: String,
) -> AppResult<UserSession> {
    state.login(&identifier, &password).await
}

#[tauri::command]
pub async fn auth_register(
    state: State<'_, AuthState>,
    username: String,
    email: String,
    password: String,
) -> AppResult<UserSession> {
    state.register(&username, &email, &password).await
}

#[tauri::command]
pub async fn auth_me(state: State<'_, AuthState>) -> AppResult<UserDto> {
    state.me().await
}

#[tauri::command]
pub async fn auth_logout(state: State<'_, AuthState>) -> AppResult<()> {
    state.logout().await
}
