// crawler/crates/crawler-core/src/tls_inspector.rs
use crate::payload::TlsPayload;
use chrono::Utc;
use rustls::{ClientConfig, ClientConnection, ServerName};
use std::io::{Read, Write};
use std::net::TcpStream;
use std::sync::Arc;
use x509_parser::prelude::*;
use tracing::{debug, warn};

pub struct TlsInspector;

impl TlsInspector {
    pub fn inspect(domain: &str) -> anyhow::Result<TlsPayload> {
        let mut root_store = rustls::RootCertStore::empty();
        root_store.add_trust_anchors(
            webpki_roots::TLS_SERVER_ROOTS.iter().map(|ta| {
                rustls::OwnedTrustAnchor::from_subject_spki_name_constraints(
                    ta.subject,
                    ta.spki,
                    ta.name_constraints,
                )
            })
        );

        let config = ClientConfig::builder()
            .with_safe_defaults()
            .with_root_certificates(root_store)
            .with_no_client_auth();

        let server_name = ServerName::try_from(domain)?;
        let mut conn = ClientConnection::new(Arc::new(config), server_name)?;
        let mut tcp = TcpStream::connect(format!("{}:443", domain))?;

        // Complete TLS handshake
        let mut stream = rustls::Stream::new(&mut conn, &mut tcp);
        stream.write_all(b"")?; // trigger handshake

        let mut payload = TlsPayload {
            canonical_domain: domain.to_string(),
            crawl_timestamp: Utc::now(),
            issuer: None,
            subject: None,
            serial_number: None,
            not_before: None,
            not_after: None,
            san_domains: vec![],
            signature_algorithm: None,
            protocol_version: None,
        };

        if let Some(certs) = conn.peer_certificates() {
            if let Some(cert_der) = certs.first() {
                if let Ok((_, cert)) = X509Certificate::from_der(cert_der.as_ref()) {
                    payload.issuer = Some(cert.issuer().to_string());
                    payload.subject = Some(cert.subject().to_string());
                    payload.serial_number = Some(cert.serial.to_str_radix(16));
                    payload.not_before = Some(cert.validity().not_before.to_rfc2822());
                    payload.not_after = Some(cert.validity().not_after.to_rfc2822());
                    payload.signature_algorithm = Some(
                        cert.signature_algorithm.algorithm.to_string()
                    );

                    // Extract SANs
                    if let Ok(Some(san_ext)) = cert.subject_alternative_name() {
                        for name in &san_ext.value.general_names {
                            if let GeneralName::DNSName(dns) = name {
                                payload.san_domains.push(dns.to_string());
                            }
                        }
                    }
                }
            }
        }

        if let Some(version) = conn.protocol_version() {
            payload.protocol_version = Some(format!("{:?}", version));
        }

        debug!(domain = domain, "TLS inspection complete");
        Ok(payload)
    }
}
