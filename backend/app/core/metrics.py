from prometheus_client import CollectorRegistry, Counter, Gauge

# Initialize standard REGISTRY
REGISTRY = CollectorRegistry()

# Counters
kintsugi_files_scanned_total = Counter(
    "kintsugi_files_scanned_total",
    "Total number of files scanned by the detection pipeline",
    registry=REGISTRY,
)

kintsugi_corruption_detected_total = Counter(
    "kintsugi_corruption_detected_total",
    "Total number of corrupted files detected",
    registry=REGISTRY,
)

# Gauges
kintsugi_scan_velocity_bytes = Gauge(
    "kintsugi_scan_velocity_bytes",
    "Current scan velocity in bytes processed",
    registry=REGISTRY,
)

kintsugi_active_plugins = Gauge(
    "kintsugi_active_plugins",
    "Number of active detector/backup plugins currently loaded",
    registry=REGISTRY,
)
