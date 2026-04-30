//! System info commands — used by PCSysInfoPanel etc.

use serde::Serialize;
use sysinfo::System;
use crate::error::AppResult;

#[derive(Debug, Serialize)]
pub struct SystemInfo {
    pub os: String,
    pub arch: String,
    pub cpu_name: String,
    pub cpu_cores: u32,
    pub total_memory_mb: u64,
    pub hostname: String,
}

#[tauri::command]
pub async fn system_info() -> AppResult<SystemInfo> {
    let mut sys = System::new();
    sys.refresh_cpu_all();
    sys.refresh_memory();

    let cpu_name = sys
        .cpus()
        .first()
        .map(|c| c.brand().to_string())
        .unwrap_or_else(|| "unknown".into());
    let cpu_cores = sys.cpus().len() as u32;
    let total_memory_mb = sys.total_memory() / 1024 / 1024;

    Ok(SystemInfo {
        os: format!("{} {}", System::name().unwrap_or_default(), System::os_version().unwrap_or_default()),
        arch: std::env::consts::ARCH.to_string(),
        cpu_name,
        cpu_cores,
        total_memory_mb,
        hostname: System::host_name().unwrap_or_else(|| "unknown".into()),
    })
}
