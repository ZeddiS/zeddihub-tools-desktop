//! Auth REST client + encrypted session storage.
//!
//! Talks to `https://zeddihub.eu/api/auth/*` with the same protocol as the
//! Python v1.7.x desktop app. APP_SECRET bypasses hCaptcha (server-side
//! check). Session token is persisted encrypted (chacha20poly1305) so
//! restart resumes without re-login.

use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::RwLock;

use crate::error::{AppError, AppResult};
use crate::services::{crypto, paths};

const API_BASE: &str = "https://zeddihub.eu/api/auth";

/// Shared with mobile + server (`api/_config.php::ZH_APP_SECRET`).
const APP_SECRET: &str = "696d63c65a8536637183028e4eecb841cd5b679ce7b2d33c6ef2d4054166e438";

const CLIENT_KIND: &str = "desktop";

/// Hardcoded username (lowercase) that gets the special `owner` role.
/// Owner sees hidden modules (e.g. Server Updater) and the admin panel
/// `/server_updater` config page. No DB column needed.
pub const OWNER_USERNAME: &str = "zeddis";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserDto {
    pub id: i64,
    pub username: String,
    pub email: String,
    #[serde(default)]
    pub role: String,
    #[serde(default, rename = "is_admin")]
    pub is_admin: bool,
    /// Computed locally from `username.to_lowercase() == OWNER_USERNAME`.
    /// Frontend gates Owner-only UI on this flag.
    #[serde(default, rename = "is_owner")]
    pub is_owner: bool,
}

/// Returns true when the user is the hardcoded Owner. Caller should
/// re-compute this from the `username` field — never trust client-supplied
/// `is_owner` for security-sensitive paths.
pub fn is_owner_user(user: &UserDto) -> bool {
    user.username.to_lowercase() == OWNER_USERNAME
}

/// Stamp `is_owner` flag on a UserDto from the username. All paths that
/// produce a UserDto for the frontend must call this before returning.
fn stamp_owner_flag(mut user: UserDto) -> UserDto {
    user.is_owner = is_owner_user(&user);
    user
}

/// What `/login` and `/register` return on success.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserSession {
    pub user: UserDto,
    pub token: String,
    #[serde(rename = "expires_at")]
    pub expires_at: i64,
}

/// Internal disk shape for `auth.enc`.
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
struct PersistedSession {
    username: String,
    token: String,
    expires_at: i64,
    /// Optional — kept so we can /login fresh when token expires.
    password: Option<String>,
    /// Optional cached user info (so resume can render UI before /me).
    user: Option<UserDto>,
}

/// In-memory session cache.
#[derive(Default)]
pub struct AuthState {
    inner: Arc<RwLock<Option<PersistedSession>>>,
}

impl AuthState {
    pub fn new() -> Self {
        Self::default()
    }

    fn http_client() -> AppResult<reqwest::Client> {
        reqwest::Client::builder()
            .timeout(Duration::from_secs(10))
            .user_agent(format!(
                "ZeddiHubTools/{} ({})",
                env!("CARGO_PKG_VERSION"),
                CLIENT_KIND
            ))
            .build()
            .map_err(AppError::Reqwest)
    }

    fn base_headers(token: Option<&str>) -> reqwest::header::HeaderMap {
        let mut h = reqwest::header::HeaderMap::new();
        h.insert("Accept", "application/json".parse().unwrap());
        h.insert("X-App-Secret", APP_SECRET.parse().unwrap());
        h.insert("X-Client-Kind", CLIENT_KIND.parse().unwrap());
        h.insert(
            "X-Client-Version",
            env!("CARGO_PKG_VERSION").parse().unwrap(),
        );
        if let Some(tok) = token {
            h.insert(
                reqwest::header::AUTHORIZATION,
                format!("Bearer {}", tok).parse().unwrap(),
            );
        }
        h
    }

    pub async fn login(&self, identifier: &str, password: &str) -> AppResult<UserSession> {
        let client = Self::http_client()?;
        let resp = client
            .post(format!("{}/login", API_BASE))
            .headers(Self::base_headers(None))
            .json(&serde_json::json!({
                "identifier": identifier,
                "password": password,
            }))
            .send()
            .await
            .map_err(|e| AppError::Network(e.to_string()))?;

        let status = resp.status();
        let body: serde_json::Value = resp.json().await.map_err(AppError::Reqwest)?;
        if !status.is_success() || body.get("ok").and_then(|v| v.as_bool()) != Some(true) {
            let key = body
                .get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("login_failed")
                .to_string();
            let msg = body
                .get("message")
                .and_then(|v| v.as_str())
                .unwrap_or(&key)
                .to_string();
            return Err(AppError::Auth { key, message: msg });
        }

        let mut session: UserSession = serde_json::from_value(body)?;
        session.user = stamp_owner_flag(session.user);

        // Persist for resume.
        let persisted = PersistedSession {
            username: session.user.username.clone(),
            token: session.token.clone(),
            expires_at: session.expires_at,
            password: Some(password.to_string()),
            user: Some(session.user.clone()),
        };
        self.persist(&persisted).await?;
        *self.inner.write().await = Some(persisted);

        Ok(session)
    }

