// crawler/crates/crawler-core/src/dns_resolver.rs
use hickory_resolver::TokioAsyncResolver;
use hickory_resolver::config::*;
use crate::payload::{DnsPayload, MxRecord};
use chrono::Utc;
use tracing::{debug, error};

pub struct DnsResolver {
    resolver: TokioAsyncResolver,
}

impl DnsResolver {
    pub async fn new() -> anyhow::Result<Self> {
        let resolver = TokioAsyncResolver::tokio(
            ResolverConfig::default(),
            ResolverOpts {
                cache_size: 1024,
                use_hosts_file: false,
                ..Default::default()
            },
        );
        Ok(Self { resolver })
    }

    pub async fn resolve_all(&self, domain: &str) -> anyhow::Result<DnsPayload> {
        let mut payload = DnsPayload {
            canonical_domain: domain.to_string(),
            crawl_timestamp: Utc::now(),
            a_records: vec![],
            aaaa_records: vec![],
            mx_records: vec![],
            txt_records: vec![],
            cname_records: vec![],
            ns_records: vec![],
        };

        // A records
        if let Ok(response) = self.resolver.ipv4_lookup(domain).await {
            payload.a_records = response.iter().map(|r| r.to_string()).collect();
        }

        // AAAA records
        if let Ok(response) = self.resolver.ipv6_lookup(domain).await {
            payload.aaaa_records = response.iter().map(|r| r.to_string()).collect();
        }

        // MX records
        if let Ok(response) = self.resolver.mx_lookup(domain).await {
            payload.mx_records = response.iter().map(|r| MxRecord {
                preference: r.preference(),
                exchange: r.exchange().to_string(),
            }).collect();
        }

        // TXT records (critical for SPF/DKIM detection)
        if let Ok(response) = self.resolver.txt_lookup(domain).await {
            payload.txt_records = response.iter().map(|r| {
                r.iter()
                    .map(|data| String::from_utf8_lossy(data).to_string())
                    .collect::<Vec<_>>()
                    .join("")
            }).collect();
        }

        // NS records
        if let Ok(response) = self.resolver.ns_lookup(domain).await {
            payload.ns_records = response.iter().map(|r| r.to_string()).collect();
        }

        debug!(domain = domain, "DNS resolution complete");
        Ok(payload)
    }
}
