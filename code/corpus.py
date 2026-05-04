"""
corpus.py – Loads the local support corpus and provides BM25-style keyword retrieval.
No network calls, no embeddings – pure TF-IDF / overlap scoring for zero-dependency retrieval.
"""

from __future__ import annotations
import json
import math
import pathlib
import re
import string
from collections import defaultdict
from typing import Optional


# ── Stopwords (tiny set) ──────────────────────────────────────────────────────
STOPWORDS = {
    "a","an","the","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall",
    "and","or","but","if","in","on","at","to","for","of","with","by","from",
    "up","about","into","through","during","before","after","above","below",
    "i","me","my","we","our","you","your","he","she","it","its","they","their",
    "what","which","who","whom","this","that","these","those","how","when","where",
    "why","not","no","nor","so","yet","both","either","neither","whether","because",
    "as","until","while","although","though","since","unless","even","just","also",
    "more","most","other","some","such","than","then","than","there","their","can",
    "please","help","hi","hello","dear","thanks","thank","regards","sincerely",
}

TRANS = str.maketrans("", "", string.punctuation)


def tokenise(text: str) -> list[str]:
    text = text.lower().translate(TRANS)
    return [t for t in text.split() if t not in STOPWORDS and len(t) > 2]


# ── Document container ─────────────────────────────────────────────────────────
class Document:
    def __init__(self, doc_id: str, domain: str, title: str, body: str, source_file: str):
        self.doc_id = doc_id
        self.domain = domain          # "hackerrank" | "claude" | "visa"
        self.title  = title
        self.body   = body
        self.source_file = source_file
        self.tokens = tokenise(f"{title} {title} {body}")  # title boosted x2
        self.tf: dict[str, float] = {}
        self._compute_tf()

    def _compute_tf(self):
        counts: dict[str, int] = defaultdict(int)
        for t in self.tokens:
            counts[t] += 1
        n = max(len(self.tokens), 1)
        self.tf = {t: c / n for t, c in counts.items()}

    def snippet(self, max_chars=2000) -> str:
        return self.body[:max_chars]

    def __repr__(self):
        return f"<Doc {self.doc_id} [{self.domain}] {self.title[:50]}>"


# ── Corpus loader ──────────────────────────────────────────────────────────────
class Corpus:
    def __init__(self, data_dir: pathlib.Path):
        self.data_dir = data_dir
        self.docs: list[Document] = []
        self._idf: dict[str, float] = {}
        self._load()
        self._build_idf()
        print(f"📚  Corpus: {len(self.docs)} documents loaded from {data_dir}")

    # ── Loading ────────────────────────────────────────────────────────────────

    def _load(self):
        for domain_dir in sorted(self.data_dir.iterdir()):
            if not domain_dir.is_dir():
                continue
            domain = domain_dir.name.lower()
            self._load_domain(domain, domain_dir)

    def _load_domain(self, domain: str, domain_dir: pathlib.Path):
        for fpath in sorted(domain_dir.rglob("*")):
            if not fpath.is_file():
                continue
            suffix = fpath.suffix.lower()
            try:
                if suffix == ".json":
                    self._ingest_json(domain, fpath)
                elif suffix in (".txt", ".md", ".html", ".csv"):
                    self._ingest_text(domain, fpath)
            except Exception as e:
                pass  # skip unreadable files silently

    def _make_id(self, fpath: pathlib.Path, idx: int = 0) -> str:
        return f"{fpath.stem}_{idx}"

    def _add(self, doc_id: str, domain: str, title: str, body: str, source_file: str):
        if not body.strip():
            return
        self.docs.append(Document(doc_id, domain, title, body[:8000], source_file))

    def _ingest_json(self, domain: str, fpath: pathlib.Path):
        raw = json.loads(fpath.read_text(encoding="utf-8", errors="replace"))

        # Handle list of articles
        if isinstance(raw, list):
            for i, item in enumerate(raw):
                self._parse_article_obj(domain, fpath, item, i)
        elif isinstance(raw, dict):
            # Might be a wrapper {"articles": [...]} or a single article
            if "articles" in raw:
                for i, item in enumerate(raw["articles"]):
                    self._parse_article_obj(domain, fpath, item, i)
            else:
                self._parse_article_obj(domain, fpath, raw, 0)

    def _parse_article_obj(self, domain, fpath, obj: dict, idx: int):
        title = (
            obj.get("title") or obj.get("name") or obj.get("subject") or
            obj.get("question") or fpath.stem
        )
        body_parts = []
        for key in ("body", "content", "answer", "description", "text", "solution"):
            val = obj.get(key, "")
            if isinstance(val, str):
                body_parts.append(val)
        body = "\n\n".join(body_parts) if body_parts else str(obj)
        # Strip HTML tags cheaply
        body = re.sub(r"<[^>]+>", " ", body)
        body = re.sub(r"\s{2,}", " ", body).strip()
        doc_id = obj.get("id") or self._make_id(fpath, idx)
        self._add(str(doc_id), domain, str(title), body, str(fpath))

    def _ingest_text(self, domain: str, fpath: pathlib.Path):
        text = fpath.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        # Split long files into ~1500-char chunks
        chunk_size = 1500
        if len(text) <= chunk_size:
            self._add(self._make_id(fpath, 0), domain, fpath.stem, text, str(fpath))
        else:
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            for i, chunk in enumerate(chunks):
                self._add(self._make_id(fpath, i), domain, f"{fpath.stem} (part {i+1})", chunk, str(fpath))

    # ── IDF ────────────────────────────────────────────────────────────────────

    def _build_idf(self):
        N = len(self.docs)
        df: dict[str, int] = defaultdict(int)
        for doc in self.docs:
            for t in set(doc.tokens):
                df[t] += 1
        self._idf = {t: math.log((N + 1) / (d + 1)) + 1 for t, d in df.items()}

    # ── Retrieval ──────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        domain_filter: Optional[str] = None,
    ) -> list[Document]:
        """BM25-lite retrieval (TF * IDF, no k1/b params)."""
        q_tokens = tokenise(query)
        if not q_tokens:
            return []

        scores: dict[str, float] = defaultdict(float)
        for t in q_tokens:
            idf = self._idf.get(t, 0.5)
            for doc in self.docs:
                if domain_filter and doc.domain != domain_filter:
                    continue
                tf = doc.tf.get(t, 0.0)
                if tf > 0:
                    scores[doc.doc_id] += tf * idf

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        id_to_doc = {d.doc_id: d for d in self.docs}
        return [id_to_doc[did] for did, _ in ranked[:top_k] if did in id_to_doc]

    def domain_docs(self, domain: str) -> list[Document]:
        return [d for d in self.docs if d.domain == domain]