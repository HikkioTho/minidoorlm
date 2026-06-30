from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from beta_config import get_beta_config, safe_display_path


ALLOWED_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
}

ALLOWED_UPLOAD_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".mp4",
    ".mov",
}


@dataclass
class SavedUpload:
    original_name: str
    saved_path: Path
    display_path: str
    extension: str
    size_bytes: int
    text_preview: str
    readable_as_text: bool


def sanitize_filename(filename: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "_"
        for char in str(filename or "").strip()
    )

    return cleaned or "uploaded_file"


def read_text_preview(path: Path, max_chars: int = 2500) -> str:
    encodings = ["utf-8", "utf-8-sig", "cp1252"]

    for encoding in encodings:
        try:
            text = path.read_text(encoding=encoding)
            return text[:max_chars]
        except UnicodeDecodeError:
            continue

    return ""


def save_uploaded_file(uploaded_file) -> SavedUpload:
    config = get_beta_config()
    config.upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = sanitize_filename(uploaded_file.name)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            "Use txt, md, csv, json, pdf, png, jpg, jpeg, webp, mp4, or mov."
        )

    data = uploaded_file.getvalue()

    if len(data) > config.max_upload_bytes:
        raise ValueError(
            f"File is too large. Limit is {config.max_upload_bytes} bytes for beta."
        )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    saved_name = f"{timestamp}_{original_name}"
    saved_path = config.upload_dir / saved_name

    saved_path.write_bytes(data)

    readable_as_text = extension in ALLOWED_TEXT_EXTENSIONS
    text_preview = read_text_preview(saved_path) if readable_as_text else ""

    return SavedUpload(
        original_name=original_name,
        saved_path=saved_path,
        display_path=safe_display_path(saved_path),
        extension=extension,
        size_bytes=len(data),
        text_preview=text_preview,
        readable_as_text=readable_as_text,
    )