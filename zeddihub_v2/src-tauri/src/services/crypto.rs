//! Encrypted credential storage using ChaCha20Poly1305.
//!
//! Replaces Python's `cryptography.fernet` from gui/auth.py. Same idea:
//! key derived from machine-specific value (host + username), stored on disk
//! at first use; AEAD encrypt/decrypt of JSON payloads.

use chacha20poly1305::{
    aead::{Aead, KeyInit, OsRng, AeadCore},
    ChaCha20Poly1305, Key, Nonce,
};
use sha2::{Digest, Sha256};

use crate::error::{AppError, AppResult};
use crate::services::paths::key_file;

fn machine_id() -> String {
    let host = hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "unknown-host".to_string());
    let user = std::env::var("USERNAME")
        .or_else(|_| std::env::var("USER"))
        .unwrap_or_else(|_| "unknown-user".to_string());
    format!("zeddihub|{}|{}", host, user)
}

fn derive_key() -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(machine_id().as_bytes());
    let result = hasher.finalize();
    let mut key = [0u8; 32];
    key.copy_from_slice(&result);
    key
}

fn load_or_create_key() -> AppResult<[u8; 32]> {
    let path = key_file()?;
    if path.exists() {
        let bytes = std::fs::read(&path)?;
        if bytes.len() == 32 {
            let mut key = [0u8; 32];
            key.copy_from_slice(&bytes);
            return Ok(key);
        }
        // Corrupted — regenerate.
    }
    let key = derive_key();
    std::fs::write(&path, &key)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let perm = std::fs::Permissions::from_mode(0o600);
        let _ = std::fs::set_permissions(&path, perm);
    }
    Ok(key)
}

/// Encrypt arbitrary bytes. Returned bytes layout: nonce(12) || ciphertext.
pub fn encrypt(plain: &[u8]) -> AppResult<Vec<u8>> {
    let key_bytes = load_or_create_key()?;
    let cipher = ChaCha20Poly1305::new(Key::from_slice(&key_bytes));
    let nonce = ChaCha20Poly1305::generate_nonce(&mut OsRng);
    let ciphertext = cipher
        .encrypt(&nonce, plain)
        .map_err(|e| AppError::Crypto(e.to_string()))?;
    let mut out = Vec::with_capacity(12 + ciphertext.len());
    out.extend_from_slice(&nonce);
    out.extend_from_slice(&ciphertext);
    Ok(out)
}

pub fn decrypt(blob: &[u8]) -> AppResult<Vec<u8>> {
    if blob.len() < 12 {
        return Err(AppError::Crypto("Too short".into()));
    }
    let key_bytes = load_or_create_key()?;
    let cipher = ChaCha20Poly1305::new(Key::from_slice(&key_bytes));
    let nonce = Nonce::from_slice(&blob[..12]);
    cipher
        .decrypt(nonce, &blob[12..])
        .map_err(|e| AppError::Crypto(e.to_string()))
}

// Tiny inline hostname implementation — we don't need a full crate for this.
mod hostname {
    use std::ffi::OsString;

    #[cfg(target_os = "windows")]
    pub fn get() -> std::io::Result<OsString> {
        std::env::var_os("COMPUTERNAME")
            .map(Ok)
            .unwrap_or_else(|| Ok(OsString::from("windows-host")))
    }

    #[cfg(not(target_os = "windows"))]
    pub fn get() -> std::io::Result<OsString> {
        // gethostname via libc — but we'll just read $HOSTNAME or fallback.
        std::env::var_os("HOSTNAME")
            .map(Ok)
            .unwrap_or_else(|| Ok(OsString::from("unix-host")))
    }
}
