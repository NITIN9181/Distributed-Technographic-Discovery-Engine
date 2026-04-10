"""
Prometheus metrics for TechDetector.

Exposes counters, histograms, and gauges for:
- Detection pipeline (per-vector, per-technology)
- Worker processing (throughput, latency)
- Queue depth (pending domains, stream messages)
- Database operations
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Detection metrics
DETECTIONS_TOTAL = Counter(
    "techdetector_detections_total",
    "Total number of technologies detected",
    ["vector", "technology", "category"],
)

DETECTION_DURATION = Histogram(
    "techdetector_detection_duration_seconds",
    "Time spent running detection pipeline",
    ["vector"],
)

# Worker metrics
MESSAGES_PROCESSED = Counter(
    "techdetector_messages_processed_total",
    "Total messages processed by workers",
    ["status"],  # success, error
)

MESSAGE_PROCESSING_DURATION = Histogram(
    "techdetector_message_processing_seconds", "Time to process a single message"
)

QUEUE_DEPTH = Gauge(
    "techdetector_queue_depth",
    "Current depth of various queues",
    ["queue"],  # pending, stream
)

# Database metrics
DB_OPERATIONS = Counter(
    "techdetector_db_operations_total", "Database operations", ["operation", "status"]
)


def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics HTTP server on the given port."""
    start_http_server(port)
