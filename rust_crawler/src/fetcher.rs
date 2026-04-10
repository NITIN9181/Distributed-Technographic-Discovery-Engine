use serde::Serialize;
use std::collections::HashMap;

#[derive(Serialize, Clone)]
pub struct FetchResult {
    pub url: String,
    pub final_url: String,
    pub status_code: u16,
    pub headers: HashMap<String, String>,
    pub html: String,
    pub fetch_time_ms: u64,
    pub error: Option<String>,
}

pub struct Fetcher {
    client: reqwest::Client,
    max_body_size: usize,
}

impl Fetcher {
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(15))
            .user_agent("TechDetector/1.0 (https://techdetector.example)")
            .redirect(reqwest::redirect::Policy::limited(5))
            .pool_max_idle_per_host(10)
            .build()
            .expect("Failed to build HTTP client");

        Self {
            client,
            max_body_size: 5 * 1024 * 1024, // 5MB max
        }
    }

    pub async fn fetch(&self, url: &str) -> FetchResult {
        let start = std::time::Instant::now();
        let mut result = FetchResult {
            url: url.to_string(),
            final_url: url.to_string(),
            status_code: 0,
            headers: HashMap::new(),
            html: String::new(),
            fetch_time_ms: 0,
            error: None,
        };

        let response = match self.client.get(url).send().await {
            Ok(r) => r,
            Err(e) => {
                result.error = Some(e.to_string());
                result.fetch_time_ms = start.elapsed().as_millis() as u64;
                return result;
            }
        };

        result.status_code = response.status().as_u16();
        result.final_url = response.url().to_string();

        for (k, v) in response.headers().iter() {
            if let Ok(value) = v.to_str() {
                result
                    .headers
                    .insert(k.as_str().to_lowercase(), value.to_string());
            }
        }

        // Limit reading the body
        if let Some(content_length) = response.content_length() {
            if content_length as usize > self.max_body_size {
                result.error = Some("Response body exceeds maximum allowed size".to_string());
                result.fetch_time_ms = start.elapsed().as_millis() as u64;
                return result;
            }
        }

        match response.bytes().await {
            Ok(bytes) => {
                let text = String::from_utf8_lossy(&bytes).into_owned();
                // Ensure we don't save huge bodies even if they gzip to something small
                if text.len() > self.max_body_size {
                    result.html = text.chars().take(self.max_body_size).collect();
                } else {
                    result.html = text;
                }
            }
            Err(e) => {
                result.error = Some(e.to_string());
            }
        }

        result.fetch_time_ms = start.elapsed().as_millis() as u64;
        result
    }

    pub async fn fetch_career_pages(&self, domain: &str) -> Vec<FetchResult> {
        let urls = vec![
            format!("https://careers.{}", domain),
            format!("https://{}/careers", domain),
            format!("https://{}/jobs", domain),
        ];

        let mut futures = vec![];
        for url in urls.into_iter() {
            futures.push(async move { self.fetch(&url).await });
        }

        let mut success_pages = vec![];
        for res in futures::future::join_all(futures).await {
            if res.status_code == 200 && res.error.is_none() {
                success_pages.push(res);
            }
        }

        success_pages
    }
}
