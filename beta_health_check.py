from dataclasses import dataclass
from pathlib import Path
from typing import List

from beta_config import get_beta_config, safe_display_path


@dataclass
class HealthCheckResult:
    passed: bool
    warnings: List[str]
    errors: List[str]


def check_directory(path: Path, label: str, create: bool = True) -> List[str]:
    errors = []

    if not path.exists():
        if create:
            path.mkdir(parents=True, exist_ok=True)
        else:
            errors.append(f"{label} does not exist: {safe_display_path(path)}")

    if path.exists() and not path.is_dir():
        errors.append(f"{label} exists but is not a directory: {safe_display_path(path)}")

    return errors


def run_beta_health_check() -> HealthCheckResult:
    config = get_beta_config()

    warnings: List[str] = []
    errors: List[str] = []

    required_dirs = [
        (config.runtime_dir, "Runtime directory"),
        (config.profile_dir, "Profile directory"),
        (config.logs_dir, "Logs directory"),
        (config.exports_dir, "Exports directory"),
        (config.upload_dir, "Upload directory"),
        (config.analytics_dir, "Analytics directory"),
        (config.public_source_dir, "Public source directory"),
        (config.knowledge_dir, "Knowledge directory"),
    ]

    for path, label in required_dirs:
        errors.extend(check_directory(path, label))

    if not config.knowledge_file.exists():
        warnings.append(
            "No local knowledge file found. Lessons will still work, but source-grounded RAG will be limited."
        )

    gitignore = Path(".gitignore")

    if gitignore.exists():
        gitignore_text = gitignore.read_text(encoding="utf-8", errors="ignore")

        recommended_ignores = [
            "runtime/",
            "data/sources/private/",
            "*.pt",
            "training_samples/",
            ".streamlit/secrets.toml",
        ]

        for item in recommended_ignores:
            if item not in gitignore_text:
                warnings.append(f".gitignore should include: {item}")
    else:
        warnings.append(".gitignore not found.")

    return HealthCheckResult(
        passed=len(errors) == 0,
        warnings=warnings,
        errors=errors,
    )
