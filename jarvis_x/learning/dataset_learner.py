import html
import os
import re
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
    """Learn from XML and HTML datasets by extracting text and adding it to the knowledge base."""

    SUPPORTED_EXTENSIONS = {'.xml', '.html', '.htm'}

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

    def _learn_file(self, path: Path) -> int:
        ext = path.suffix.lower()
        text = ''
        if ext == '.xml':
            text = self._extract_xml(path)
        elif ext in {'.html', '.htm'}:
            text = self._extract_html(path)
        else:
            return 0
        return self._learn_text(text, path)

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
