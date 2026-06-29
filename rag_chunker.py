from dataclasses import dataclass
from typing import List


@dataclass
class TextChunk:
    source_name: str
    chunk_id: str
    text: str


def normalize_text(text: str) -> str:
    return "\n".join(
        line.rstrip()
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ).strip()


def split_into_paragraphs(text: str) -> List[str]:
    paragraphs = []
    current = []

    for line in normalize_text(text).splitlines():
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                paragraphs.append(" ".join(current))
                current = []

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs


def chunk_text(
    source_name: str,
    text: str,
    max_chars: int = 900,
    overlap_chars: int = 120,
) -> List[TextChunk]:
    paragraphs = split_into_paragraphs(text)

    chunks: List[TextChunk] = []
    current_text = ""

    for paragraph in paragraphs:
        if not current_text:
            current_text = paragraph
            continue

        if len(current_text) + len(paragraph) + 1 <= max_chars:
            current_text += "\n" + paragraph
        else:
            chunk_number = len(chunks) + 1
            chunks.append(
                TextChunk(
                    source_name=source_name,
                    chunk_id=f"{source_name}::chunk_{chunk_number}",
                    text=current_text.strip(),
                )
            )

            overlap = current_text[-overlap_chars:] if overlap_chars > 0 else ""
            current_text = (overlap + "\n" + paragraph).strip()

    if current_text:
        chunk_number = len(chunks) + 1
        chunks.append(
            TextChunk(
                source_name=source_name,
                chunk_id=f"{source_name}::chunk_{chunk_number}",
                text=current_text.strip(),
            )
        )

    return chunks