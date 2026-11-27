"""Ringkasan hasil eksperimen: CSV mentah per pesan + CSV ringkasan per menit."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def _events():
    for path in sorted(RAW.rglob("*.jsonl")):
        run = path.parent.relative_to(RAW).as_posix() if path.parent != RAW else "main"
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rec["_run"] = run
                rec["_file"] = path.name
                yield rec


def _p95(values):
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, math.ceil(0.95 * len(s)) - 1)
    return s[idx]


def main() -> None:
    global RAW
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(RAW))
    args = ap.parse_args()
    raw_root = Path(args.raw)
    RAW = raw_root

    records = list(_events())
    by_id: dict[str, dict] = {}
    for rec in records:
        mid = rec.get("id")
        if not mid:
            continue
        row = by_id.setdefault(mid, {
            "id": mid, "seq": rec.get("seq"), "direction": rec.get("direction") or "",
            "run": rec["_run"], "sent_ts": None, "conv_in": None, "conv_out": None,
            "dst_recv_ts": None, "delivered": False, "payload_sha256": "",
        })
        extra = rec.get("extra") or {}
        ev = rec["event"]
        if ev in ("PUBLISH", "POST") and extra.get("sent_ts"):
            row["sent_ts"] = float(extra["sent_ts"])
            row["direction"] = rec.get("direction") or row["direction"]
        elif ev == "CONV_IN":
            row["conv_in"] = float(rec["ts"])
            row["direction"] = rec.get("direction") or row["direction"]
        elif ev == "CONV_OUT":
            row["conv_out"] = float(rec["ts"])
        elif ev == "DELIVER":
            row["dst_recv_ts"] = float(extra.get("dst_recv_ts", rec["ts"]))
            row["delivered"] = True
            row["direction"] = rec.get("direction") or row["direction"]

    rows = []
    for row in by_id.values():
        sent = row["sent_ts"]
        conv = ((row["conv_out"] - row["conv_in"]) * 1000.0
                if row["conv_out"] and row["conv_in"] else None)
        e2e = ((row["dst_recv_ts"] - sent) * 1000.0
               if row["dst_recv_ts"] and sent else None)
        rows.append({**row, "conversion_delay_ms": conv, "e2e_delay_ms": e2e})

    messages_path = raw_root / "messages.csv"
    with messages_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "seq", "direction", "run", "sent_ts",
                                           "conv_in", "conv_out", "dst_recv_ts",
                                           "delivered", "conversion_delay_ms",
                                           "e2e_delay_ms", "payload_sha256"])
        w.writeheader()
        w.writerows(rows)

    # Ringkasan per run / arah / menit
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if row["sent_ts"] is None:
            continue
        minute = int((row["sent_ts"] // 60) % 60) + 1
        m = re.search(r"r(\d+)", row["run"])
        rate = int(m.group(1)) if m else 0
        groups[(row["run"], row["direction"] or "?", rate, minute)].append(row)

    cpu_by_run: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for path in sorted(raw_root.rglob("cpu.csv")):
        run = path.parent.relative_to(raw_root).as_posix()
        with path.open(encoding="utf-8") as fh:
            for r in csv.reader(fh):
                if len(r) >= 3:
                    try:
                        cpu_by_run[run].append((float(r[0]), float(r[1]), float(r[2])))
                    except ValueError:
                        pass

    summary_path = ROOT / "data" / "summary" / "summary.csv"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for (run, direction, rate, minute), items in sorted(groups.items()):
        delivered = [r for r in items if r["delivered"]]
        conv = [r["conversion_delay_ms"] for r in delivered
                if r["conversion_delay_ms"] is not None]
        e2e = [r["e2e_delay_ms"] for r in delivered if r["e2e_delay_ms"] is not None]
        cpu = [c[1] for c in cpu_by_run.get(run, [])]
        mem = [c[2] for c in cpu_by_run.get(run, [])]
        summary_rows.append({
            "run": run, "direction": direction, "rate": rate, "minute": minute,
            "sent": len(items), "received": len(delivered),
            "success_pct": round(100.0 * len(delivered) / len(items), 3),
            "loss_pct": round(100.0 * (len(items) - len(delivered)) / len(items), 3),
            "avg_conversion_ms": round(sum(conv) / len(conv), 3) if conv else 0.0,
            "p95_conversion_ms": round(_p95(conv), 3),
            "avg_e2e_ms": round(sum(e2e) / len(e2e), 3) if e2e else 0.0,
            "p95_e2e_ms": round(_p95(e2e), 3),
            "avg_cpu": round(sum(cpu) / len(cpu), 3) if cpu else 0.0,
            "p95_cpu": round(_p95(cpu), 3),
            "peak_cpu": round(max(cpu), 3) if cpu else 0.0,
            "avg_mem_mb": round(sum(mem) / len(mem), 3) if mem else 0.0,
            "p95_mem_mb": round(_p95(mem), 3) if mem else 0.0,
            "peak_mem_mb": round(max(mem), 3) if mem else 0.0,
        })
    # Run yang gagal total tidak punya event PUBLISH/POST, tetap dicatat.
    existing = {r["run"] for r in summary_rows}
    for path in sorted(raw_root.glob("run_*.json")):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        run = meta.get("run_id", path.stem[4:])
        if run in existing:
            continue
        cpu = [c[1] for c in cpu_by_run.get(run, [])]
        mem = [c[2] for c in cpu_by_run.get(run, [])]
        summary_rows.append({
            "run": run, "direction": meta.get("direction", "?"),
            "rate": int(meta.get("rate", 0)), "minute": 0,
            "sent": 0, "received": 0, "success_pct": 0.0, "loss_pct": 0.0,
            "avg_conversion_ms": 0.0, "p95_conversion_ms": 0.0,
            "avg_e2e_ms": 0.0, "p95_e2e_ms": 0.0,
            "avg_cpu": round(sum(cpu) / len(cpu), 3) if cpu else 0.0,
            "p95_cpu": round(_p95(cpu), 3),
            "peak_cpu": round(max(cpu), 3) if cpu else 0.0,
            "avg_mem_mb": round(sum(mem) / len(mem), 3) if mem else 0.0,
            "p95_mem_mb": round(_p95(mem), 3) if mem else 0.0,
            "peak_mem_mb": round(max(mem), 3) if mem else 0.0,
        })
        existing.add(run)

    with summary_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary_rows[0]) if summary_rows else
                           ["run", "direction", "rate", "minute"])
        w.writeheader()
        w.writerows(summary_rows)

    metrics = {
        "total_messages": len(rows),
        "total_delivered": sum(1 for r in rows if r["delivered"]),
        "overall_success_pct": round(100.0 * sum(1 for r in rows if r["delivered"])
                                     / len(rows), 3) if rows else 0.0,
        "runs": len(set(r["run"] for r in rows)),
    }
    (ROOT / "data" / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"messages.csv: {len(rows)} baris; summary.csv: {len(summary_rows)} baris")


if __name__ == "__main__":
    main()
