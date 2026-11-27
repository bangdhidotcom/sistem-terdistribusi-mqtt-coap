"""CoAP server dengan resource /target dan /source.

Setiap POST menambah pesan ke antrean. GET mengembalikan seluruh pesan
yang belum diambil sebagai JSON array, sehingga tidak ada pesan yang
tertindih antar polling 1 detik.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

import aiocoap
from aiocoap import Code, Message
from aiocoap.resource import Resource, Site

from common.logging_conf import event_log
from common.schema import decode_message, now, validate_message

STATE: dict[str, list[dict[str, Any]]] = {"target": [], "source": []}
LOG_DIR = "data/raw"
TARGET_GET_MAX = int(os.environ.get("COAP_TARGET_GET_MAX", "2"))
SOURCE_GET_MAX = int(os.environ.get("COAP_SOURCE_GET_MAX", "200"))


def _reply_bad(detail: str) -> Message:
    return Message(code=Code.BAD_REQUEST, payload=detail.encode("utf-8"))


class TargetResource(Resource):
    """Tujuan akhir alur MQTT -> CoAP (POST)."""

    async def render_post(self, request: Message) -> Message:
        try:
            msg = decode_message(request.payload)
        except Exception as exc:
            return _reply_bad(f"json rusak: {exc}")
        errors = validate_message(msg)
        if errors:
            return _reply_bad("; ".join(errors))
        msg["meta"]["dst_recv_ts"] = now()
        STATE["target"].append(msg)
        event_log(os.path.join(LOG_DIR, "coap_server.jsonl"), "POST_OK",
                  id=msg["id"], seq=msg["seq"], direction=msg["direction"],
                  extra={"resource": "/target", "size": len(request.payload)})
        return Message(code=Code.CHANGED, payload=b"OK")

    async def render_get(self, request: Message) -> Message:
        msgs = STATE["target"][:TARGET_GET_MAX]
        if not msgs:
            return Message(code=Code.NOT_FOUND, payload=b"empty")
        STATE["target"] = STATE["target"][TARGET_GET_MAX:]
        event_log(os.path.join(LOG_DIR, "coap_server.jsonl"), "GET_OK",
                  count=len(msgs), extra={"resource": "/target"})
        return Message(payload=json.dumps(msgs, separators=(",", ":")).encode("utf-8"))


class SourceResource(Resource):
    """Sumber alur CoAP -> MQTT (POST/PUT menulis, GET dibaca converter)."""

    async def render_post(self, request: Message) -> Message:
        return await self._store(request)

    async def render_put(self, request: Message) -> Message:
        return await self._store(request)

    async def _store(self, request: Message) -> Message:
        try:
            msg = decode_message(request.payload)
        except Exception as exc:
            return _reply_bad(f"json rusak: {exc}")
        errors = validate_message(msg)
        if errors:
            return _reply_bad("; ".join(errors))
        msg["meta"]["dst_recv_ts"] = now()
        STATE["source"].append(msg)
        event_log(os.path.join(LOG_DIR, "coap_server.jsonl"), "POST_OK",
                  id=msg["id"], seq=msg["seq"], direction=msg["direction"],
                  extra={"resource": "/source", "size": len(request.payload)})
        return Message(code=Code.CHANGED, payload=b"OK")

    async def render_get(self, request: Message) -> Message:
        msgs = STATE["source"][:SOURCE_GET_MAX]
        if not msgs:
            return Message(code=Code.NOT_FOUND, payload=b"empty")
        STATE["source"] = STATE["source"][SOURCE_GET_MAX:]
        event_log(os.path.join(LOG_DIR, "coap_server.jsonl"), "GET_OK",
                  count=len(msgs), extra={"resource": "/source"})
        return Message(payload=json.dumps(msgs, separators=(",", ":")).encode("utf-8"))


async def serve(host: str, port: int) -> None:
    global LOG_DIR
    LOG_DIR = os.environ.get("LOG_DIR", "data/raw")
    site = Site()
    site.add_resource(("target",), TargetResource())
    site.add_resource(("source",), SourceResource())
    context = await aiocoap.Context.create_server_context(site, bind=(host, port))
    event_log(os.path.join(LOG_DIR, "coap_server.jsonl"), "COAP_READY",
              host=host, port=port)
    try:
        await asyncio.Event().wait()
    finally:
        await context.shutdown()


def main() -> None:
    ap = argparse.ArgumentParser(description="CoAP server untuk eksperimen")
    ap.add_argument("--host", default=os.environ.get("COAP_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("COAP_PORT", 5683)))
    args = ap.parse_args()
    asyncio.run(serve(args.host, args.port))


if __name__ == "__main__":
    main()
