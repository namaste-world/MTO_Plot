"""backend/density.py
Computes how many papers appear in each calendar year.  Output is a simple
{"YYYY": count} mapping consumed by the Density/Burst view.
"""
from __future__ import annotations
import json, pathlib, collections
from typing import List, Dict
from .load_data import safe_parse_date  # reuse robust date parser


def build(papers: List[Dict], out_dir: pathlib.Path):
    """Write year_density.json (count of papers per year)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    year_counts = collections.Counter()
    for p in papers:
        dt = safe_parse_date(p['date_raw'])
        if dt:
            year_counts[dt.year] += 1

    (out_dir / 'year_density.json').write_text(
        json.dumps(dict(year_counts), indent=2))
    print(f"[density] wrote year_density.json (years: {len(year_counts)})")

    return year_counts
