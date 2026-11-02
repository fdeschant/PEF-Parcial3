import os
import re
from dataclasses import dataclass


@dataclass
class SearchResult:
    doc_id: int
    doc_name: str
    score: float
    snippet: str = ""


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\W+", text.lower()) if t]


def build_snippet(tokens: list[str], query_terms: list[str], context: int = 3) -> str:
    for i, token in enumerate(tokens):
        if token in query_terms:
            start = max(0, i - context)
            end = min(len(tokens), i + context + 1)
            return " ".join(tokens[start:end])
    return " ".join(tokens[:6])


def parse_doc_id(filename: str) -> int:
    stem = filename.rsplit(".", 1)[0]
    parts = stem.split("_")
    return int(parts[-1])


def list_doc_files(docs_dir: str) -> list[str]:
    if not os.path.isdir(docs_dir):
        return []
    return sorted(
        f for f in os.listdir(docs_dir) if f.startswith("documento_") and f.endswith(".txt")
    )


def read_tokens(filepath: str) -> list[str]:
    with open(filepath, encoding="utf-8") as f:
        return tokenize(f.read())
