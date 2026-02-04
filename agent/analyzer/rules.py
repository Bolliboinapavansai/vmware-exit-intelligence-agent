from pathlib import Path
from typing import Any, Dict, List
import json

try:
    import yaml as _yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _yaml = None
    _HAS_YAML = False


def load_rules(path: Path) -> List[Dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if _HAS_YAML:
        data = _yaml.safe_load(text)
    else:
        try:
            data = json.loads(text)
        except Exception:
            raise RuntimeError(
                "PyYAML is not installed and rules file is not valid JSON.\n"
                "Install PyYAML (pip install PyYAML) to load YAML rules."
            )

    if not isinstance(data, list):
        raise ValueError("Rules file must be a YAML/JSON list of rules")
    return data
