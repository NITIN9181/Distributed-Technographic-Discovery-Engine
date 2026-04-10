use std::collections::HashMap;
use tokio::sync::RwLock;

pub struct RobotsCache {
    cache: RwLock<HashMap<String, RobotsRules>>,
    fetcher: reqwest::Client,
}

pub struct RobotsRules {
    allowed_paths: Vec<String>,
    disallowed_paths: Vec<String>,
    crawl_delay: Option<f64>,
    fetched_at: std::time::Instant,
}

impl RobotsCache {
    pub fn new() -> Self {
        RobotsCache {
            cache: RwLock::new(HashMap::new()),
            fetcher: reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(5))
                .user_agent("TechDetector/1.0 (https://techdetector.example)")
                .build()
                .unwrap_or_default(),
        }
    }

    pub async fn is_allowed(&self, domain: &str, path: &str) -> (bool, Option<f64>) {
        let domain_string = domain.to_string();
        
        // Fast path: Check cache
        {
            let cache_read = self.cache.read().await;
            if let Some(rules) = cache_read.get(&domain_string) {
                // If fetched in the last hour, use it
                if rules.fetched_at.elapsed() < std::time::Duration::from_secs(3600) {
                    return (self.check_rules(rules, path), rules.crawl_delay);
                }
            }
        }

        // Slow path: Fetch and parse
        let url = format!("https://{}/robots.txt", domain);
        let rules = if let Ok(resp) = self.fetcher.get(&url).send().await {
            if let Ok(text) = resp.text().await {
                self.parse_rules(&text)
            } else {
                self.default_rules()
            }
        } else {
            self.default_rules()
        };

        let result = (self.check_rules(&rules, path), rules.crawl_delay);

        // Update cache
        let mut cache_write = self.cache.write().await;
        cache_write.insert(domain_string, rules);

        result
    }

    fn default_rules(&self) -> RobotsRules {
        RobotsRules {
            allowed_paths: vec![],
            disallowed_paths: vec![],
            crawl_delay: None,
            fetched_at: std::time::Instant::now(),
        }
    }

    fn parse_rules(&self, text: &str) -> RobotsRules {
        let mut rules = self.default_rules();
        let mut in_target_agent = false;

        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') { continue; }

            let parts: Vec<&str> = line.splitn(2, ':').collect();
            if parts.len() != 2 { continue; }

            let key = parts[0].trim().to_lowercase();
            let value = parts[1].trim();

            if key == "user-agent" {
                let agent = value.to_lowercase();
                in_target_agent = agent == "*" || agent.contains("techdetector");
            } else if in_target_agent {
                match key.as_str() {
                    "allow" => rules.allowed_paths.push(value.to_string()),
                    "disallow" => rules.disallowed_paths.push(value.to_string()),
                    "crawl-delay" => if let Ok(delay) = value.parse::<f64>() {
                        rules.crawl_delay = Some(delay);
                    },
                    _ => {}
                }
            }
        }
        rules
    }

    fn check_rules(&self, rules: &RobotsRules, path: &str) -> bool {
        // Find longest matching prefix
        let mut longest_disallow = 0;
        let mut longest_allow = 0;

        for d in &rules.disallowed_paths {
            if path.starts_with(d) && d.len() > longest_disallow {
                longest_disallow = d.len();
            }
        }
        
        for a in &rules.allowed_paths {
            if path.starts_with(a) && a.len() > longest_allow {
                longest_allow = a.len();
            }
        }

        // If allow is more specific, or if neither matched (implicitly allowed)
        longest_allow > longest_disallow || longest_disallow == 0
    }
}
