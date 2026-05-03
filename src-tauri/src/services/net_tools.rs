//! Network utilities — DNS lookup, TCP port check.
//!
//! Used by LinksPanel "DNS / Port" tab and (later) PCNetToolsPanel.

use std::net::ToSocketAddrs;
use std::time::Duration;

use crate::error::{AppError, AppResult};

/// DNS lookup. Returns list of resolved IP addresses for the host portion.
/// `record_type` is currently informational — a true DNS-record-typed query
/// (A/AAAA/MX/TXT/...) needs a proper resolver crate (`hickory-resolver`).
/// For v2 alpha we use `ToSocketAddrs` which gives us A + AAAA only.
pub async fn dns_lookup(domain: &str, _record_type: &str) -> AppResult<Vec<String>> {
    if domain.is_empty() {
        return Err(AppError::BadInput("Domain is empty".into()));
    }
    // ToSocketAddrs needs a port — use 0 for resolver-only.
    let host = format!("{}:0", domain);

    let resolved = tokio::task::spawn_blocking(move || {
        host.to_socket_addrs()
            .map(|iter| iter.map(|sa| sa.ip().to_string()).collect::<Vec<_>>())
    })
    .await
    .map_err(|e| AppError::Generic(e.to_string()))?
    .map_err(AppError::Io)?;

    // Deduplicate while preserving order
    let mut seen = std::collections::HashSet::new();
    let unique: Vec<String> = resolved.into_iter().filter(|x| seen.insert(x.clone())).collect();
    Ok(unique)
}

/// TCP port check — returns true if connect within timeout succeeds.
pub async fn port_check(host: &str, port: u16, timeout_ms: u64) -> AppResult<bool> {
    if host.is_empty() {
        return Err(AppError::BadInput("Host is empty".into()));
    }
    let addr = format!("{}:{}", host, port);
    let timeout = Duration::from_millis(timeout_ms.max(100).min(30_000));

    let res = tokio::time::timeout(timeout, tokio::net::TcpStream::connect(&addr)).await;

    match res {
        Ok(Ok(_stream)) => Ok(true),
        Ok(Err(_)) => Ok(false),    // refused / unreachable
        Err(_) => Ok(false),        // timeout
    }
}

/// TCP latency probe — returns roundtrip time to handshake completion in ms,
/// or `None` on failure. Used by Ping Tester panel.
pub async fn tcp_ping(host: &str, port: u16, timeout_ms: u64) -> AppResult<Option<f64>> {
    if host.is_empty() {
        return Err(AppError::BadInput("Host is empty".into()));
    }
    let addr = format!("{}:{}", host, port);
    let timeout = Duration::from_millis(timeout_ms.max(100).min(30_000));

    let start = std::time::Instant::now();
    let res = tokio::time::timeout(timeout, tokio::net::TcpStream::connect(&addr)).await;

    Ok(match res {
        Ok(Ok(_stream)) => Some(start.elapsed().as_secs_f64() * 1000.0),
        Ok(Err(_)) | Err(_) => None,
    })
}
