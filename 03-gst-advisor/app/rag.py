"""Small, dependency-free retrieval layer over GST markdown knowledge."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

_TOKEN = re.compile(r"[a-zA-Z0-9₹%]+")


@dataclass
class Chunk:
    source: str
    text: str
    tf: dict[str, float]
    title: str = ""
    token_count: int = 0


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


class KnowledgeBase:
    def __init__(self, folder: str | Path):
        self.chunks: list[Chunk] = []
        self.idf: dict[str, float] = {}
        self._load(Path(folder))

    def _load(self, folder: Path) -> None:
        files = sorted(folder.glob("*.md"))
        raw_chunks: list[tuple[str, str, str]] = []
        for f in files:
            text = f.read_text(encoding="utf-8")
            # Imported knowledge files may contain YAML front matter; it is metadata, not answer content.
            text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)
            parts = re.split(r"\n## ", text)
            for i, part in enumerate(parts):
                body = part if i == 0 else "## " + part
                body = body.strip()
                if len(body) < 40:
                    continue
                heading = body.splitlines()[0].lstrip("# ").strip()
                raw_chunks.append((f.name, body, heading))
        df: dict[str, int] = {}
        parsed: list[tuple[str, str, dict[str, float], str, int]] = []
        for source, body, heading in raw_chunks:
            toks = _tokens(body)
            tf: dict[str, float] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            n = max(len(toks), 1)
            tf = {k: v / n for k, v in tf.items()}
            for k in tf:
                df[k] = df.get(k, 0) + 1
            parsed.append((source, body, tf, heading, len(toks)))
        n = max(len(parsed), 1)
        self.idf = {k: math.log((n + 1) / (v + 1)) + 1 for k, v in df.items()}
        self.average_length = sum(item[4] for item in parsed) / n
        self.chunks = [Chunk(s, b, tf, heading, count) for s, b, tf, heading, count in parsed]

    def search(self, query: str, k: int = 4) -> list[tuple[float, Chunk]]:
        qtf: dict[str, float] = {}
        qt = _tokens(query)
        for t in qt:
            qtf[t] = qtf.get(t, 0) + 1
        scored = []
        for ch in self.chunks:
            score = 0.0
            for t, qv in qtf.items():
                term_frequency = ch.tf.get(t, 0.0)
                if not term_frequency:
                    continue
                # BM25-style saturation avoids long chunks winning by size alone.
                raw_tf = term_frequency * ch.token_count
                length_factor = 1 - 0.75 + 0.75 * ch.token_count / max(self.average_length, 1)
                score += self.idf.get(t, 0.0) * (raw_tf * 2.0 / (raw_tf + 1.2 * length_factor))
            heading_tokens = set(_tokens(ch.title))
            score += sum(self.idf.get(t, 0.0) * 0.35 for t in qtf if t in heading_tokens)
            if len(qt) > 1 and " ".join(qt) in " ".join(_tokens(ch.text)):
                score += 1.0
            scored.append((score, ch))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [x for x in scored[:k] if x[0] > 0] or scored[:k]


_kb: KnowledgeBase | None = None


def kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        folder = Path(settings.knowledge_dir)
        if not folder.is_absolute():
            folder = Path(__file__).resolve().parent.parent / folder
        _kb = KnowledgeBase(folder)
    return _kb
