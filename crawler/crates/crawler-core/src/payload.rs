// crawler/crates/crawler-core/src/payload.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrawlPayload {
    pub canonical_domain: String,
    pub url: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub html_body: Option<String>,
    pub http_status: u16,
    pub response_headers: HashMap<String, String>,
    pub final_url: String,  // after redirects
    pub content_type: Option<String>,
    pub response_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DnsPayload {
    pub canonical_domain: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub a_records: Vec<String>,
    pub aaaa_records: Vec<String>,
    pub mx_records: Vec<MxRecord>,
    pub txt_records: Vec<String>,
    pub cname_records: Vec<String>,
    pub ns_records: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MxRecord {
    pub preference: u16,
    pub exchange: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TlsPayload {
    pub canonical_domain: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub issuer: Option<String>,
    pub subject: Option<String>,
    pub serial_number: Option<String>,
    pub not_before: Option<String>,
    pub not_after: Option<String>,
    pub san_domains: Vec<String>,
    pub signature_algorithm: Option<String>,
    pub protocol_version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobPostingPayload {
    pub canonical_domain: String,
    pub crawl_timestamp: DateTime<Utc>,
    pub page_url: String,
    pub raw_text: String,
    pub job_title: Option<String>,
}
