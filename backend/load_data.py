# backend/load_data.py
import json, pathlib, re
from typing import List, Dict, Any

from datetime import datetime

DATE_PATTERNS = ["%Y/%m/%d", "%Y-%m-%d", "%Y/%m", "%Y-%m", "%Y"]

def safe_parse_date(raw: str) -> datetime | None:
    """Return datetime if `raw` matches common patterns; else None."""
    for fmt in DATE_PATTERNS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None

def slug(text: str) -> str:
    t = re.sub(r"<[^>]+>", "", text)
    t = re.sub(r"[^\w\s-]", "", t.lower())
    return re.sub(r"\s+", "-", t.strip())[:90]

def parse_date(raw: str) -> str:
    """Convert 'YYYY/MM/DD' or 'YYYY/MM' or 'YYYY' → ISO 'YYYY-MM-DD'."""
    parts = raw.split('/')
    parts += ['01'] * (3 - len(parts))      # pad missing month/day
    y, m, d = parts[:3]
    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

def load(json_dir: pathlib.Path) -> List[Dict[str, Any]]:
    papers: List[Dict[str, Any]] = []
    for fp in sorted(json_dir.glob('*.json')):
        data = json.loads(fp.read_text())
        papers.append({
            "id"        : slug(data.get("title", fp.stem)),
            "title"     : data.get("title", ""),
            "authors"   : data.get("authors", []),
            "date_raw"  : data.get("date", ""),
            "date"      : parse_date(data.get("date", "1900/01/01")),
            "keywords"  : data.get("keywords", []),
            "abstract"  : data.get("abstract", ""),
            "citations_raw": data.get("citations", {})
        })
    return papers
