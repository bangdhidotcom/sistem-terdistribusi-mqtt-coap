"""Skema pesan bersama untuk seluruh komponen konversi MQTT <-> CoAP.

Semua pesan direpresentasikan sebagai JSON dengan field tetap. Payload biner
dikodekan base64 agar aman melewati MQTT maupun CoAP.
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from typing import Any

VALID_DIRECTIONS = ("m2c", "c2m")


def now() -> float:
    """Epoch time dalam detik (semua proses berjalan di satu host)."""
    return time.time()


def sha256_of(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def make_message(source: str, seq: int, payload: bytes, direction: str,
                 extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """Buat pesan baru dengan ID unik, timestamp, dan hash payload."""
    if direction not in VALID_DIRECTIONS:
        raise ValueError(f"direction harus salah satu dari {VALID_DIRECTIONS}")
    meta: dict[str, Any] = {
        "origin_processed": False,
        "hops": [source],
        "conv_recv_ts": 0.0,
        "conv_send_ts": 0.0,
        "dst_recv_ts": 0.0,
    }
    if extra_meta:
        meta.update(extra_meta)
    return {
        "id": str(uuid.uuid4()),
        "seq": int(seq),
        "source": source,
        "sent_ts": now(),
        "payload": base64.b64encode(payload).decode("ascii"),
        "payload_sha256": sha256_of(payload),
        "direction": direction,
        "meta": meta,
    }


def encode_message(msg: dict[str, Any]) -> bytes:
    return json.dumps(msg, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_message(raw: bytes | str | bytearray) -> dict[str, Any]:
    if isinstance(raw, (bytes, bytearray)):
        raw = bytes(raw).decode("utf-8")
    return json.loads(raw)


def validate_message(msg: Any) -> list[str]:
    """Kembalikan daftar error; kosong berarti pesan valid."""
    errors: list[str] = []
    if not isinstance(msg, dict):
        return ["pesan bukan objek JSON"]
    for key in ("id", "seq", "source", "sent_ts", "payload",
                "payload_sha256", "direction", "meta"):
        if key not in msg:
            errors.append(f"field hilang: {key}")
    if errors:
        return errors
    if msg["direction"] not in VALID_DIRECTIONS:
        errors.append("direction tidak dikenal")
    if not isinstance(msg["meta"], dict):
        errors.append("meta bukan objek")
        return errors
    try:
        payload = payload_of(msg)
    except Exception as exc:
        errors.append(f"payload base64 rusak: {exc}")
        payload = b""
    if sha256_of(payload) != msg["payload_sha256"]:
        errors.append("payload_sha256 tidak cocok")
    return errors


def payload_of(msg: dict[str, Any]) -> bytes:
    return base64.b64decode(msg["payload"])


def mark_processed(msg: dict[str, Any]) -> dict[str, Any]:
    """Tandai pesan sudah dikonversi untuk mencegah loop balik."""
    msg.setdefault("meta", {})["origin_processed"] = True
    hops = msg["meta"].setdefault("hops", [])
    if "conversion_server" not in hops:
        hops.append("conversion_server")
    return msg


def set_ts(msg: dict[str, Any], key: str, ts: float | None = None) -> dict[str, Any]:
    msg.setdefault("meta", {})[key] = now() if ts is None else float(ts)
    return msg
