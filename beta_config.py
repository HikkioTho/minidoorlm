from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class BetaConfig:
    app_name: str
    environment: str
    project_root: Path

    runtime_dir: Path
    data_dir: Path
    profile_dir: Path
    logs_dir: Path
    exports_dir: Path
    upload_dir: Path
    analytics_dir: Path

    public_source_dir: Path
    private_source_dir: Path
    knowledge_dir: Path
    knowledge_file: Path

    show_debug_errors: bool
    show_admin_diagnostics: bool
    allow_profile_saving: bool
    allow_assignment_exports: bool

    max_topic_chars: int
    max_profile_field_chars: int
    max_submission_chars: int
    min_submission_words: int
    max_upload_bytes: int


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def project_path(relative_path: str) -> Path:
    clean = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
    return PROJECT_ROOT / clean


def get_beta_config() -> BetaConfig:
    environment = os.getenv("OPENDOOR_ENV", "public_beta").strip()

    runtime_dir = project_path(os.getenv("OPENDOOR_RUNTIME_DIR", "runtime"))
    data_dir = project_path(os.getenv("OPENDOOR_DATA_DIR", "data"))

    profile_dir = runtime_dir / "profiles"
    logs_dir = runtime_dir / "logs"
    exports_dir = runtime_dir / "exports"
    upload_dir = runtime_dir / "uploads"
    analytics_dir = runtime_dir / "analytics"

    public_source_dir = data_dir / "sources" / "public"
    private_source_dir = data_dir / "sources" / "private"
    knowledge_dir = data_dir / "knowledge"
    knowledge_file = knowledge_dir / "knowledge_chunks.json"

    return BetaConfig(
        app_name=os.getenv("OPENDOOR_APP_NAME", "OpenDoor Beta"),
        environment=environment,
        project_root=PROJECT_ROOT,

        runtime_dir=runtime_dir,
        data_dir=data_dir,
        profile_dir=profile_dir,
        logs_dir=logs_dir,
        exports_dir=exports_dir,
        upload_dir=upload_dir,
        analytics_dir=analytics_dir,

        public_source_dir=public_source_dir,
        private_source_dir=private_source_dir,
        knowledge_dir=knowledge_dir,
        knowledge_file=knowledge_file,

        show_debug_errors=env_bool("OPENDOOR_SHOW_DEBUG_ERRORS", default=False),
        show_admin_diagnostics=env_bool("OPENDOOR_SHOW_ADMIN_DIAGNOSTICS", default=False),
        allow_profile_saving=env_bool("OPENDOOR_ALLOW_PROFILE_SAVING", default=True),
        allow_assignment_exports=env_bool("OPENDOOR_ALLOW_ASSIGNMENT_EXPORTS", default=False),

        max_topic_chars=env_int("OPENDOOR_MAX_TOPIC_CHARS", 500),
        max_profile_field_chars=env_int("OPENDOOR_MAX_PROFILE_FIELD_CHARS", 1200),
        max_submission_chars=env_int("OPENDOOR_MAX_SUBMISSION_CHARS", 7000),
        min_submission_words=env_int("OPENDOOR_MIN_SUBMISSION_WORDS", 25),
        max_upload_bytes=env_int("OPENDOOR_MAX_UPLOAD_BYTES", 5_000_000),
    )


def safe_display_path(path: Path | None) -> str:
    if path is None:
        return ""

    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return "[outside project]"