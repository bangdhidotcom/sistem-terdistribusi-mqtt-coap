"""CoAP client: POST ke /source (c2m) dan GET /target untuk verifikasi (m2c)."""
from __future__ import annotations

import argparse
import asyncio
import os
import time

import aiocoap

from common.logging_conf import event_log
from common.schema import (decode_message, encode_message, make_message, now,
                           payload_of, sha256_of, validate_message)


async def _respond(context, req, timeout: float = 2.0):
    """Retry cepat dengan timeout agar satu request gagal tidak memblokir laju."""
    for attempt in range(3):
        try:
            return await asyncio.wait_for(context.request(req).response,
                                          timeout=timeout)
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(0.05 * (2 ** attempt))


async def do_post(args, payload: bytes) -> None:
    context = await aiocoap.Context.create_client_context()
    uri = f"coap://{args.host}:{args.port}/source"
    interval = 1.0 / args.rate if args.rate > 0 else 0.0
    start = time.time()
    try:
        for seq in range(1, args.count + 1):
            if args.duration and time.time() - start >= args.duration:
                break
            msg = make_message(args.source, seq, payload, "c2m")
            req = aiocoap.Message(code=aiocoap.Code.POST, uri=uri,
                                  payload=encode_message(msg))
            try:
                resp = await _respond(context, req)
            except Exception as exc:  # noqa: BLE001
                event_log(os.path.join(args.log_dir, "coap_client.jsonl"), "ERROR",
                          id=msg["id"], seq=seq, direction="c2m",
                          extra={"reason": f"POST gagal: {exc}"})
                if interval:
                    await asyncio.sleep(interval)
                continue
            if not resp.code.is_successful():
                event_log(os.path.join(args.log_dir, "coap_client.jsonl"), "ERROR",
                          id=msg["id"], extra={"reason": f"POST {resp.code}"})
            else:
                event_log(os.path.join(args.log_dir, "coap_client.jsonl"), "POST",
                          id=msg["id"], seq=seq, direction="c2m",
                          extra={"resource": "/source",
                                 "sent_ts": msg["sent_ts"],
                                 "payload_size": len(payload)})
            if interval:
                await asyncio.sleep(interval)
    finally:
        await context.shutdown()


async def do_get(args) -> None:
    context = await aiocoap.Context.create_client_context()
    uri = f"coap://{args.host}:{args.port}/target"
    seen: set[str] = set()
    start = time.time()
    try:
        while True:
            if args.duration and time.time() - start >= args.duration:
                break
            if args.count and len(seen) >= args.count:
                break
            req = aiocoap.Message(code=aiocoap.Code.GET, uri=uri)
            try:
                resp = await _respond(context, req, timeout=8.0)
            except Exception as exc:  # noqa: BLE001
                event_log(os.path.join(args.log_dir, "coap_client.jsonl"), "ERROR",
                          extra={"reason": f"GET gagal: {exc}"})
                await asyncio.sleep(0.5)
                continue
            if resp.code == aiocoap.Code.NOT_FOUND or not resp.payload:
                await asyncio.sleep(0.05)
                continue
            try:
                decoded = decode_message(resp.payload)
            except Exception:  # noqa: BLE001
                await asyncio.sleep(0.05)
                continue
            messages = decoded if isinstance(decoded, list) else [decoded]
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                mid = msg.get("id")
                if not mid or mid in seen or validate_message(msg):
                    continue
                seen.add(mid)
                recv_ts = now()
                msg["meta"]["dst_recv_ts"] = recv_ts
                ok = sha256_of(payload_of(msg)) == msg["payload_sha256"]
                latency = (recv_ts - float(msg["sent_ts"])) * 1000.0
                event_log(os.path.join(args.log_dir, "coap_client.jsonl"), "DELIVER",
                          id=mid, seq=msg["seq"], direction="m2c", latency_ms=latency,
                          extra={"verified": ok, "resource": "/target",
                                 "dst_recv_ts": recv_ts, "sent_ts": msg["sent_ts"]})
            await asyncio.sleep(0.05)
    finally:
        await context.shutdown()


def main() -> None:
    ap = argparse.ArgumentParser(description="CoAP POST/GET client")
    ap.add_argument("--mode", choices=["post", "get"], required=True)
    ap.add_argument("--host", default=os.environ.get("COAP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("COAP_PORT", 5683)))
    ap.add_argument("--rate", type=float, default=10.0)
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--payload-file", default="data/payload_200kb.bin")
    ap.add_argument("--log-dir", default=os.environ.get("LOG_DIR", "data/raw"))
    ap.add_argument("--source", default="coap_client")
    args = ap.parse_args()
    if args.mode == "get":
        asyncio.run(do_get(args))
    else:
        with open(args.payload_file, "rb") as fh:
            payload = fh.read()
        asyncio.run(do_post(args, payload))


if __name__ == "__main__":
    main()
