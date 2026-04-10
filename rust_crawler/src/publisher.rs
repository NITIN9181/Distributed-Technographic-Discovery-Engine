use redis::AsyncCommands;
use serde::Serialize;
use serde_json;

#[derive(Serialize)]
pub struct CrawlResult {
    pub message_id: Option<String>, // Assigned by Redis, internal usage
    pub domain: String,
    pub crawled_at: String,
    pub html: String,
    pub headers: std::collections::HashMap<String, String>,
    pub career_pages: Vec<crate::fetcher::FetchResult>,
    pub dns_records: crate::dns::DNSRecords,
    pub tls_info: crate::tls::TLSInfo,
}

pub struct StreamPublisher {
    redis: redis::Client,
    stream_name: String,
}

impl StreamPublisher {
    pub fn new(redis: redis::Client, stream_name: String) -> Self {
        Self { redis, stream_name }
    }

    pub async fn publish(&self, result: CrawlResult) -> Result<String, redis::RedisError> {
        let mut con = self.redis.get_async_connection().await?;
        
        let payload = match serde_json::to_string(&result) {
            Ok(p) => p,
            Err(_) => return Err(redis::RedisError::from(
                std::io::Error::new(std::io::ErrorKind::InvalidData, "Failed to serialize")
            )),
        };

        let message_id: String = con.xadd(
            &self.stream_name,
            "*",
            &[("payload", &payload)],
        ).await?;

        Ok(message_id)
    }
}
