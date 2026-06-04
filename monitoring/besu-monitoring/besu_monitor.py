#!/usr/bin/env python3
"""
Append-only Besu host/container resource monitor.

Each run writes one compact JSON record to logs/metrics.jsonl. It is designed
to be triggered by systemd timer, but it can also be run manually.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import docker
import psutil


SCHEMA_VERSION = 2

DEFAULT_CONTAINERS = [
    "blockchain-validator1-1",
    "blockchain-validator2-1",
    "blockchain-validator3-1",
    "blockchain-validator4-1",
    "rpcnode",
]

DEFAULT_DIRS = [
    "/home/manos/blockchain",
    "/home/manos/blockchain/config/besu",
    "/home/manos/blockchain/logs/besu",
    "/home/manos/blockchain/config/nodes/validator1",
    "/home/manos/blockchain/config/nodes/validator2",
    "/home/manos/blockchain/config/nodes/validator3",
    "/home/manos/blockchain/config/nodes/validator4",
]


def parse_csv_env(name, default):
    """Read a comma-separated environment variable with a sensible default."""
    raw_value = os.environ.get(name)
    if not raw_value:
        return default

    values = [value.strip() for value in raw_value.split(",") if value.strip()]
    return values or default


CONTAINERS = parse_csv_env("BESU_MONITOR_CONTAINERS", DEFAULT_CONTAINERS)
DIRS = parse_csv_env("BESU_MONITOR_DIRS", DEFAULT_DIRS)
LOG_DIR = Path(os.environ.get("BESU_MONITOR_LOG_DIR", Path(__file__).parent / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
METRICS_LOG = LOG_DIR / "metrics.jsonl"


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "monitor.log"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def human_bytes(size_bytes):
    if size_bytes is None:
        return None

    value = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024


def percent(used, total):
    return round((used / total) * 100, 2) if total else 0.0


def get_system_stats():
    try:
        disk_usage = psutil.disk_usage("/")
        memory = psutil.virtual_memory()
        load_average = os.getloadavg() if hasattr(os, "getloadavg") else None

        return {
            "disk": {
                "path": "/",
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "percent": round(disk_usage.percent, 2),
                "used": human_bytes(disk_usage.used),
                "total": human_bytes(disk_usage.total),
                "free": human_bytes(disk_usage.free),
            },
            "memory": {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "percent": round(memory.percent, 2),
                "used": human_bytes(memory.used),
                "total": human_bytes(memory.total),
                "available": human_bytes(memory.available),
            },
            "load_average": {
                "1m": load_average[0],
                "5m": load_average[1],
                "15m": load_average[2],
            }
            if load_average
            else None,
        }
    except Exception as exc:
        logging.error("Error getting system stats: %s", exc)
        return {"status": "error", "error": str(exc)}


def calculate_container_cpu_percent(container_stats):
    cpu_stats = container_stats.get("cpu_stats", {})
    precpu_stats = container_stats.get("precpu_stats", {})
    cpu_usage = cpu_stats.get("cpu_usage", {})
    precpu_usage = precpu_stats.get("cpu_usage", {})

    cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get("total_usage", 0)
    system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
    online_cpus = (
        cpu_stats.get("online_cpus")
        or len(cpu_usage.get("percpu_usage", []))
        or psutil.cpu_count()
        or 1
    )

    if cpu_delta <= 0 or system_delta <= 0:
        return 0.0

    return round((cpu_delta / system_delta) * online_cpus * 100, 2)


def get_container_memory_stats(memory_stats):
    raw_usage = memory_stats.get("usage", 0)
    stats = memory_stats.get("stats", {})
    cache = stats.get("inactive_file", stats.get("cache", 0))
    usage = max(raw_usage - cache, 0)
    limit = memory_stats.get("limit", 0)

    return {
        "usage_bytes": usage,
        "limit_bytes": limit,
        "percent": percent(usage, limit),
        "usage": human_bytes(usage),
        "limit": human_bytes(limit),
    }


def get_docker_stats():
    try:
        client = docker.from_env()
        stats = {}

        for container_name in CONTAINERS:
            try:
                container = client.containers.get(container_name)
                container_stats = container.stats(stream=False)
                stats[container_name] = {
                    "status": "ok",
                    "container_id": container.short_id,
                    "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                    "state": container.status,
                    "cpu_percent": calculate_container_cpu_percent(container_stats),
                    "memory": get_container_memory_stats(container_stats.get("memory_stats", {})),
                }
            except docker.errors.NotFound:
                stats[container_name] = {"status": "not_found", "error": "Container not found"}
            except Exception as exc:
                stats[container_name] = {"status": "error", "error": str(exc)}

        return stats
    except Exception as exc:
        logging.error("Error connecting to Docker: %s", exc)
        return {"_collector": {"status": "error", "error": str(exc)}}


def get_directory_size_bytes(directory):
    commands = (
        (["du", "-sb", directory], 1),
        (["du", "-sk", directory], 1024),
    )

    last_error = "du failed"
    for command, multiplier in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.split()[0]) * multiplier
        last_error = result.stderr.strip() or last_error

    raise RuntimeError(last_error)


def get_directory_sizes():
    sizes = {}
    for directory in DIRS:
        try:
            if os.path.exists(directory):
                size_bytes = get_directory_size_bytes(directory)
                sizes[directory] = {
                    "status": "ok",
                    "bytes": size_bytes,
                    "size": human_bytes(size_bytes),
                }
            else:
                sizes[directory] = {"status": "not_found", "error": "Directory not found"}
        except Exception as exc:
            sizes[directory] = {"status": "error", "error": str(exc)}
    return sizes


def collect_metrics():
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp": now_utc(),
        "system": get_system_stats(),
        "containers": get_docker_stats(),
        "directories": get_directory_sizes(),
    }


def append_metrics_log(record):
    with METRICS_LOG.open("a", encoding="utf-8") as metrics_file:
        metrics_file.write(json.dumps(record, separators=(",", ":"), sort_keys=True))
        metrics_file.write("\n")

    logging.info("Metrics appended to %s", METRICS_LOG)
    return METRICS_LOG


def main():
    logger = setup_logging()
    logger.info("Starting Besu monitoring service")

    try:
        record = collect_metrics()
        log_file = append_metrics_log(record)
        logger.info("Metrics collected and appended to %s", log_file)
    except Exception as exc:
        logger.error("Error in monitoring service: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
