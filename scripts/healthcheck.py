"""Cek kesiapan port dan log READY."""
from __future__ import annotations

import os
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS = [(os.environ.get("MQTT_HOST", "127.0.0.1"),
           int(os.environ.get("MQTT_PORT", 1883)))]


def tcp_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def main() -> None:
    log_dir = ROOT / os.environ.get("LOG_DIR", "data/raw")
    for host, port in TOPICS:
        print(f"TCP {host}:{port} = {'READY' if tcp_open(host, port) else 'DOWN'}")
    for name, marker in [("mqtt_broker.jsonl", "BROKER_READY"),
                         ("coap_server.jsonl", "COAP_READY"),
                         ("conversion_server.jsonl", "CONV_READY")]:
        p = log_dir / name
        ok = p.exists() and marker in p.read_text(encoding="utf-8", errors="ignore")
        print(f"{name}: {marker} = {'OK' if ok else 'WAITING'}")


if __name__ == "__main__":
    main()
