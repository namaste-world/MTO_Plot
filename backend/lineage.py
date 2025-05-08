"""backend/lineage.py
Creates vertical lineage threads by connecting consecutive publications of the
*first* author.  Output edges carry a `yearGap` attribute so the front‑end can
vary stroke opacity or dash pattern.
"""
from __future__ import annotations
import json, pathlib, itertools
from typing import List, Dict
from .load_data import safe_parse_date


def build(papers: List[Dict], out_dir: pathlib.Path):
    """Write lineage_edges.json connecting an author's successive papers."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # group by first author
    author_map: Dict[str, List[tuple]] = {}
    for p in papers:
        if p['authors']:
            a0 = p['authors'][0]
            dt = safe_parse_date(p['date_raw'])
            if dt:
                author_map.setdefault(a0, []).append((dt, p['id']))

    edges = []
    for pubs in author_map.values():
        pubs.sort()  # by date
        for (d1, pid1), (d2, pid2) in itertools.pairwise(pubs):
            gap = (d2.year - d1.year) or 1  # avoid zero gap
            edges.append({
                'source': pid1,
                'target': pid2,
                'type'  : 'lineage',
                'yearGap': gap
            })

    (out_dir / 'lineage_edges.json').write_text(json.dumps(edges, indent=2))
    print(f"[lineage] wrote lineage_edges.json (edges: {len(edges)})")

    return edges
