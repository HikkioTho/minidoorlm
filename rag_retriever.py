import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


DEFAULT_KNOWLEDGE_FILE = Path("data/knowledge/knowledge_chunks.json")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "why",
    "with",
}


@dataclass
class RetrievedChunk:
    source_name: str
    chunk_id: str
    text: str
    score: float


def tokenize(text: str) -> List[str]:
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def load_chunks(path: Path = DEFAULT_KNOWLEDGE_FILE) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("chunks", [])


def score_chunk(query_terms: List[str], chunk_text: str) -> float:
    if not query_terms:
        return 0.0

    chunk_terms = tokenize(chunk_text)

    if not chunk_terms:
        return 0.0

    chunk_counts: Dict[str, int] = {}

    for term in chunk_terms:
        chunk_counts[term] = chunk_counts.get(term, 0) + 1

    score = 0.0

    for term in query_terms:
        if term in chunk_counts:
            score += 1.0 + math.log(1 + chunk_counts[term])

    coverage = len(set(query_terms).intersection(set(chunk_terms))) / max(1, len(set(query_terms)))
    score += coverage * 2.0

    return round(score, 4)


def retrieve_relevant_chunks(
    query: str,
    limit: int = 4,
    knowledge_file: Path = DEFAULT_KNOWLEDGE_FILE,
) -> List[RetrievedChunk]:
    chunks = load_chunks(knowledge_file)
    query_terms = tokenize(query)

    scored: List[RetrievedChunk] = []

    for chunk in chunks:
        text = chunk.get("text", "")
        score = score_chunk(query_terms, text)

        if score <= 0:
            continue

        scored.append(
            RetrievedChunk(
                source_name=chunk.get("source_name", "unknown"),
                chunk_id=chunk.get("chunk_id", "unknown"),
                text=text,
                score=score,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]