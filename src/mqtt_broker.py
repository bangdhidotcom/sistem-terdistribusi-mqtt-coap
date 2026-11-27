"""Broker MQTT 3.1.1 minimal (QoS 0/1) untuk keperluan eksperimen lokal.

Implementasi sengaja dibuat mandiri agar tidak bergantung pada daemon eksternal.
Peran ini tetap merupakan "MQTT broker" yang menerima PUBLISH dan meneruskan
ke subscriber melalui TCP, sesuai spesifikasi tugas.
"""
from __future__ import annotations

import argparse
import os
import socket
import socketserver
import struct
import threading
from typing import Dict, Set

from common.logging_conf import event_log

STATE_LOCK = threading.Lock()
SUBSCRIBERS: Dict[socket.socket, Set[str]] = {}


def _enc_str(value: str) -> bytes:
    raw = value.encode("utf-8")
    return struct.pack("!H", len(raw)) + raw


def _read_str(buf: bytes, offset: int) -> tuple[str, int]:
    if offset + 2 > len(buf):
        raise ValueError("string terpotong")
    n = struct.unpack("!H", buf[offset:offset + 2])[0]
    offset += 2
    return buf[offset:offset + n].decode("utf-8", "replace"), offset + n


def _read_packet(reader) -> tuple[int, bytes] | None:
    head = reader.read(1)
    if not head:
        return None
    multiplier, remaining = 1, 0
    while True:
        ch = reader.read(1)
        if not ch:
            return None
        b = ch[0]
        remaining += (b & 127) * multiplier
        if not b & 128:
            break
        multiplier *= 128
        if multiplier > 128 * 128 * 128:
            raise ValueError("remaining length terlalu besar")
    body = reader.read(remaining)
    if len(body) != remaining:
        return None
    return head[0], body


def _send(sock: socket.socket, data: bytes) -> None:
    try:
        sock.sendall(data)
    except OSError:
        pass


def _publish_to_subscribers(topic: str, payload: bytes) -> None:
    body = _enc_str(topic) + payload
    packet = bytes([0x30]) + _packet_len(body) + body
    with STATE_LOCK:
        targets = [(s, t) for s, t in SUBSCRIBERS.items()
                   if any(_matches(f, topic) for f in t)]
    for sock, _ in targets:
        _send(sock, packet)


def _matches(filter_: str, topic: str) -> bool:
    if filter_ == topic:
        return True
    if filter_ == "#":
        return True
    if filter_.endswith("/#"):
        return topic.startswith(filter_[:-2])
    if "+" in filter_:
        f = filter_.split("/")
        t = topic.split("/")
        if len(f) != len(t):
            return False
        return all(a == b or a == "+" for a, b in zip(f, t))
    return False


def _packet_len(body: bytes) -> bytes:
    out = bytearray()
    n = len(body)
    while True:
        b = n % 128
        n //= 128
        if n:
            out.append(b | 128)
        else:
            out.append(b)
            break
    return bytes(out)


class BrokerHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        with STATE_LOCK:
            SUBSCRIBERS[self.request] = set()
        try:
            while True:
                item = _read_packet(self.rfile)
                if item is None:
                    break
                head, body = item
                ptype = head >> 4
                if ptype == 1:  # CONNECT
                    _read_str(body, 0)
                    if len(body) < 10:
                        break
                    _send(self.request, bytes([0x20, 0x02, 0x00, 0x00]))
                elif ptype == 8:  # SUBSCRIBE
                    if len(body) < 2:
                        break
                    pid = body[:2]
                    off, codes = 2, bytearray()
                    while off < len(body):
                        topic, off = _read_str(body, off)
                        if off >= len(body):
                            break
                        codes.append(body[off])
                        off += 1
                        with STATE_LOCK:
                            SUBSCRIBERS.setdefault(self.request, set()).add(topic)
                    suback_body = pid + bytes(codes)
                    _send(self.request, bytes([0x90]) +
                          _packet_len(suback_body) + suback_body)
                elif ptype == 3:  # PUBLISH
                    topic, off = _read_str(body, 0)
                    qos = (head >> 1) & 3
                    if qos > 0 and off + 2 <= len(body):
                        pid = body[off:off + 2]
                        off += 2
                        _send(self.request, bytes([0x40, 0x02]) + pid)
                    _publish_to_subscribers(topic, body[off:])
                elif ptype == 12:  # PINGREQ
                    _send(self.request, bytes([0xD0, 0x00]))
                elif ptype == 14:  # DISCONNECT
                    break
        except (OSError, ValueError):
            pass
        finally:
            with STATE_LOCK:
                SUBSCRIBERS.pop(self.request, None)
            try:
                self.request.close()
            except OSError:
                pass


class Broker(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    ap = argparse.ArgumentParser(description="Broker MQTT lokal untuk eksperimen")
    ap.add_argument("--host", default=os.environ.get("MQTT_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", 1883)))
    ap.add_argument("--log", default=os.environ.get("LOG_DIR", "data/raw"))
    args = ap.parse_args()

    with Broker((args.host, args.port), BrokerHandler) as server:
        event_log(os.path.join(args.log, "mqtt_broker.jsonl"), "BROKER_READY",
                  host=args.host, port=args.port)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
