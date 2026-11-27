"""Bangun 4 grafik sebagai shape DrawingML editabel + PNG preview identik.

Satu sumber data: data/summary/summary.csv. Sumbu x time-series memakai indeks
bucket 1..11 (600 detik melintang batas menit), BUKAN minute jam 1..60.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from vendor.jump2.uml_core import Diagram  # noqa: E402
from vendor.jump2.uml_drawml import to_drawingml  # noqa: E402
from vendor.jump2.uml_png import render_png  # noqa: E402
from vendor.jump2.uml_validate import validate, report_text_fit  # noqa: E402

SUMMARY = ROOT / "data" / "summary" / "summary.csv"
XML_DIR = ROOT / "output-xml"
PNG_DIR = ROOT / "data" / "grafik"
XML_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

W, H = 15.8, 8.8
PLOT_L, PLOT_R, PLOT_T, PLOT_B = 2.6, 15.1, 1.6, 7.0
SERIES = [
    ("m2c", 10, "2A5FD4", "m2c / 10"),
    ("m2c", 20, "0E7C66", "m2c / 20"),
    ("c2m", 10, "7D3C98", "c2m / 10"),
    ("c2m", 20, "CA6F1E", "c2m / 20"),
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(SUMMARY)
    df["idx"] = df.groupby(["direction", "rate", "run"]).cumcount() + 1
    return (
        df.groupby(["direction", "rate", "idx"], as_index=False)
        .agg(avg_e2e_ms=("avg_e2e_ms", "mean"),
             avg_conversion_ms=("avg_conversion_ms", "mean"),
             avg_cpu=("avg_cpu", "mean"))
    )


def base(title: str) -> Diagram:
    d = Diagram(title, W, H)
    d.label_at(W / 2, 0.5, title, pt=7.5, bold=True, color="000000")
    return d


def frame(d: Diagram, ymax: float, unit: str, ticks: int = 4) -> None:
    d.seg((PLOT_L, PLOT_T), (PLOT_L, PLOT_B), color="000000", lw=1.0)
    d.seg((PLOT_L, PLOT_B), (PLOT_R, PLOT_B), color="000000", lw=1.0)
    for i in range(ticks + 1):
        v = ymax * i / ticks
        y = PLOT_B - (PLOT_B - PLOT_T) * i / ticks
        if 0 < i < ticks:
            d.seg((PLOT_L, y), (PLOT_R, y), color="E6EBF2", lw=0.5)
        d.seg((PLOT_L - 0.10, y), (PLOT_L, y), color="000000", lw=0.8)
        d.label_at(PLOT_L - 0.75, y, f"{v:,.0f}".replace(",", "."),
                   pt=5, color="000000")
    d.label_at(1.0, PLOT_T - 0.35, unit, pt=5.5, bold=True, color="000000")


def legend(d: Diagram, entries, y: float = 8.25) -> None:
    step = 14.0 / len(entries)
    for i, (color, text) in enumerate(entries):
        x = 1.1 + i * step
        d.rect(None, x, y - 0.09, 0.32, 0.18, fill=color, line=color)
        d.label_at(x + 1.05, y, text, pt=5.2, color="000000")


def save(d: Diagram, name: str, doc_id: int) -> None:
    d._name = name
    with open(XML_DIR / f"{name}.xml", "w", encoding="utf-8") as f:
        f.write(to_drawingml(d, doc_id=doc_id, name=name))
    render_png(d, str(PNG_DIR / f"{name}.png"), dpi=200)
    print(f"--- {name} ---")
    validate(d)
    report_text_fit(d)


def timeseries(df: pd.DataFrame, col: str, title: str, unit: str,
               name: str, doc_id: int) -> None:
    d = base(title)
    ymax = float(df[col].max())
    ymax = max(1.0, round(ymax / 4) * 4)
    frame(d, ymax, unit)
    for direction, rate, color, label in SERIES:
        sub = df[(df.direction == direction) & (df.rate == rate)].sort_values("idx")
        pts = []
        for _, r in sub.iterrows():
            x = PLOT_L + (r.idx - 1) * (PLOT_R - PLOT_L) / 10
            y = PLOT_B - (float(r[col]) / ymax) * (PLOT_B - PLOT_T)
            pts.append((x, y))
        for p1, p2 in zip(pts, pts[1:]):
            d.seg(p1, p2, color=color, lw=1.4)
        for x, y in pts:
            d.circle(x, y, 0.045, fill=color, line=color)
    for idx in (1, 3, 5, 7, 9, 11):
        x = PLOT_L + (idx - 1) * (PLOT_R - PLOT_L) / 10
        d.label_at(x, PLOT_B + 0.32, str(idx), pt=5, color="000000")
    d.label_at((PLOT_L + PLOT_R) / 2, PLOT_B + 0.70,
               "Indeks bucket (1 sampai 11)", pt=5.2, color="000000")
    legend(d, [(c, t) for _, _, c, t in SERIES])
    d.label_at(13.1, 0.90, "11 bucket = 600 detik melintang batas menit",
               pt=4.5, color="000000")
    save(d, name, doc_id)


def comparison(name: str, doc_id: int) -> None:
    d = base("Loss (%): artikel acuan vs replikasi")
    frame(d, 100.0, "%", ticks=4)
    configs = [
        ("m2c/10", 0.00, 0.00),
        ("m2c/20", 0.00, 0.33),
        ("c2m/10", 92.54, 0.00),
        ("c2m/20", 95.52, 0.01),
    ]
    step = (PLOT_R - PLOT_L) / 4
    for i, (label, art, ours) in enumerate(configs):
        cx = PLOT_L + step * (i + 0.5)
        for j, (value, color, off) in enumerate(((art, "777777", -0.38),
                                                 (ours, "2A5FD4", 0.38))):
            h = max(value / 100 * (PLOT_B - PLOT_T), 0.03)
            x = cx + off - 0.28
            d.rect(None, x, PLOT_B - h, 0.56, h, fill=color, line=color)
            d.label_at(cx + off, PLOT_B - h - 0.24, f"{value:.2f}",
                       pt=5, color="000000")
        d.label_at(cx, PLOT_B + 0.34, label, pt=5.3, bold=True, color="000000")
    legend(d, [("777777", "Artikel acuan"), ("2A5FD4", "Replikasi kami")])
    d.label_at(11.9, 0.90, "Sumber: Tabel 2.2 dan Tabel 6.2",
               pt=4.5, color="000000")
    save(d, name, doc_id)


def main() -> None:
    data = load_data()
    timeseries(data, "avg_e2e_ms", "Delay E2E per Menit (rerata 10 run)", "ms",
               "delay_e2e_per_menit", 401)
    timeseries(data, "avg_conversion_ms", "Delay Konversi per Menit (rerata 10 run)", "ms",
               "delay_konversi_per_menit", 402)
    timeseries(data, "avg_cpu", "CPU Conversion Server per Menit (rerata 10 run)", "% CPU",
               "cpu_per_menit", 403)
    comparison("perbandingan_artikel", 404)


if __name__ == "__main__":
    main()
