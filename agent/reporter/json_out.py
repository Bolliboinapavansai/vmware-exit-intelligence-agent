from pathlib import Path
import json
from typing import List, Dict, Any


def write_classification(out_dir: Path, records: List[Dict[str, Any]]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "classification.json"
    with p.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)
    return p
