//! Source RCON protocol client over TCP.
//!
//! Implements Valve's Source RCON Protocol — same one CS2 / CS:GO / TF2 servers
//! use. Authentication via SERVERDATA_AUTH (type=3), commands via
//! SERVERDATA_EXECCOMMAND (type=2), responses come back as
//! SERVERDATA_RESPONSE_VALUE (type=0).
//!
//! Packet format: `[i32 size][i32 id][i32 type][body bytes][\x00][\x00]`
//! All integers little-endian. `size` excludes its own 4 bytes.
//!
//! State is kept in `RconState` (Tauri-managed) — connection persists
//! across multiple `rcon_send` calls until `rcon_disconnect` or app exit.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::sync::Mutex;

use crate::error::{AppError, AppResult};

const TYPE_AUTH: i32 = 3;
const TYPE_EXEC: i32 = 2;

/// Max body size we'll accept from server (4 KiB is plenty for `status` etc.)
const MAX_BODY: usize = 4096;

pub struct Connection {
    stream: TcpStream,
    next_id: i32,
}

impl Connection {
    fn pack(id: i32, ptype: i32, body: &str) -> Vec<u8> {
        let mut body_bytes = body.as_bytes().to_vec();
        body_bytes.push(0); // null terminator for body
        body_bytes.push(0); // null terminator for empty string field
        let size: i32 = (body_bytes.len() + 8) as i32; // id(4) + type(4) + body
        let mut out = Vec::with_capacity(4 + size as usize);
        out.extend_from_slice(&size.to_le_bytes());
        out.extend_from_slice(&id.to_le_bytes());
        out.extend_from_slice(&ptype.to_le_bytes());
        out.extend_from_slice(&body_bytes);
        out
    }

    /// Read one packet. Returns `(id, type, body)`.
    async fn read_packet(&mut self) -> AppResult<(i32, i32, String)> {
        let mut size_buf = [0u8; 4];
        self.stream.read_exact(&mut size_buf).await
            .map_err(|e| AppError::Network(format!("rcon read size: {e}")))?;
        let size = i32::from_le_bytes(size_buf);
        if size < 8 || size as usize > MAX_BODY + 16 {
            return Err(AppError::Network(format!("rcon bad packet size {size}")));
        }
        let mut buf = vec![0u8; size as usize];
        self.stream.read_exact(&mut buf).await
            .map_err(|e| AppError::Network(format!("rcon read body: {e}")))?;

        let id = i32::from_le_bytes([buf[0], buf[1], buf[2], buf[3]]);
        let ptype = i32::from_le_bytes([buf[4], buf[5], buf[6], buf[7]]);
        let body = &buf[8..];
        // Strip trailing nulls
        let end = body.iter().position(|&b| b == 0).unwrap_or(body.len());
        let text = String::from_utf8_lossy(&body[..end]).into_owned();
        Ok((id, ptype, text))
    }

    pub async fn auth(&mut self, password: &str) -> AppResult<()> {
        self.next_id = 1;
        let pkt = Self::pack(self.next_id, TYPE_AUTH, password);
        self.stream.write_all(&pkt).await
            .map_err(|e| AppError::Network(format!("rcon auth write: {e}")))?;

        // Server replies with up to 2 packets — first is RESPONSE_VALUE (junk),
        // second is AUTH_RESPONSE. AUTH_RESPONSE id == -1 → bad password.
        let _ = self.read_packet().await?;
        let (id, _, _) = self.read_packet().await?;
        if id == -1 {
            return Err(AppError::Auth {
                key: "rcon_bad_password".into(),
                message: "Špatné RCON heslo.".into(),
            });
        }
        Ok(())
    }

    pub async fn exec(&mut self, cmd: &str) -> AppResult<String> {
        self.next_id = self.next_id.wrapping_add(1).max(2);
        let pkt = Self::pack(self.next_id, TYPE_EXEC, cmd);
        self.stream.write_all(&pkt).await
            .map_err(|e| AppError::Network(format!("rcon exec write: {e}")))?;

        // Read with 2 s timeout so we don't hang on commands that produce no output
        match tokio::time::timeout(Duration::from_secs(2), self.read_packet()).await {
            Ok(Ok((_, _, body))) => Ok(body),
            Ok(Err(e)) => Err(e),
            Err(_) => Ok(String::new()), // no response within timeout = OK
        }
    }
}

/// Tauri-managed state: one optional active connection.
pub struct RconState {
    pub conn: Arc<Mutex<HashMap<String, Connection>>>,
}

impl RconState {
    pub fn new() -> Self {
        Self { conn: Arc::new(Mutex::new(HashMap::new())) }
    }
}

impl Default for RconState {
    fn default() -> Self { Self::new() }
}

/// Connect to host:port + authenticate. Returns connection key (host:port string).
pub async fn connect(state: &RconState, host: &str, port: u16, password: &str) -> AppResult<String> {
    let addr = format!("{host}:{port}");
    let stream = tokio::time::timeout(
        Duration::from_secs(5),
        TcpStream::connect(&addr),
    ).await
        .map_err(|_| AppError::Network(format!("rcon connect timeout: {addr}")))?
        .map_err(|e| AppError::Network(format!("rcon connect: {e}")))?;

    let mut conn = Connection { stream, next_id: 0 };
    conn.auth(password).await?;

    let key = addr.clone();
    state.conn.lock().await.insert(key.clone(), conn);
    Ok(key)
}

pub async fn send(state: &RconState, key: &str, cmd: &str) -> AppResult<String> {
    let mut map = state.conn.lock().await;
    let conn = map.get_mut(key).ok_or_else(||
        AppError::NotFound(format!("RCON connection '{key}' not found")))?;
    conn.exec(cmd).await
}

pub async fn disconnect(state: &RconState, key: &str) -> AppResult<()> {
    let mut map = state.conn.lock().await;
    if let Some(mut conn) = map.remove(key) {
        let _ = conn.stream.shutdown().await;
    }
    Ok(())
}
