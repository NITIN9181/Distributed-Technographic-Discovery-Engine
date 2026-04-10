use serde::Serialize;
use trust_dns_resolver::{config::*, TokioAsyncResolver};

#[derive(Serialize)]
pub struct DNSRecords {
    pub domain: String,
    pub mx_records: Vec<String>,
    pub txt_records: Vec<String>,
    pub cname_records: Vec<String>,
    pub ns_records: Vec<String>,
    pub error: Option<String>,
}

pub struct DNSResolver {
    resolver: TokioAsyncResolver,
}

impl DNSResolver {
    pub async fn new() -> Self {
        // Use default google/cloudflare resolvers to ensure quick lookups
        let resolver =
            TokioAsyncResolver::tokio(ResolverConfig::cloudflare(), ResolverOpts::default());
        Self { resolver }
    }

    pub async fn resolve(&self, domain: &str) -> DNSRecords {
        let mut records = DNSRecords {
            domain: domain.to_string(),
            mx_records: vec![],
            txt_records: vec![],
            cname_records: vec![],
            ns_records: vec![],
            error: None,
        };

        match self.resolver.mx_lookup(domain).await {
            Ok(lookup) => {
                records.mx_records = lookup.iter().map(|v| v.exchange().to_utf8()).collect()
            }
            Err(e) => tracing::debug!("Failed MX lookup for {}: {}", domain, e),
        }

        match self.resolver.txt_lookup(domain).await {
            Ok(lookup) => {
                records.txt_records = lookup
                    .iter()
                    .map(|v| String::from_utf8_lossy(&v.txt_data().concat()).into_owned())
                    .collect()
            }
            Err(e) => tracing::debug!("Failed TXT lookup for {}: {}", domain, e),
        }

        match self.resolver.ns_lookup(domain).await {
            Ok(lookup) => records.ns_records = lookup.iter().map(|v| v.to_utf8()).collect(),
            Err(e) => tracing::debug!("Failed NS lookup for {}: {}", domain, e),
        }

        // Keep it simple for CNAME; CNAME only exists if there are no other records,
        // but we'll try looking it up just in case or for specific subdomains like www.
        let cname_query = format!("www.{}", domain);
        match self
            .resolver
            .lookup(
                &cname_query,
                trust_dns_resolver::proto::rr::RecordType::CNAME,
            )
            .await
        {
            Ok(lookup) => {
                for r in lookup.iter() {
                    if let Some(cname) = r.as_cname() {
                        records.cname_records.push(cname.to_utf8());
                    }
                }
            }
            Err(e) => tracing::debug!("Failed CNAME lookup for {}: {}", cname_query, e),
        }

        records
    }
}
