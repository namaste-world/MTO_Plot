"""backend/sharedref.py
Builds *bibliographic‑coupling* links: an undirected edge between two papers
when they share ≥ `min_shared` canonical reference strings.  Edge attribute
`weight` equals the number of shared references so the front‑end can scale
stroke width (e.g., `sqrt(weight)`).

Output
------
public/sharedRef_edges.json
"""
from __future__ import annotations
import json, pathlib, re, itertools, collections
from typing import List, Dict

# we re‑use the lightweight slug function; import from citation if available
try:
    from .citation import _slug  # type: ignore
except ImportError:
    def _slug(txt: str) -> str:            # fallback copy
        txt = re.sub(r"<[^>]+>", "", txt)
        txt = re.sub(r"[^\w\s-]", "", txt.lower())
        return re.sub(r"\s+", " ", txt).strip()

# ──────────────────────────────────────────────────────────────────────────────

def build(papers: List[Dict], out_dir: pathlib.Path, *, min_shared: int = 2):
    """Generate bibliographic‑coupling edges and write sharedRef_edges.json.

    Parameters
    ----------
    papers     list[dict]  – records from backend.load_data.load()
    out_dir    Path        – destination dir
    min_shared int         – minimum #common references to keep an edge
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. map canonical reference slug → set(paper_ids)
    ref_index: Dict[str, set[str]] = collections.defaultdict(set)
    for p in papers:
        pid = p['id']
        for ref in p['citations_raw'].values():
            ref_index[_slug(ref)].add(pid)

    # 2. count shared occurrences for every unordered pair
    pair_counts: Dict[tuple[str, str], int] = collections.Counter()
    for plist in ref_index.values():
        for a, b in itertools.combinations(sorted(plist), 2):
            pair_counts[(a, b)] += 1

    # 3. convert to edge list with weight ≥ min_shared
    edges = [
        {'source': a, 'target': b, 'type': 'sharedRef', 'weight': w}
        for (a, b), w in pair_counts.items() if w >= min_shared
    ]

    (out_dir / 'sharedRef_edges.json').write_text(json.dumps(edges, indent=2))
    print(f"[sharedRef] wrote sharedRef_edges.json (edges: {len(edges)})")

    return edges