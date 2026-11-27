"""Pembuat payload 200 KB.

Spesifikasi menyarankan scapy packet generator. Di sini scapy dipakai untuk
membangun byte payload (Raw) tanpa mengirim paket jaringan apa pun.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_payload(size: int) -> bytes:
    try:
        from scapy.packet import Raw
        chunk = bytes(Raw(load=(b"MQTT-CoAP-" + os.urandom(1022))))
        payload = (chunk * ((size // len(chunk)) + 1))[:size]
    except Exception:
        block = b"MQTT-CoAP-" + os.urandom(1022)
        payload = (block * ((size // len(block)) + 1))[:size]
    return payload


def main() -> None:
    ap = argparse.ArgumentParser(description="Generator payload eksperimen")
    ap.add_argument("--size", type=int, default=204800)
    ap.add_argument("--out", default="data/payload_200kb.bin")
    args = ap.parse_args()
    if args.size > 65500:
        print("Info: payload melebihi MTU CoAP; aiocoap blockwise akan dipakai.")
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build_payload(args.size)
    out.write_bytes(data)
    print(f"Payload {len(data)} byte ditulis ke {out}")


if __name__ == "__main__":
    main()
