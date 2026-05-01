//! User settings persistence.
//!
//! Stored in `<data_dir>/settings.json` as plain JSON. Reactive front-end
//! store loads on startup, mutations propagate via auth_save command.
//!
//! Schema:
//! ```json
//! {
//!   "lang": "cs",
//!   "appearance": "dark",
//!   "close_behavior": "minimize",     // minimize | quit
//!   "telemetry_enabled": true,
//!   "auto_update_enabled": true,
//!   "first_launch_done": true,
//!   "sidebar_sections": { "cs2": false, "rust": true, ... },
//!   "data_dir": "C:\\Users\\...\\Documents\\ZeddiHub.Tools.Data"  // optional override
//! }
//! ```

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use tokio::fs;

use crate::error::{AppError, AppResult};
use crate::services::paths;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    #[serde(default = "default_lang")]
    pub lang: String,
    #[serde(default = "default_appearance")]
    pub appearance: String,
    #[serde(default = "default_close_behavior")]
    pub close_behavior: String,
    #[serde(default = "default_true")]
    pub telemetry_enabled: bool,
    #[serde(default = "default_true")]
    pub auto_update_enabled: bool,
    #[serde(default)]
    pub first_launch_done: bool,
    #[serde(default)]
    pub sidebar_sections: HashMap<String, bool>,
    #[serde(default)]
    pub data_dir_override: Option<String>,
}

fn default_lang() -> String { "cs".into() }
fn default_appearance() -> String { "dark".into() }
fn default_close_behavior() -> String { "minimize".into() }
fn default_true() -> bool { true }

impl Default for Settings {
    fn default() -> Self {
        Self {
            lang: default_lang(),
            appearance: default_appearance(),
            close_behavior: default_close_behavior(),
            telemetry_enabled: true,
            auto_update_enabled: true,
            first_launch_done: false,
            sidebar_sections: HashMap::new(),
            data_dir_override: None,
        }
    }
}

pub async fn load() -> AppResult<Settings> {
    let path = paths::config_file()?;
    if !path.exists() {
        return Ok(Settings::default());
    }
    let bytes = fs::read(&path).await.map_err(AppError::Io)?;
    let s: Settings = serde_json::from_slice(&bytes)
        .unwrap_or_else(|_| Settings::default());
    Ok(s)
}

pub async fn save(settings: &Settings) -> AppResult<()> {
    let path = paths::config_file()?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).await.map_err(AppError::Io)?;
    }
    let bytes = serde_json::to_vec_pretty(settings)?;
    fs::write(&path, bytes).await.map_err(AppError::Io)
}

pub async fn data_dir() -> AppResult<PathBuf> {
    paths::data_dir()
}

/// Mark first launch wizard completed — short-circuit for the first-launch
/// redirect logic in +layout.svelte.
pub async fn mark_first_launch_done() -> AppResult<()> {
    let mut s = load().await?;
    s.first_launch_done = true;
    save(&s).await
}

/// Reset everything in data dir except the encryption key file.
/// Returns count of removed files.
pub async fn factory_reset() -> AppResult<usize> {
    let dir = paths::data_dir()?;
    let key_path = paths::key_file()?;
    let mut count = 0usize;
    if !dir.exists() {
        return Ok(0);
    }
    let mut entries = fs::read_dir(&dir).await.map_err(AppError::Io)?;
    while let Some(e) = entries.next_entry().await.map_err(AppError::Io)? {
        let p = e.path();
        if p == key_path {
            continue;  // keep crypto key so user doesn't lose machine ID binding
        }
        let meta = e.metadata().await.map_err(AppError::Io)?;
        if meta.is_dir() {
            fs::remove_dir_all(&p).await.map_err(AppError::Io)?;
        } else {
            fs::remove_file(&p).await.map_err(AppError::Io)?;
        }
        count += 1;
    }
    Ok(count)
}

/// Open the data directory in the OS file manager (Win Explorer, Finder, etc.)
/// via shell open. Stub — wire in commands layer using Tauri shell plugin.
pub async fn data_dir_string() -> AppResult<String> {
    Ok(paths::data_dir()?.display().to_string())
}
