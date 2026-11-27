"""Logging terstruktur JSONL untuk seluruh komponen."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
_LOCK = threading.Lock()


def ensure_dirs() -> None:
    for p in (DATA_DIR, RAW_DIR, DATA_DIR / "summary", DATA_DIR / "grafik",
              DATA_DIR / "bukti_konektivitas"):
        p.mkdir(parents=True, exist_ok=True)


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def event_log(path: str | Path, event: str, **fields: Any) -> None:
    """Tulis satu baris event ke file JSONL (thread-safe)."""
    ensure_dirs()
    record = {"ts": __import__("time").time(), "event": event}
    record.update(fields)
    target = resolve(path)
    line = json.dumps(record, separators=(",", ":"), ensure_ascii=False, default=str)
    with _LOCK:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
