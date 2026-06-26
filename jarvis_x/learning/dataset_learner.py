import html
import os
import re
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import List
from xml.etree import ElementTree as ET

from jarvis_x.memory.store import KnowledgeBase


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = []

    def handle_data(self, data):
        if data and data.strip():
            self.fragments.append(data.strip())

    def get_text(self) -> str:
        return "\n".join(self.fragments)


class DatasetLearner:
    """Learn from XML, JSON, TXT, and HTML datasets by extracting text and adding it to the knowledge base."""

    SUPPORTED_EXTENSIONS = {'.xml', '.html', '.htm', '.json', '.txt'}

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def learn_from_path(self, path: str) -> int:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Dataset path not found: {path}")

        total = 0
        if path_obj.is_dir():
            for file_path in path_obj.rglob('*'):
                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    total += self._learn_file(file_path)
        else:
            total = self._learn_file(path_obj)
        return total

    def auto_scan_pool(self) -> int:
        """
        Auto-scans the dataset pool directory from Config.
        """
        from jarvis_x.core.config import Config
        pool_path = Config.DATASET_POOL_DIR
        if not os.path.exists(pool_path):
            return 0
        return self.learn_from_path(pool_path)

    def _learn_file(self, path: Path) -> int:
        ext = path.suffix.lower()
        if ext == '.xml':
            text = self._extract_xml(path)
            return self._learn_text(text, path)
        elif ext in {'.html', '.htm'}:
            text = self._extract_html(path)
            return self._learn_text(text, path)
        elif ext == '.txt':
            text = self._extract_txt(path)
            return self._learn_text(text, path)
        elif ext == '.json':
            return self._learn_json(path)
        return 0

    def _extract_xml(self, path: Path) -> str:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            fragments: List[str] = []
            for element in root.iter():
                if element.text and element.text.strip():
                    fragments.append(element.text.strip())
                if element.tail and element.tail.strip():
                    fragments.append(element.tail.strip())
            return '\n'.join(fragments)
        except ET.ParseError:
            return ''

    def _extract_html(self, path: Path) -> str:
        try:
            parser = _HTMLTextExtractor()
            with path.open('r', encoding='utf-8', errors='ignore') as handle:
                parser.feed(handle.read())
            return parser.get_text()
        except Exception:
            return ''

    def _extract_txt(self, path: Path) -> str:
        try:
            with path.open('r', encoding='utf-8', errors='ignore') as handle:
                return handle.read()
        except Exception:
            return ''

    def _learn_json(self, path: Path) -> int:
        count = 0
        try:
            with path.open('r', encoding='utf-8', errors='ignore') as handle:
                data = json.load(handle)
            
            # If it's a list of Q&A dictionaries
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Support multiple key formats: input/output, query/response, pattern/response
                        q = item.get("input") or item.get("query") or item.get("pattern") or item.get("question")
                        a = item.get("output") or item.get("response") or item.get("answer")
                        if q and a:
                            self.kb.learn(str(q).strip(), str(a).strip(), confidence=0.95)
                            self.kb.log_learning('dataset_learn_qa', f"{path.name}: {q[:30]}")
                            count += 1
                        else:
                            # Fallback: extract all values recursively
                            text = self._extract_json_text_recursive(item)
                            count += self._learn_text(text, path)
            elif isinstance(data, dict):
                # Check for direct key-value pairs representing questions/answers
                for k, v in data.items():
                    if isinstance(v, str) and len(v) > 10:
                        self.kb.learn(str(k).strip(), str(v).strip(), confidence=0.85)
                        count += 1
                    else:
                        text = self._extract_json_text_recursive(v)
                        count += self._learn_text(text, path)
        except Exception:
            pass
        return count

    def _extract_json_text_recursive(self, data) -> str:
        fragments = []
        if isinstance(data, dict):
            for k, v in data.items():
                fragments.append(str(k))
                fragments.append(self._extract_json_text_recursive(v))
        elif isinstance(data, list):
            for item in data:
                fragments.append(self._extract_json_text_recursive(item))
        else:
            fragments.append(str(data))
        return "\n".join(f for f in fragments if f.strip())

    def _learn_text(self, text: str, path: Path) -> int:
        if not text:
            return 0

        count = 0
        text = html.unescape(re.sub(r'\s+', ' ', text)).strip()
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sentence in sentences:
            clean = sentence.strip()
            if len(clean) < 40:
                continue
            key = ' '.join(clean.split()[:8]).lower()
            if len(key) < 15:
                continue
            self.kb.learn(key, clean, confidence=0.45)
            self.kb.log_learning('dataset_learn', f"{path.name}: {key}")
            count += 1
        return count
