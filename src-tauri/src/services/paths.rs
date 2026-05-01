//! Per-platform data directory resolver.
//!
//! Windows: `%LOCALAPPDATA%\ZeddiHub\Tools`
//! macOS:   `~/Library/Application Support/eu.zeddihub.tools`
//! Linux:   `~/.local/share/zeddihub-tools`

use std::path::PathBuf;
use crate::error::{AppError, AppResult};

const APP_NAME: &str = "ZeddiHub";
const SUB_DIR: &str = "Tools";

/// Resolve and ensure the app data directory exists.
pub fn data_dir() -> AppResult<PathBuf> {
    let base = directories::ProjectDirs::from("eu", APP_NAME, SUB_DIR)
        .ok_or_else(|| AppError::Generic("Cannot resolve project dirs".into()))?;
    let dir = base.data_local_dir().to_path_buf();
    std::fs::create_dir_all(&dir).map_err(AppError::Io)?;
    Ok(dir)
}

pub fn cache_dir() -> AppResult<PathBuf> {
    let base = directories::ProjectDirs::from("eu", APP_NAME, SUB_DIR)
        .ok_or_else(|| AppError::Generic("Cannot resolve project dirs".into()))?;
    let dir = base.cache_dir().to_path_buf();
    std::fs::create_dir_all(&dir).map_err(AppError::Io)?;
    Ok(dir)
}

pub fn config_file() -> AppResult<PathBuf> {
    Ok(data_dir()?.join("settings.json"))
}

pub fn auth_file() -> AppResult<PathBuf> {
    Ok(data_dir()?.join("auth.enc"))
}

pub fn key_file() -> AppResult<PathBuf> {
    Ok(data_dir()?.join(".key"))
}
