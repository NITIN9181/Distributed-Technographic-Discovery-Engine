// crawler/crates/crawler-kafka/src/producer.rs
use rdkafka::config::ClientConfig;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::util::Timeout;
// We need to import the payload structs. Wait, in the project plan, 
// producer.rs has: `use crate::payload::*;` or uses `crawler_core::payload::*`
// Ah, crawler-kafka depends on crawler-core or it uses its own payload?
// actually `crawler-kafka` doesn't have `payload` defined. The plan has `use crate::payload::*;` 
// inside `crawler-kafka/src/producer.rs` which is actually incorrect if payload is in `crawler-core`.
// In a typical rust workspace, crawler-kafka would depend on crawler-core, but crawler-core depends on crawler-kafka!
// To fix cyclic dependency, `crawler-kafka` probably uses `crawler_core::payload::*`, but since crawler-core depends on crawler-kafka, that's cyclic.
// Actually, `payload.rs` could be moved or redefined, or `serde_json::Value` could be used. Or we can just duplicate payload or make a common crate.
// Wait, the project plan says `use crate::payload::*;` inside `producer.rs`. Let me check if payload was in Kafka crate.
// No, payload.rs is in `crawler-core`. Let me just replace the payload imports with `serde::Serialize` and take an opaque struct!

use serde::Serialize;
use std::time::Duration;
use tracing::error;

pub struct KafkaPayloadProducer {
    producer: FutureProducer,
}

impl KafkaPayloadProducer {
    pub fn new(brokers: &str) -> anyhow::Result<Self> {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("message.timeout.ms", "5000")
            .set("queue.buffering.max.messages", "100000")
            .set("queue.buffering.max.kbytes", "1048576") // 1GB buffer
            .set("batch.num.messages", "1000")
            .set("linger.ms", "50")
            .set("compression.type", "zstd")
            .set("acks", "1")
            .create()?;

        Ok(Self { producer })
    }

    async fn send<T: Serialize>(&self, topic: &str, key: &str, payload: &T) -> anyhow::Result<()> {
        let json = serde_json::to_string(payload)?;
        let record = FutureRecord::to(topic)
            .key(key)
            .payload(&json);

        self.producer
            .send(record, Timeout::After(Duration::from_secs(5)))
            .await
            .map_err(|(err, _)| {
                error!(topic = topic, key = key, error = %err, "Kafka send failed");
                anyhow::anyhow!("Kafka produce error: {}", err)
            })?;

        Ok(())
    }

    pub async fn send_crawl_payload<T: Serialize>(&self, topic: &str, payload: &T, key: &str) -> anyhow::Result<()> {
        self.send(topic, key, payload).await
    }

    // Since we don't have the specific types here to break circular dependencies, 
    // we use generics that implement Serialize and pass the key explicitly.
    pub async fn send_headers<T: Serialize>(&self, topic: &str, payload: &T, key: &str) -> anyhow::Result<()> {
        self.send(topic, key, payload).await
    }

    pub async fn send_dns<T: Serialize>(&self, topic: &str, payload: &T, key: &str) -> anyhow::Result<()> {
        self.send(topic, key, payload).await
    }

    pub async fn send_tls<T: Serialize>(&self, topic: &str, payload: &T, key: &str) -> anyhow::Result<()> {
        self.send(topic, key, payload).await
    }

    pub async fn send_job_posting<T: Serialize>(&self, topic: &str, payload: &T, key: &str) -> anyhow::Result<()> {
        self.send(topic, key, payload).await
    }
}
