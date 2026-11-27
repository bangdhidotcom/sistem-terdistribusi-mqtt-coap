"""Ulangi run gagal (delivered=0 atau JSON hilang) setelah kampanye selesai."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PATTERN = re.compile(r"^(m2c|c2m)_r(\d+)_s(\d+)$")


def collect(direction: str) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for path in sorted(RAW.glob("run_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("status") != "ok" or data.get("delivered", 0) != 0:
            continue
        if direction != "both" and data.get("direction") != direction:
            continue
        found[data["run_id"]] = data
    # Pulihkan run yang JSON-nya terhapus saat proses sebelumnya terputus.
    for folder in sorted(RAW.iterdir()):
        if not folder.is_dir():
            continue
        m = PATTERN.match(folder.name)
        if not m:
            continue
        run_id = folder.name
        if (RAW / f"run_{run_id}.json").exists() or run_id in found:
            continue
        d, rate, rep = m.group(1), int(m.group(2)), int(m.group(3))
        if direction != "both" and d != direction:
            continue
        found[run_id] = {"run_id": run_id, "direction": d, "rate": rate,
                         "rep": rep, "duration": 600, "payload_size": 4096}
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", choices=["both", "m2c", "c2m"], default="both")
    args = ap.parse_args()
    failed = collect(args.direction)
    print(f"[{args.direction}] run gagal ditemukan: {len(failed)}", flush=True)
    for run_id, data in failed.items():
        shutil.rmtree(RAW / run_id, ignore_errors=True)
        (RAW / f"run_{run_id}.json").unlink(missing_ok=True)
        cmd = [sys.executable, str(ROOT / "experiments" / "run_matrix.py"),
               "--direction", data["direction"], "--rate", str(data["rate"]),
               "--duration", str(data["duration"]), "--reps", str(data["rep"]),
               "--start-rep", str(data["rep"]),
               "--payload-size", str(data.get("payload_size", 4096))]
        print("rerun", " ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=str(ROOT), check=True)
    done = ROOT / "data" / f"rerun_done_{args.direction}.txt"
    done.write_text(f"RERUN_DONE direction={args.direction} count={len(failed)}",
                    encoding="utf-8")
    print("Selesai:", done.read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    main()
