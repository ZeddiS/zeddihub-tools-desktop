//! Steam A2S_INFO server query (UDP).
//!
//! Reference: https://developer.valvesoftware.com/wiki/Server_queries
//! Used by WatchdogPanel + (future) Server Updater status checks.

use std::time::{Duration, Instant};

use serde::Serialize;
use tokio::net::UdpSocket;
use tokio::time::timeout;

use crate::error::{AppError, AppResult};

const A2S_INFO_REQUEST: &[u8] = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00";

#[derive(Debug, Clone, Serialize)]
pub struct ServerInfo {
    pub online: bool,
    pub ping_ms: u32,
    pub name:        Option<String>,
    pub map:         Option<String>,
    pub players:     Option<u8>,
    pub max_players: Option<u8>,
}

impl ServerInfo {
    fn offline() -> Self {
        Self { online: false, ping_ms: 0, name: None, map: None, players: None, max_players: None }
    }
}

/// Query a Source-engine server. Falls back to TCP connectivity probe if UDP
/// fails (some servers block A2S but still respond on game port).
pub async fn query(host: &str, port: u16, timeout_ms: u64) -> AppResult<ServerInfo> {
    if host.is_empty() {
        return Err(AppError::BadInput("Host is empty".into()));
    }
    let addr = format!("{}:{}", host, port);
    let dur = Duration::from_millis(timeout_ms.max(500).min(10_000));

    // ── Try UDP A2S_INFO first ────────────────────────────────────────
    let started = Instant::now();
    let udp_result = async {
        let sock = UdpSocket::bind("0.0.0.0:0").await?;
        sock.connect(&addr).await?;
        sock.send(A2S_INFO_REQUEST).await?;
        let mut buf = [0u8; 4096];
        let n = sock.recv(&mut buf).await?;

        // Some servers reply with a challenge first (header 0x41) — re-send
        // request with the challenge appended.
        let response = if n >= 5 && buf[4] == b'A' {
            let challenge = &buf[5..9].to_vec();
            let mut req = A2S_INFO_REQUEST.to_vec();
            req.extend_from_slice(challenge);
            sock.send(&req).await?;
            let n2 = sock.recv(&mut buf).await?;
            buf[..n2].to_vec()
        } else {
            buf[..n].to_vec()
        };
        Ok::<Vec<u8>, std::io::Error>(response)
    };

    if let Ok(Ok(data)) = timeout(dur, udp_result).await {
        let ping_ms = started.elapsed().as_millis() as u32;
        if let Some(info) = parse_a2s_info(&data) {
            return Ok(ServerInfo {
                online: true,
                ping_ms,
                ..info
            });
        }
        // Got a UDP response but couldn't parse — server is alive at least.
        return Ok(ServerInfo {
            online: true, ping_ms,
            name: None, map: None, players: None, max_players: None,
        });
    }

    // ── Fallback: TCP connectivity probe ──────────────────────────────
    let tcp_started = Instant::now();
    let tcp_res = timeout(dur, tokio::net::TcpStream::connect(&addr)).await;
    if let Ok(Ok(_)) = tcp_res {
        return Ok(ServerInfo {
            online: true,
            ping_ms: tcp_started.elapsed().as_millis() as u32,
            name: None, map: None, players: None, max_players: None,
        });
    }

    Ok(ServerInfo::offline())
}

/// Parse A2S_INFO response payload (Source Engine 0x49 reply).
fn parse_a2s_info(data: &[u8]) -> Option<ServerInfo> {
    if data.len() < 6 { return None; }
    // 4-byte 0xFF header, 1-byte type, 1-byte protocol
    if &data[..4] != [0xFF, 0xFF, 0xFF, 0xFF] { return None; }
    if data[4] != 0x49 { return None; } // 'I' = info reply

    let mut pos = 6usize;

    // Strings are null-terminated UTF-8.
    fn read_str(d: &[u8], pos: &mut usize) -> Option<String> {
        let end = d[*pos..].iter().position(|&b| b == 0)?;
        let s = String::from_utf8_lossy(&d[*pos..*pos + end]).to_string();
        *pos += end + 1;
        Some(s)
    }

    let name        = read_str(data, &mut pos)?;
    let map         = read_str(data, &mut pos)?;
    let _folder     = read_str(data, &mut pos)?;
    let _game_name  = read_str(data, &mut pos)?;

    if pos + 4 > data.len() {
        return Some(ServerInfo {
            online: true, ping_ms: 0,
            name: Some(name), map: Some(map),
            players: None, max_players: None,
        });
    }

    // Skip 2-byte AppID, then players + max_players + bots (1 byte each)
    pos += 2;
    let players = if pos < data.len() { Some(data[pos]) } else { None };
    pos += 1;
    let max_players = if pos < data.len() { Some(data[pos]) } else { None };

    Some(ServerInfo {
        online: true, ping_ms: 0,
        name: Some(name), map: Some(map),
        players, max_players,
    })
}
