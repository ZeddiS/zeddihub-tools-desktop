//! Tauri commands wrapping `services::a2s`.

use crate::error::AppResult;
use crate::services::a2s::{self, ServerInfo};

#[tauri::command]
pub async fn a2s_query(host: String, port: u16, timeout_ms: u64) -> AppResult<ServerInfo> {
    a2s::query(&host, port, timeout_ms).await
}