    pub async fn register(
        &self,
        username: &str,
        email: &str,
        password: &str,
    ) -> AppResult<UserSession> {
        let client = Self::http_client()?;
        let resp = client
            .post(format!("{}/register", API_BASE))
            .headers(Self::base_headers(None))
            .json(&serde_json::json!({
                "username": username,
                "email": email,
                "password": password,
            }))
            .send()
            .await
            .map_err(|e| AppError::Network(e.to_string()))?;

        let status = resp.status();
        let body: serde_json::Value = resp.json().await.map_err(AppError::Reqwest)?;
        if !status.is_success() || body.get("ok").and_then(|v| v.as_bool()) != Some(true) {
            let key = body
                .get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("register_failed")
                .to_string();
            let msg = body
                .get("message")
                .and_then(|v| v.as_str())
                .unwrap_or(&key)
                .to_string();
            return Err(AppError::Auth { key, message: msg });
        }

        let mut session: UserSession = serde_json::from_value(body)?;
        session.user = stamp_owner_flag(session.user);
        let persisted = PersistedSession {
            username: session.user.username.clone(),
            token: session.token.clone(),
            expires_at: session.expires_at,
            password: Some(password.to_string()),
            user: Some(session.user.clone()),
        };
        self.persist(&persisted).await?;
        *self.inner.write().await = Some(persisted);
        Ok(session)
    }

    pub async fn me(&self) -> AppResult<UserDto> {
        // Try restore from disk if memory is empty.
        if self.inner.read().await.is_none() {
            if let Some(restored) = self.load_persisted().await {
                *self.inner.write().await = Some(restored);
            }
        }
        let session = self
            .inner
            .read()
            .await
            .clone()
            .ok_or_else(|| AppError::Auth {
                key: "no_session".into(),
                message: "Žádná aktivní session.".into(),
            })?;

        let client = Self::http_client()?;
        let resp = client
            .get(format!("{}/me", API_BASE))
            .headers(Self::base_headers(Some(&session.token)))
            .send()
            .await
            .map_err(|e| AppError::Network(e.to_string()))?;

        let status = resp.status();
        let body: serde_json::Value = resp.json().await.map_err(AppError::Reqwest)?;
        if !status.is_success() || body.get("ok").and_then(|v| v.as_bool()) != Some(true) {
            // Token mrtvý — zruš lokální session.
            *self.inner.write().await = None;
            let _ = self.delete_persisted().await;
            let key = body
                .get("error")
                .and_then(|v| v.as_str())
                .unwrap_or("me_failed")
                .to_string();
            let msg = body
                .get("message")
                .and_then(|v| v.as_str())
                .unwrap_or(&key)
                .to_string();
            return Err(AppError::Auth { key, message: msg });
        }

        let user: UserDto = serde_json::from_value(
            body.get("user").cloned().unwrap_or(serde_json::Value::Null),
        )?;
        let user = stamp_owner_flag(user);

        // Update cached user.
        if let Some(s) = self.inner.write().await.as_mut() {
            s.user = Some(user.clone());
        }
        Ok(user)
    }

    pub async fn logout(&self) -> AppResult<()> {
        let token = self.inner.read().await.as_ref().map(|s| s.token.clone());
        if let Some(tok) = token {
            let client = Self::http_client()?;
            let _ = client
                .post(format!("{}/logout", API_BASE))
                .headers(Self::base_headers(Some(&tok)))
                .send()
                .await; // best-effort
        }
        *self.inner.write().await = None;
        let _ = self.delete_persisted().await;
        Ok(())
    }

    // ── Disk persistence (encrypted) ────────────────────────────────────
    async fn persist(&self, session: &PersistedSession) -> AppResult<()> {
        let plain = serde_json::to_vec(session)?;
        let blob = crypto::encrypt(&plain)?;
        tokio::fs::write(paths::auth_file()?, blob)
            .await
            .map_err(AppError::Io)
    }

    async fn load_persisted(&self) -> Option<PersistedSession> {
        let path = paths::auth_file().ok()?;
        let blob = tokio::fs::read(&path).await.ok()?;
        let plain = crypto::decrypt(&blob).ok()?;
        serde_json::from_slice(&plain).ok()
    }

    async fn delete_persisted(&self) -> AppResult<()> {
        let path = paths::auth_file()?;
        if path.exists() {
            tokio::fs::remove_file(path).await.map_err(AppError::Io)?;
        }
        Ok(())
    }
}
