"""Conversion server: jembatan dua arah MQTT <-> CoAP.

Arah m2c : MQTT subscriber -> CoAP POST /target
Arah c2m : CoAP GET /source (polling 1 detik) -> MQTT publisher

Catatan definisi: spesifikasi menuliskan "delay konversi = waktu penerimaan
sebelum konversi dikurangi waktu setelah konversi", yang secara harfiah negatif.
Implementasi memakai konvensi konsisten: conv_send_ts - conv_recv_ts, dan
penjelasan ini dicantumkan di laporan.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import os
import time
from collections import deque

import aiocoap
import paho.mqtt.client as mqtt
import psutil

from common.logging_conf import event_log
from common.schema import (decode_message, encode_message, mark_processed,
                           now, set_ts, validate_message)


class ConversionServer:
    def __init__(self, mqtt_host: str, mqtt_port: int, coap_host: str,
                 coap_port: int, topic_m2c: str, topic_c2m: str,
                 log_dir: str) -> None:
        self.mqtt_host, self.mqtt_port = mqtt_host, mqtt_port
        self.coap_host, self.coap_port = coap_host, coap_port
        self.topic_m2c, self.topic_c2m = topic_m2c, topic_c2m
        self.log_dir = log_dir
        self.seen: deque[str] = deque(maxlen=5000)
        self.seen_set: set[str] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.context: aiocoap.Context | None = None
        self.client: mqtt.Client | None = None
        self._proc = psutil.Process()

    # ---------- MQTT ----------
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        # paho 2.x bisa memberikan ReasonCode, int, atau bool tergantung versi.
        rc_value = getattr(reason_code, "value", reason_code)
        if rc_value:
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "ERROR", extra={"reason": "mqtt connect gagal", "rc": str(reason_code)})
            return
        client.subscribe([(self.topic_m2c, 0), (self.topic_c2m, 0)])
        event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                  "CONV_READY", extra={"subscribed": [self.topic_m2c, self.topic_c2m]})

    def _on_message(self, client, userdata, message: mqtt.MQTTMessage):
        if message.topic != self.topic_m2c:
            return
        try:
            msg = decode_message(message.payload)
        except Exception as exc:  # noqa: BLE001
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "ERROR", extra={"reason": f"decode gagal: {exc}"})
            return
        errors = validate_message(msg)
        if errors:
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "ERROR", id=msg.get("id"), extra={"errors": errors})
            return
        if msg.get("meta", {}).get("origin_processed"):
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "SKIP_LOOP", id=msg["id"])
            return
        set_ts(msg, "conv_recv_ts")
        mark_processed(msg)
        event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                  "CONV_IN", id=msg["id"], seq=msg["seq"], direction="m2c")
        assert self.loop is not None
        fut = asyncio.run_coroutine_threadsafe(self._post_target(msg), self.loop)
        try:
            fut.result(timeout=30)
        except Exception as exc:  # noqa: BLE001
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "ERROR", id=msg["id"], extra={"reason": f"POST gagal: {exc}"})

    def _start_mqtt(self) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                  client_id="conversion_server")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        self.client.connect_async(self.mqtt_host, self.mqtt_port, keepalive=60)
        self.client.loop_start()

    # ---------- CoAP ----------
    @staticmethod
    async def _respond(context, req, timeout: float = 3.0):
        """Retry cepat dengan timeout untuk request CoAP blockwise."""
        for attempt in range(3):
            try:
                return await asyncio.wait_for(context.request(req).response,
                                              timeout=timeout)
            except Exception:
                if attempt == 2:
                    raise
                await asyncio.sleep(0.05 * (2 ** attempt))

    async def _post_target(self, msg: dict) -> None:
        assert self.context is not None
        uri = f"coap://{self.coap_host}:{self.coap_port}/target"
        req = aiocoap.Message(code=aiocoap.Code.POST, uri=uri,
                              payload=encode_message(msg))
        resp = await self._respond(self.context, req)
        if resp.code.is_successful() is False:
            raise RuntimeError(f"CoAP POST respons {resp.code}: {resp.payload[:120]!r}")
        set_ts(msg, "conv_send_ts")
        event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                  "CONV_OUT", id=msg["id"], seq=msg["seq"], direction="m2c",
                  extra={"response": str(resp.code)})

    async def _poll_source(self) -> None:
        assert self.context is not None and self.client is not None
        uri = f"coap://{self.coap_host}:{self.coap_port}/source"
        req = aiocoap.Message(code=aiocoap.Code.GET, uri=uri)
        try:
            resp = await self._respond(self.context, req)
        except Exception as exc:  # noqa: BLE001
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "ERROR", extra={"reason": f"GET source gagal: {exc}"})
            return
        if resp.code == aiocoap.Code.NOT_FOUND or not resp.payload:
            return
        try:
            decoded = decode_message(resp.payload)
        except Exception:  # noqa: BLE001
            return
        messages = decoded if isinstance(decoded, list) else [decoded]
        for msg in messages:
            if not isinstance(msg, dict) or validate_message(msg):
                continue
            mid = msg["id"]
            if mid in self.seen_set:
                event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                          "SKIP_DUP", id=mid)
                continue
            if msg.get("meta", {}).get("origin_processed"):
                event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                          "SKIP_LOOP", id=mid)
                continue
            self.seen.append(mid)
            self.seen_set.add(mid)
            if len(self.seen_set) > 5000:
                self.seen_set.discard(self.seen.popleft())
            set_ts(msg, "conv_recv_ts")
            mark_processed(msg)
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "CONV_IN", id=mid, seq=msg["seq"], direction="c2m")
            info = self.client.publish(self.topic_c2m, encode_message(msg), qos=0)
            info.wait_for_publish(timeout=10)
            set_ts(msg, "conv_send_ts")
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "CONV_OUT", id=mid, seq=msg["seq"], direction="c2m",
                      extra={"response": "published"})
            event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                      "PUBLISH_OK", id=mid, direction="c2m")

    # ---------- CPU ----------
    async def _sample_cpu(self) -> None:
        path = os.path.join(self.log_dir, "cpu.csv")
        with open(path, "a", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            while True:
                writer.writerow([now(), self._proc.cpu_percent(interval=None),
                                 self._proc.memory_info().rss / (1024 * 1024)])
                fh.flush()
                await asyncio.sleep(1.0)

    async def run(self) -> None:
        self.loop = asyncio.get_running_loop()
        self.context = await aiocoap.Context.create_client_context()
        self._start_mqtt()
        event_log(os.path.join(self.log_dir, "conversion_server.jsonl"),
                  "CONV_READY", extra={"stage": "coap"})
        cpu_task = asyncio.create_task(self._sample_cpu())
        try:
            while True:
                await self._poll_source()
                await asyncio.sleep(1.0)
        finally:
            cpu_task.cancel()
            await self.context.shutdown()
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()


def main() -> None:
    ap = argparse.ArgumentParser(description="Conversion server MQTT <-> CoAP")
    ap.add_argument("--mqtt-host", default=os.environ.get("MQTT_HOST", "127.0.0.1"))
    ap.add_argument("--mqtt-port", type=int, default=int(os.environ.get("MQTT_PORT", 1883)))
    ap.add_argument("--coap-host", default=os.environ.get("COAP_HOST", "127.0.0.1"))
    ap.add_argument("--coap-port", type=int, default=int(os.environ.get("COAP_PORT", 5683)))
    ap.add_argument("--topic-m2c", default=os.environ.get("TOPIC_M2C", "iot/mqtt_to_coap"))
    ap.add_argument("--topic-c2m", default=os.environ.get("TOPIC_C2M", "iot/coap_to_mqtt"))
    ap.add_argument("--log-dir", default=os.environ.get("LOG_DIR", "data/raw"))
    args = ap.parse_args()
    server = ConversionServer(args.mqtt_host, args.mqtt_port, args.coap_host,
                              args.coap_port, args.topic_m2c, args.topic_c2m,
                              args.log_dir)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
