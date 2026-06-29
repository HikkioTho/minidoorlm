from dataclasses import dataclass
from pathlib import Path
from typing import List

from beta_config import get_beta_config


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
            errors.append(f"{label} does not exist: {path}")

    if path.exists() and not path.is_dir():
        errors.append(f"{label} exists but is not a directory: {path}")

    return errors


def run_beta_health_check() -> HealthCheckResult:
    config = get_beta_config()

    warnings = []
    errors = []

    errors.extend(check_directory(config.data_dir, "Data directory"))
    errors.extend(check_directory(config.profile_dir, "Profile directory"))
    errors.extend(check_directory(config.logs_dir, "Logs directory"))
    errors.extend(check_directory(config.exports_dir, "Exports directory"))

    if config.environment == "production":
        if config.show_debug_errors:
            warnings.append("Debug errors are visible in production mode.")

        if config.allow_profile_saving:
            warnings.append(
                "Profile saving is enabled. Make sure profile storage is approved for production."
            )

    gitignore = Path(".gitignore")

    if gitignore.exists():
        gitignore_text = gitignore.read_text(encoding="utf-8", errors="ignore")

        recommended_ignores = [
            "data/profiles/",
            "logs/",
            "exports/",
            "training_samples/",
            "*.pt",
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