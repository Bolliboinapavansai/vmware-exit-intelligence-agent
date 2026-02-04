from pathlib import Path
import csv
from typing import List, Dict, Any


def write_summary_csv(out_dir: Path, records: List[Dict[str, Any]]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "summary.csv"
    headers = ["vm_id", "name", "category", "confidence", "risk_score", "risk_level"]
    with p.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for r in records:
            writer.writerow({h: r.get(h) for h in headers})
    return p
