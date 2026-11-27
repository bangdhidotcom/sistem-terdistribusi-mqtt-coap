"""Grafik wajib analisis hasil eksperimen."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "data" / "summary" / "summary.csv"
OUT = ROOT / "data" / "grafik"
OUT.mkdir(parents=True, exist_ok=True)

ARTICLE = {
    ("m2c", 10): (52.43407, 52.9, 0.0),
    ("m2c", 20): (53.11167, 53.5, 0.0),
    ("c2m", 10): (0.179852, 0.1, 92.53731),
    ("c2m", 20): (0.182637, 0.1, 95.52239),
}


def _load() -> pd.DataFrame:
    if not SUMMARY.exists():
        return pd.DataFrame()
    return pd.read_csv(SUMMARY)


def _save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150)
    plt.close(fig)


def main() -> None:
    df = _load()
    if df.empty:
        print("summary.csv kosong; grafik tidak dibuat.")
        return
    for col, fname, title, ylabel in [
        ("avg_e2e_ms", "delay_e2e_per_menit.png",
         "Rerata Delay Ujung-ke-Ujung per Menit", "Delay (ms)"),
        ("avg_conversion_ms", "delay_konversi_per_menit.png",
         "Rerata Delay Konversi per Menit", "Delay (ms)"),
        ("avg_cpu", "cpu_per_menit.png",
         "Rerata CPU Conversion Server per Menit", "CPU (%)"),
    ]:
        fig, ax = plt.subplots(figsize=(9, 5))
        grouped = df.groupby(["direction", "rate", "minute"])[col].mean().reset_index()
        for (direction, rate), sub in grouped.groupby(["direction", "rate"]):
            ax.plot(sub["minute"], sub[col], marker="o",
                    label=f"{direction.upper()} {rate} msg/s")
        ax.set_title(title)
        ax.set_xlabel("Menit ke-")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend()
        _save(fig, fname)

    rows, labels = [], []
    for (direction, rate), (delay, rtt, loss) in ARTICLE.items():
        sub = df[(df["direction"] == direction) & (df["rate"] == rate)]
        if sub.empty:
            continue
        rows.append([sub["avg_e2e_ms"].mean(), delay])
        labels.append(f"{direction.upper()}\n{rate}/s")
    if rows:
        import numpy as np
        arr = np.array(rows)
        fig, ax = plt.subplots(figsize=(8, 5))
        x = np.arange(len(labels))
        ax.bar(x - 0.2, arr[:, 0], 0.4, label="Replikasi (delay ms)")
        ax.bar(x + 0.2, arr[:, 1], 0.4, label="Artikel (delay s, skala berbeda)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title("Perbandingan Delay dengan Artikel Acuan")
        ax.set_ylabel("Nilai numerik (perhatikan beda satuan)")
        ax.legend()
        ax.grid(alpha=0.3, axis="y")
        _save(fig, "perbandingan_artikel.png")
    print(f"Grafik tersimpan di {OUT}")


if __name__ == "__main__":
    main()
