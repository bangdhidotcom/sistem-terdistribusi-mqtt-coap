"""Regenerate 4 grafik eksperimen.

Satu sumber kebenaran: `laporan/chart_shapes.py` menghasilkan XML DrawingML
editabel DAN PNG preview dari summary.csv yang sama, sehingga kedua format
tidak pernah berbeda isinya.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "laporan"))

from chart_shapes import main  # noqa: E402


if __name__ == "__main__":
    main()
