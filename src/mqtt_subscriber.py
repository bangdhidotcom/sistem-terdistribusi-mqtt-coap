"""MQTT subscriber: menerima hasil translasi dari sisi CoAP dan memverifikasinya."""
from __future__ import annotations

import argparse
import os
import time

import paho.mqtt.client as mqtt

from common.logging_conf import event_log
from common.schema import decode_message, now, payload_of, sha256_of, validate_message

SEEN: set[str] = set()


def main() -> None:
    ap = argparse.ArgumentParser(description="MQTT subscriber")
    ap.add_argument("--host", default=os.environ.get("MQTT_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", 1883)))
    ap.add_argument("--topic", default=os.environ.get("TOPIC_C2M", "iot/coap_to_mqtt"))
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--log-dir", default=os.environ.get("LOG_DIR", "data/raw"))
    args = ap.parse_args()

    def on_connect(client, userdata, flags, reason_code, properties=None):
        client.subscribe(args.topic, qos=0)

    def on_message(client, userdata, message: mqtt.MQTTMessage):
        try:
            msg = decode_message(message.payload)
        except Exception as exc:  # noqa: BLE001
            event_log(os.path.join(args.log_dir, "mqtt_subscriber.jsonl"), "ERROR",
                      extra={"reason": f"decode gagal: {exc}"})
            return
        errors = validate_message(msg)
        mid = msg.get("id")
        if mid in SEEN:
            event_log(os.path.join(args.log_dir, "mqtt_subscriber.jsonl"),
                      "SKIP_DUP", id=mid)
            return
        if errors:
            event_log(os.path.join(args.log_dir, "mqtt_subscriber.jsonl"), "ERROR",
                      id=mid, extra={"errors": errors})
            return
        SEEN.add(mid)
        recv_ts = now()
        msg["meta"]["dst_recv_ts"] = recv_ts
        ok = sha256_of(payload_of(msg)) == msg["payload_sha256"]
        latency = (recv_ts - float(msg["sent_ts"])) * 1000.0
        event_log(os.path.join(args.log_dir, "mqtt_subscriber.jsonl"), "DELIVER",
                  id=mid, seq=msg["seq"], direction="c2m", latency_ms=latency,
                  extra={"verified": ok, "topic": message.topic,
                         "dst_recv_ts": recv_ts, "sent_ts": msg["sent_ts"]})

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="mqtt_subscriber")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()
    if args.duration > 0:
        time.sleep(args.duration)
    else:
        while True:
            time.sleep(1)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
