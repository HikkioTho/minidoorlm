import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from beta_config import get_beta_config


@dataclass
class StudentProfile:
    name: str
    level: str
    goals: str
    analogy_preferences: str
    weak_topics: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    current_streak: int = 0
    last_review_date: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def get_profile_dir() -> Path:
    return get_beta_config().profile_dir


def clean_topic_list(raw_value: str) -> List[str]:
    if not raw_value:
        return []

    pieces = raw_value.replace("\n", ",").split(",")
    cleaned = []

    for piece in pieces:
        topic = piece.strip()

        if topic:
            cleaned.append(topic)

    return cleaned


def profile_file_path(name: str) -> Path:
    safe_name = "".join(
        char.lower() if char.isalnum() else "_"
        for char in name.strip()
    ).strip("_")

    if not safe_name:
        safe_name = "student"

    profile_dir = get_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)

    return profile_dir / f"{safe_name}.json"


def save_profile(profile: StudentProfile) -> Path:
    profile.updated_at = datetime.now(timezone.utc).isoformat()

    path = profile_file_path(profile.name)
    path.write_text(
        json.dumps(asdict(profile), indent=2),
        encoding="utf-8",
    )

    return path


def load_profile(name: str) -> StudentProfile:
    path = profile_file_path(name)

    if not path.exists():
        raise FileNotFoundError("Profile not found.")

    payload = json.loads(path.read_text(encoding="utf-8"))

    return StudentProfile(**payload)


def list_profiles() -> List[str]:
    profile_dir = get_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)

    names = []

    for path in profile_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            names.append(payload.get("name", path.stem))
        except json.JSONDecodeError:
            continue

    return sorted(names)


def build_profile(
    name: str,
    level: str,
    goals: str,
    analogy_preferences: str,
    weak_topics_raw: str,
    strong_topics_raw: str,
    current_streak: int = 0,
    last_review_date: Optional[str] = None,
) -> StudentProfile:
    return StudentProfile(
        name=name.strip(),
        level=level.strip(),
        goals=goals.strip(),
        analogy_preferences=analogy_preferences.strip(),
        weak_topics=clean_topic_list(weak_topics_raw),
        strong_topics=clean_topic_list(strong_topics_raw),
        current_streak=max(0, int(current_streak)),
        last_review_date=last_review_date,
    )