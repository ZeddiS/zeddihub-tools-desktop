//! Unified `AppError` type for all Tauri commands. Auto-implements `Serialize`
//! so the frontend gets clean JSON error objects.

use serde::{Serialize, Serializer};

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("Network: {0}")]
    Network(String),

    #[error("HTTP {status}: {message}")]
    Http { status: u16, message: String },

    #[error("Auth: {key} — {message}")]
    Auth { key: String, message: String },

    #[error("IO: {0}")]
    Io(#[from] std::io::Error),

    #[error("Serde: {0}")]
    Serde(#[from] serde_json::Error),

    #[error("Reqwest: {0}")]
    Reqwest(#[from] reqwest::Error),

    #[error("Crypto: {0}")]
    Crypto(String),

    #[error("Bad input: {0}")]
    BadInput(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Generic: {0}")]
    Generic(String),
}

// Tauri requires command errors to be `Serialize`. We serialise to a tagged
// JSON shape so the JS side can branch on the error key.
impl Serialize for AppError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let (key, message, status) = match self {
            AppError::Network(m)         => ("network",     m.clone(), None),
            AppError::Http { status, message } => ("http", message.clone(), Some(*status)),
            AppError::Auth { key, message }    => (key.as_str(), message.clone(), None),
            AppError::Io(e)              => ("io",          e.to_string(), None),
            AppError::Serde(e)           => ("serde",       e.to_string(), None),
            AppError::Reqwest(e)         => ("reqwest",     e.to_string(), None),
            AppError::Crypto(m)          => ("crypto",      m.clone(), None),
            AppError::BadInput(m)        => ("bad_input",   m.clone(), None),
            AppError::NotFound(m)        => ("not_found",   m.clone(), None),
            AppError::Generic(m)         => ("generic",     m.clone(), None),
        };

        let mut out = serde_json::Map::new();
        out.insert("key".into(),     serde_json::Value::String(key.to_string()));
        out.insert("message".into(), serde_json::Value::String(message));
        if let Some(s) = status {
            out.insert("status".into(), serde_json::Value::Number(s.into()));
        }
        serde_json::Value::Object(out).serialize(serializer)
    }
}

pub type AppResult<T> = std::result::Result<T, AppError>;
