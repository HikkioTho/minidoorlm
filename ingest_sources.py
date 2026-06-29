import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from beta_config import get_beta_config, safe_display_path
from rag_chunker import TextChunk, chunk_text


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
}


def parse_args():
    config = get_beta_config()

    parser = argparse.ArgumentParser(
        description="Ingest approved local OpenDoor public source files into simple RAG chunks."
    )

    parser.add_argument(
        "--source-dir",
        type=Path,
        default=config.public_source_dir,
        help="Approved folder containing .txt or .md source files.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=config.knowledge_file,
        help="Output JSON file for knowledge chunks.",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=900,
        help="Maximum characters per chunk.",
    )

    parser.add_argument(
        "--overlap-chars",
        type=int,
        default=120,
        help="Character overlap between chunks.",
    )

    return parser.parse_args()


def assert_inside_project(path: Path) -> None:
    config = get_beta_config()

    try:
        path.resolve().relative_to(config.project_root.resolve())
    except ValueError:
        raise ValueError(
            "Refusing to read or write outside the OpenDoor project folder."
        )


def read_source_file(path: Path) -> str:
    encodings = ["utf-8", "utf-8-sig", "cp1252"]
    last_error = None

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(f"Could not read source file. Last error: {last_error}")


def collect_source_files(source_dir: Path) -> List[Path]:
    assert_inside_project(source_dir)

    if not source_dir.exists():
        source_dir.mkdir(parents=True, exist_ok=True)
        return []

    files = []

    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return sorted(files)


def build_chunks(source_dir: Path, max_chars: int, overlap_chars: int) -> List[TextChunk]:
    source_files = collect_source_files(source_dir)
    all_chunks: List[TextChunk] = []

    for source_file in source_files:
        assert_inside_project(source_file)

        text = read_source_file(source_file)
        relative_name = str(source_file.relative_to(source_dir)).replace("\\", "/")

        chunks = chunk_text(
            source_name=relative_name,
            text=text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )

        all_chunks.extend(chunks)

    return all_chunks


def main() -> int:
    args = parse_args()

    assert_inside_project(args.source_dir)
    assert_inside_project(args.out)

    chunks = build_chunks(
        source_dir=args.source_dir,
        max_chars=args.max_chars,
        overlap_chars=args.overlap_chars,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "chunk_count": len(chunks),
        "source_dir": safe_display_path(args.source_dir),
        "chunks": [asdict(chunk) for chunk in chunks],
    }

    args.out.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print(f"Source directory: {safe_display_path(args.source_dir)}")
    print(f"Created chunks: {len(chunks)}")
    print(f"Saved to: {safe_display_path(args.out)}")

    if len(chunks) == 0:
        print("")
        print("No source files found.")
        print("Add .txt or .md files to data/sources/public/ and run this again.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())