"""Orkestrator matriks eksperimen R1/R2.

Menjalankan enam peran logis sebagai proses terpisah untuk setiap kombinasi
(arah, laju, pengulangan) selama `duration` detik, lalu menyimpan ringkasan
per run. Aman di-resume: run dengan JSON valid dilewati.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
PORTS = {"m2c": {"mqtt": 1883, "coap": 5683},
         "c2m": {"mqtt": 1884, "coap": 5684}}


def _spawn(script: str, args: list[str], env: dict[str, str], log_path: Path):
    fh = log_path.open("a", encoding="utf-8")
    proc = subprocess.Popen([PY, str(ROOT / "src" / script), *args],
                            cwd=str(ROOT), env=env,
                            stdout=fh, stderr=subprocess.STDOUT)
    return proc, fh


def _wait_ready(log_dir: Path, timeout: float = 40.0) -> bool:
    checks = [("mqtt_broker.jsonl", "BROKER_READY"),
              ("coap_server.jsonl", "COAP_READY"),
              ("conversion_server.jsonl", "CONV_READY")]
    deadline = time.time() + timeout
    while time.time() < deadline:
        ok = True
        for name, marker in checks:
            p = log_dir / name
            if not p.exists() or marker not in p.read_text(encoding="utf-8", errors="ignore"):
                ok = False
                break
        if ok:
            return True
        time.sleep(0.5)
    return False


def _count_delivered(log_dir: Path) -> int:
    total = 0
    for name in ("mqtt_subscriber.jsonl", "coap_client.jsonl"):
        p = log_dir / name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                if json.loads(line).get("event") == "DELIVER":
                    total += 1
            except json.JSONDecodeError:
                pass
    return total


def run_one(direction: str, rate: int, rep: int, duration: int,
            payload_size: int, timeout: int) -> dict:
    run_id = f"{direction}_r{rate}_s{rep:02d}"
    log_rel = f"data/raw/{run_id}"
    log_dir = ROOT / log_rel
    log_dir.mkdir(parents=True, exist_ok=True)
    out_json = ROOT / "data" / "raw" / f"run_{run_id}.json"
    if out_json.exists():
        try:
            data = json.loads(out_json.read_text(encoding="utf-8"))
            if data.get("status") in ("ok", "smoke-ok"):
                return data
        except json.JSONDecodeError:
            pass

    env = os.environ.copy()
    env.update({
        "MQTT_HOST": "127.0.0.1", "MQTT_PORT": str(PORTS[direction]["mqtt"]),
        "COAP_HOST": "127.0.0.1", "COAP_PORT": str(PORTS[direction]["coap"]),
        "TOPIC_M2C": "iot/mqtt_to_coap", "TOPIC_C2M": "iot/coap_to_mqtt",
        "LOG_DIR": log_rel, "PYTHONUNBUFFERED": "1", "COAP_GET_MAX": "50",
    })
    payload_file = ROOT / "data" / f"payload_{payload_size}.bin"
    if not payload_file.exists():
        subprocess.run([PY, str(ROOT / "experiments" / "payload_gen.py"),
                        "--size", str(payload_size),
                        "--out", f"data/payload_{payload_size}.bin"],
                       cwd=str(ROOT), check=True)

    procs, handles = [], []

    def start(script: str, args: list[str]) -> None:
        proc, fh = _spawn(script, args, env, log_dir / "processes.log")
        procs.append(proc)
        handles.append(fh)

    start("mqtt_broker.py", [])
    start("coap_server.py", [])
    time.sleep(0.5)
    start("conversion_server.py", [])
    start("mqtt_subscriber.py", ["--duration", str(duration + 15)])
    if direction == "m2c":
        start("coap_client.py", ["--mode", "get", "--count", "1000000", "--duration", str(duration + 5)])
        start("mqtt_publisher.py", ["--rate", str(rate), "--count", "1000000",
                                    "--duration", str(duration),
                                    "--payload-file", f"data/payload_{payload_size}.bin"])
    else:
        start("coap_client.py", ["--mode", "post", "--rate", str(rate),
                                 "--count", "1000000", "--duration", str(duration),
                                 "--payload-file", f"data/payload_{payload_size}.bin"])

    ready = _wait_ready(log_dir)
    result = {
        "run_id": run_id, "direction": direction, "rate": rate, "rep": rep,
        "duration": duration, "payload_size": payload_size,
        "ready": ready, "delivered": 0, "status": "ok" if ready else "not-ready",
        "ports": PORTS[direction], "finished_at": time.time(),
    }
    if ready:
        time.sleep(duration)
        result["delivered"] = _count_delivered(log_dir)
    for proc in reversed(procs):
        if proc.poll() is None:
            proc.terminate()
    for proc in reversed(procs):
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    for fh in handles:
        fh.close()
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", default="10,20")
    ap.add_argument("--duration", type=int, default=600)
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--direction", choices=["both", "m2c", "c2m"], default="both")
    ap.add_argument("--payload-size", type=int, default=204800)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--start-rep", type=int, default=1)
    args = ap.parse_args()
    rates = [int(x) for x in args.rate.split(",")]
    dirs = ["m2c", "c2m"] if args.direction == "both" else [args.direction]
    for direction in dirs:
        for rate in rates:
            for rep in range(args.start_rep, args.reps + 1):
                r = run_one(direction, rate, rep, args.duration,
                            args.payload_size, args.timeout)
                print(json.dumps(r, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
