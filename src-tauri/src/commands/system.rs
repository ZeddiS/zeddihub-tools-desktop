//! System info + process management commands.
//!
//! Used by PCSysInfoPanel + PCUtilityPanel (Process List).

use serde::Serialize;
use sysinfo::{Disks, Pid, ProcessesToUpdate, System};
use crate::error::AppResult;

#[derive(Debug, Serialize)]
pub struct DiskInfo {
    pub mount: String,
    pub kind: String,
    pub total_mb: u64,
    pub free_mb: u64,
    pub used_mb: u64,
    pub usage_pct: f32,
}

#[derive(Debug, Serialize)]
pub struct SystemInfo {
    pub os: String,
    pub arch: String,
    pub cpu_name: String,
    pub cpu_cores: u32,
    pub cpu_usage_pct: f32,
    pub total_memory_mb: u64,
    pub used_memory_mb: u64,
    pub mem_usage_pct: f32,
    pub hostname: String,
    pub uptime_secs: u64,
    pub disks: Vec<DiskInfo>,
}

#[tauri::command]
pub async fn system_info() -> AppResult<SystemInfo> {
    let info = tokio::task::spawn_blocking(|| {
        let mut sys = System::new();
        sys.refresh_cpu_all();
        sys.refresh_memory();
        // sysinfo's CPU usage requires a sampling interval; sleep briefly.
        std::thread::sleep(std::time::Duration::from_millis(200));
        sys.refresh_cpu_all();

        let cpu_name = sys.cpus().first().map(|c| c.brand().trim().to_string()).unwrap_or_else(|| "unknown".into());
        let cpu_cores = sys.cpus().len() as u32;
        let cpu_usage_pct = sys.global_cpu_usage();

        let total_memory_mb = sys.total_memory() / 1024 / 1024;
        let used_memory_mb  = sys.used_memory() / 1024 / 1024;
        let mem_usage_pct = if total_memory_mb > 0 {
            (used_memory_mb as f32 / total_memory_mb as f32) * 100.0
        } else { 0.0 };

        let disks_list = Disks::new_with_refreshed_list();
        let disks: Vec<DiskInfo> = disks_list.list().iter().map(|d| {
            let total = d.total_space();
            let free  = d.available_space();
            let used  = total.saturating_sub(free);
            DiskInfo {
                mount:    d.mount_point().display().to_string(),
                kind:     format!("{:?}", d.kind()),
                total_mb: total / 1024 / 1024,
                free_mb:  free / 1024 / 1024,
                used_mb:  used / 1024 / 1024,
                usage_pct: if total > 0 { (used as f32 / total as f32) * 100.0 } else { 0.0 },
            }
        }).collect();

        SystemInfo {
            os: format!("{} {}", System::name().unwrap_or_default(), System::os_version().unwrap_or_default()),
            arch: std::env::consts::ARCH.to_string(),
            cpu_name,
            cpu_cores,
            cpu_usage_pct,
            total_memory_mb,
            used_memory_mb,
            mem_usage_pct,
            hostname: System::host_name().unwrap_or_else(|| "unknown".into()),
            uptime_secs: System::uptime(),
            disks,
        }
    }).await.map_err(|e| crate::error::AppError::Generic(e.to_string()))?;
    Ok(info)
}

// ── Processes (Utility panel) ────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct ProcessInfo {
    pub pid: u32,
    pub name: String,
    pub cpu_pct: f32,
    pub memory_mb: u64,
}

#[tauri::command]
pub async fn process_list() -> AppResult<Vec<ProcessInfo>> {
    let procs = tokio::task::spawn_blocking(|| {
        let mut sys = System::new();
        sys.refresh_processes(ProcessesToUpdate::All, true);
        std::thread::sleep(std::time::Duration::from_millis(200));
        sys.refresh_processes(ProcessesToUpdate::All, true);

        let mut out: Vec<ProcessInfo> = sys.processes().iter().map(|(pid, p)| ProcessInfo {
            pid: pid.as_u32(),
            name: p.name().to_string_lossy().to_string(),
            cpu_pct: p.cpu_usage(),
            memory_mb: p.memory() / 1024 / 1024,
        }).collect();
        // Most-CPU first, then memory
        out.sort_by(|a, b|
            b.cpu_pct.partial_cmp(&a.cpu_pct).unwrap_or(std::cmp::Ordering::Equal)
                .then(b.memory_mb.cmp(&a.memory_mb))
        );
        out
    }).await.map_err(|e| crate::error::AppError::Generic(e.to_string()))?;
    Ok(procs)
}

#[tauri::command]
pub async fn process_kill(pid: u32) -> AppResult<bool> {
    let killed = tokio::task::spawn_blocking(move || {
        let mut sys = System::new();
        sys.refresh_processes(ProcessesToUpdate::All, true);
        sys.process(Pid::from_u32(pid)).map(|p| p.kill()).unwrap_or(false)
    }).await.map_err(|e| crate::error::AppError::Generic(e.to_string()))?;
    Ok(killed)
}
