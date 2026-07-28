import json
import os
import re
from pathlib import Path
from typing import Dict, List


class DatasetValidator:
    """Validate and score local datasets without external services."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]

    def validate_directory(self, directory: Path | str) -> Dict[str, object]:
        directory = Path(directory)
        files = []
        errors: List[str] = []
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".json", ".txt", ".xml", ".csv"}:
                files.append(path)
        for path in files:
            try:
                if path.suffix.lower() == ".json":
                    json.loads(path.read_text(encoding="utf-8"))
                elif path.suffix.lower() == ".txt":
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if not text.strip():
                        errors.append(f"{path.name}: empty text file")
                elif path.suffix.lower() == ".xml":
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if "<" not in text or ">" not in text:
                        errors.append(f"{path.name}: malformed xml")
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")
        return {"files_scanned": len(files), "errors": errors}
