//! Process-wide HTTP cache with TTL.
//!
//! Mirrors `gui/http_cache.py` from the v1.7.9 experiment, but in Rust:
//! in-memory map, async-safe via `tokio::sync::RwLock`, returns stale data
//! on network failure when available (better UX than blank screens).

use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};

use tokio::sync::RwLock;

use crate::error::{AppError, AppResult};

/// In-memory cache entry — wrap an arbitrary JSON value with timestamp.
#[derive(Clone)]
struct Entry {
    inserted_at: Instant,
    value: serde_json::Value,
}

#[derive(Default)]
pub struct HttpCache {
    inner: Arc<RwLock<HashMap<String, Entry>>>,
}

impl HttpCache {
    pub fn new() -> Self {
        Self::default()
    }

    /// Fetch JSON with TTL cache. If fresh, returns cached. If stale or
    /// missing, fetches; on network failure returns stale if available.
    pub async fn fetch_json(
        &self,
        url: &str,
        ttl_seconds: u64,
        force_refresh: bool,
    ) -> AppResult<serde_json::Value> {
        if !force_refresh {
            if let Some(v) = self.fresh(url, ttl_seconds).await {
                return Ok(v);
            }
        }

        match self.do_fetch(url).await {
            Ok(value) => {
                self.store(url, value.clone()).await;
                Ok(value)
            }
            Err(e) => {
                // Network failed — return stale cache if any.
                if let Some(v) = self.any_cached(url).await {
                    return Ok(v);
                }
                Err(e)
            }
        }
    }

    async fn fresh(&self, url: &str, ttl_seconds: u64) -> Option<serde_json::Value> {
        let map = self.inner.read().await;
        let entry = map.get(url)?;
        if entry.inserted_at.elapsed() < Duration::from_secs(ttl_seconds) {
            Some(entry.value.clone())
        } else {
            None
        }
    }

    async fn any_cached(&self, url: &str) -> Option<serde_json::Value> {
        let map = self.inner.read().await;
        map.get(url).map(|e| e.value.clone())
    }

    async fn store(&self, url: &str, value: serde_json::Value) {
        let mut map = self.inner.write().await;
        map.insert(
            url.to_string(),
            Entry {
                inserted_at: Instant::now(),
                value,
            },
        );
    }

    async fn do_fetch(&self, url: &str) -> AppResult<serde_json::Value> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(8))
            .user_agent(format!(
                "ZeddiHubTools/{} (tauri-rust)",
                env!("CARGO_PKG_VERSION")
            ))
            .build()
            .map_err(AppError::Reqwest)?;
        let resp = client
            .get(url)
            .header("Accept", "application/json")
            .send()
            .await
            .map_err(|e| AppError::Network(e.to_string()))?;

        let status = resp.status().as_u16();
        if !resp.status().is_success() {
            let body = resp.text().await.unwrap_or_default();
            return Err(AppError::Http {
                status,
                message: body.chars().take(200).collect(),
            });
        }

        let value: serde_json::Value = resp.json().await.map_err(AppError::Reqwest)?;
        Ok(value)
    }

    pub async fn invalidate(&self, url: &str) {
        let mut map = self.inner.write().await;
        map.remove(url);
    }

    pub async fn age_seconds(&self, url: &str) -> Option<u64> {
        let map = self.inner.read().await;
        map.get(url).map(|e| e.inserted_at.elapsed().as_secs())
    }
}
