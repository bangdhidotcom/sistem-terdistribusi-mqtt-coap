"""MQTT publisher: menghasilkan pesan uji dengan ID, timestamp, dan payload."""
from __future__ import annotations

import argparse
import os
import time

import paho.mqtt.client as mqtt

from common.logging_conf import event_log
from common.schema import encode_message, make_message


def main() -> None:
    ap = argparse.ArgumentParser(description="MQTT publisher")
    ap.add_argument("--host", default=os.environ.get("MQTT_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", 1883)))
    ap.add_argument("--topic", default=os.environ.get("TOPIC_M2C", "iot/mqtt_to_coap"))
    ap.add_argument("--rate", type=float, default=10.0)
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--payload-file", default="data/payload_200kb.bin")
    ap.add_argument("--log-dir", default=os.environ.get("LOG_DIR", "data/raw"))
    ap.add_argument("--source", default="mqtt_publisher")
    args = ap.parse_args()

    with open(args.payload_file, "rb") as fh:
        payload = fh.read()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=args.source)
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()
    time.sleep(0.2)

    interval = 1.0 / args.rate if args.rate > 0 else 0.0
    start = time.time()
    for seq in range(1, args.count + 1):
        if args.duration and time.time() - start >= args.duration:
            break
        msg = make_message(args.source, seq, payload, "m2c")
        client.publish(args.topic, encode_message(msg), qos=0)
        event_log(os.path.join(args.log_dir, "mqtt_publisher.jsonl"), "PUBLISH",
                  id=msg["id"], seq=seq, direction="m2c",
                  extra={"topic": args.topic, "sent_ts": msg["sent_ts"],
                         "payload_size": len(payload)})
        if interval:
            time.sleep(interval)
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
