//! Tauri commands wrapping `services::net_tools`.

use crate::error::AppResult;
use crate::services::net_tools;

#[tauri::command]
pub async fn net_dns_lookup(domain: String, record_type: String) -> AppResult<Vec<String>> {
    net_tools::dns_lookup(&domain, &record_type).await
}

#[tauri::command]
pub async fn net_port_check(host: String, port: u16, timeout_ms: u64) -> AppResult<bool> {
    net_tools::port_check(&host, port, timeout_ms).await
}
