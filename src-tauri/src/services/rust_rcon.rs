//! Rust (Facepunch) RCON over WebSocket.
//!
//! Protocol differs from Source RCON: connect as
//! `ws://host:port/password`, send JSON `{Identifier, Message, Name}`,
//! responses come back as JSON `{Message, Identifier, Type, Stacktrace}`.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;

use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use tokio::sync::{mpsc, Mutex};
use tokio_tungstenite::tungstenite::protocol::Message;

use crate::error::{AppError, AppResult};

#[derive(Debug, Serialize)]
struct ClientMsg<'a> {
    #[serde(rename = "Identifier")]
    identifier: i64,
    #[serde(rename = "Message")]
    message: &'a str,
    #[serde(rename = "Name")]
    name: &'a str,
}

#[derive(Debug, Deserialize, Default)]
struct ServerMsg {
    #[serde(rename = "Message", default)]
    message: String,
    #[allow(dead_code)]
    #[serde(rename = "Identifier", default)]
    identifier: i64,
    #[allow(dead_code)]
    #[serde(rename = "Type", default)]
    msg_type: String,
}

/// One active connection — channel for sending commands, receiver for responses.
pub struct Connection {
    tx: mpsc::Sender<String>,
    /// Buffer of recent unsolicited messages from server (chat, joins…).
    /// Drained on `recv()` calls.
    buffer: Arc<Mutex<Vec<String>>>,
    next_id: i64,
}

#[derive(Default)]
pub struct RustRconState {
    inner: Arc<Mutex<HashMap<String, Connection>>>,
}

impl RustRconState {
    pub fn new() -> Self { Self::default() }
}

pub async fn connect(state: &RustRconState, host: &str, port: u16, password: &str) -> AppResult<String> {
    let url = format!("ws://{host}:{port}/{password}");

    let connect_future = tokio_tungstenite::connect_async(&url);
    let (ws, _resp) = tokio::time::timeout(Duration::from_secs(5), connect_future)
        .await
        .map_err(|_| AppError::Network(format!("Rust RCON connect timeout: {host}:{port}")))?
        .map_err(|e| {
            // tungstenite returns 401 on bad password, "connection reset" on
            // refused. Both go through `e.to_string()` cleanly.
            let s = e.to_string();
            if s.contains("401") || s.contains("Unauthorized") {
                AppError::Auth { key: "rust_rcon_bad_password".into(), message: "Špatné RCON heslo.".into() }
            } else {
                AppError::Network(format!("Rust RCON connect: {s}"))
            }
        })?;

    let (mut sink, mut stream) = ws.split();
    let (tx, mut rx) = mpsc::channel::<String>(32);
    let buffer: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(Vec::new()));
    let buffer_clone = buffer.clone();

    // Sender task: forward strings from rx → sink.
    tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            if sink.send(Message::Text(msg.into())).await.is_err() {
                break;
            }
        }
        let _ = sink.close().await;
    });

    // Receiver task: parse server messages, push to buffer.
    tokio::spawn(async move {
        while let Some(msg) = stream.next().await {
            let Ok(msg) = msg else { break };
            let text = match msg {
                Message::Text(t) => t.to_string(),
                Message::Binary(b) => String::from_utf8_lossy(&b).to_string(),
                Message::Close(_) => break,
                _ => continue,
            };
            let parsed: ServerMsg = serde_json::from_str(&text).unwrap_or_default();
            let line = if parsed.message.is_empty() { text } else { parsed.message };
            let mut buf = buffer_clone.lock().await;
            buf.push(line);
            // Cap buffer to avoid unbounded growth
            if buf.len() > 500 {
                let drop_n = buf.len() - 500;
                buf.drain(..drop_n);
            }
        }
    });

    let key = format!("{host}:{port}");
    state.inner.lock().await.insert(key.clone(), Connection {
        tx,
        buffer,
        next_id: 1,
    });
    Ok(key)
}

pub async fn send(state: &RustRconState, key: &str, cmd: &str) -> AppResult<()> {
    let mut map = state.inner.lock().await;
    let conn = map.get_mut(key).ok_or_else(||
        AppError::NotFound(format!("Rust RCON connection '{key}' not found")))?;
    let id = conn.next_id;
    conn.next_id = conn.next_id.wrapping_add(1).max(1);
    let msg = ClientMsg { identifier: id, message: cmd, name: "ZeddiHub" };
    let json = serde_json::to_string(&msg)?;
    conn.tx.send(json).await
        .map_err(|_| AppError::Network("Rust RCON channel closed".into()))?;
    // Give server a moment to push response
    drop(map);
    tokio::time::sleep(Duration::from_millis(200)).await;
    Ok(())
}

pub async fn recv(state: &RustRconState, key: &str) -> AppResult<Vec<String>> {
    let map = state.inner.lock().await;
    let conn = map.get(key).ok_or_else(||
        AppError::NotFound(format!("Rust RCON connection '{key}' not found")))?;
    let mut buf = conn.buffer.lock().await;
    let drained: Vec<String> = buf.drain(..).collect();
    Ok(drained)
}

pub async fn disconnect(state: &RustRconState, key: &str) -> AppResult<()> {
    let mut map = state.inner.lock().await;
    if let Some(conn) = map.remove(key) {
        // Closing the channel cascades to close the WebSocket sender task
        drop(conn);
    }
    Ok(())
}
