use redis::AsyncCommands;

pub struct DistributedRateLimiter {
    redis: redis::Client,
    default_rate: f64,
}

impl DistributedRateLimiter {
    pub fn new(redis: redis::Client, default_rate: f64) -> Self {
        Self { redis, default_rate }
    }

    pub fn acquire<'a>(&'a self, domain: &'a str) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(), Box<dyn std::error::Error + Send + Sync>>> + Send + 'a>> {
        Box::pin(async move {
            let mut con = self.redis.get_async_connection().await?;
            let key = format!("rate_limit:{}", domain);
            
            let rate: f64 = match con.get(&format!("rate_limit_config:{}", domain)).await {
                Ok(val) => val,
                Err(_) => self.default_rate,
            };

            if rate <= 0.0 {
                // Implicit 0 delay
                return Ok(());
            }

            let current_time = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_millis() as u64;
            let window_size = 1000; // 1 second window
            let window_start = current_time - window_size;

            // Sliding window logic using Redis sorted sets
            redis::pipe()
                .atomic()
                .zrembyscore(&key, "-inf", window_start)
                .zadd(&key, current_time as f64, current_time)
                .expire(&key, 2)
                .query_async::<_, ()>(&mut con).await?;

            let count: i32 = con.zcard(&key).await?;

            if count as f64 > rate {
                // Wait out the limit and recurse. Simple backoff format.
                tokio::time::sleep(std::time::Duration::from_millis((1000.0 / rate) as u64)).await;
                return self.acquire(domain).await;
            }

            Ok(())
        })
    }
    
    pub async fn set_rate(&self, domain: &str, rate: f64) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut con = self.redis.get_async_connection().await?;
        let key = format!("rate_limit_config:{}", domain);
        con.set_ex::<_, _, ()>(key, rate, 3600).await?; // Cache for 1 hour
        Ok(())
    }
}
