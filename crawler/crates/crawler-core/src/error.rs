// crawler/crates/crawler-core/src/error.rs
use thiserror::Error;

#[derive(Error, Debug)]
pub enum CrawlerError {
    #[error("Network error: {0}")]
    NetworkError(#[from] reqwest::Error),
    #[error("Configuration error: {0}")]
    ConfigError(String),
}
