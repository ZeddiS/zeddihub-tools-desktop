//! Tauri commands — thin wrappers around `services::http_cache`.

use tauri::State;
use crate::error::AppResult;
use crate::services::http_cache::HttpCache;

#[tauri::command]
pub async fn http_fetch_json(
    state: State<'_, HttpCache>,
    url: String,
    ttl_seconds: u64,
    force_refresh: bool,
) -> AppResult<serde_json::Value> {
    state.fetch_json(&url, ttl_seconds, force_refresh).await
}

#[tauri::command]
pub async fn http_cache_age(
    state: State<'_, HttpCache>,
    url: String,
) -> AppResult<Option<u64>> {
    Ok(state.age_seconds(&url).await)
}

#[tauri::command]
pub async fn http_invalidate(
    state: State<'_, HttpCache>,
    url: String,
) -> AppResult<()> {
    state.invalidate(&url).await;
    Ok(())
}
