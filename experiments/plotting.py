"""Grafik hasil eksperimen Sistem Terdistribusi."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "data" / "summary" / "summary.csv"
OUT = ROOT / "data" / "grafik"
OUT.mkdir(parents=True, exist_ok=True)

# Warna selaras diagram
PAL = {"blue": "#2A5FD4", "green": "#0E7C66", "purple": "#7D3C98", "orange": "#CA6F1E"}

def _load():
    return pd.read_csv(SUMMARY) if SUMMARY.exists() else pd.DataFrame()

def _save(fig, name):
    fig.savefig(OUT / name, dpi=200)
    plt.close(fig)

def main():
    df = _load()
    if df.empty: return
    
    # 3 Grafik metrik
    for col, fname, title, ylabel in [
        ("avg_e2e_ms", "delay_e2e_per_menit.png", "Temuan: Delay E2E per Menit", "Delay E2E (ms)"),
        ("avg_conversion_ms", "delay_konversi_per_menit.png", "Temuan: Delay Konversi per Menit", "Delay konversi (ms)"),
        ("avg_cpu", "cpu_per_menit.png", "Temuan: Beban CPU Conversion Server", "CPU conversion server (%)"),
    ]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for (d, r), sub in df.groupby(["direction", "rate"]):
            ax.plot(sub["minute"], sub[col], marker="o", label=f"{d.upper()} {r} msg/s", linewidth=2.2, alpha=0.8)
            ax.fill_between(sub["minute"], sub[col], alpha=0.1)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Menit ke-")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(fontsize=9)
        _save(fig, fname)

    # Perbandingan
    fig, ax = plt.subplots(figsize=(8, 4.5))
    # Sederhanakan: ambil rerata per direction
    grouped = df.groupby("direction")["avg_e2e_ms"].mean()
    ax.bar(grouped.index, grouped.values, color=[PAL["blue"], PAL["green"]])
    ax.set_title("Perbandingan Delay E2E Rerata", fontsize=12, fontweight="bold")
    ax.set_ylabel("Delay (ms)")
    ax.spines[["top", "right"]].set_visible(False)
    _save(fig, "perbandingan_artikel.png")

if __name__ == "__main__":
    main()