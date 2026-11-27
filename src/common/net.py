"""Utilitas konektivitas dan retry untuk proses lokal."""
from __future__ import annotations

import socket
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def now() -> float:
    return time.time()


def wait_for_tcp(host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def wait_for_udp(host: str, port: int, timeout: float = 20.0) -> bool:
    """UDP tidak punya koneksi; cukup pastikan port bisa di-bind pada host lokal."""
    if host not in ("127.0.0.1", "localhost", "0.0.0.0"):
        return True
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind((host, port))
            return True
        except OSError:
            time.sleep(0.2)
    return False


def retry(fn: Callable[[], T], attempts: int = 5, delay: float = 0.5) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - sengaja dicoba ulang
            last = exc
            time.sleep(delay * (2 ** i))
    raise last if last else RuntimeError("retry gagal")
