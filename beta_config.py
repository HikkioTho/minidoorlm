from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class BetaConfig:
    """
    Central beta configuration for OpenDoor.

    This avoids scattering local paths and beta settings across the app.
    Later, these values can come from environment variables when deployed.
    """

    app_name: str
    environment: str
    data_dir: Path
    profile_dir: Path
    logs_dir: Path
    exports_dir: Path
    show_debug_errors: bool
    allow_profile_saving: bool
    allow_assignment_exports: bool


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_beta_config() -> BetaConfig:
    environment = os.getenv("OPENDOOR_ENV", "local_beta").strip()

    data_dir = Path(os.getenv("OPENDOOR_DATA_DIR", "data"))
    logs_dir = Path(os.getenv("OPENDOOR_LOGS_DIR", "logs"))
    exports_dir = Path(os.getenv("OPENDOOR_EXPORTS_DIR", "exports"))
    profile_dir = Path(os.getenv("OPENDOOR_PROFILE_DIR", str(data_dir / "profiles")))

    return BetaConfig(
        app_name=os.getenv("OPENDOOR_APP_NAME", "OpenDoor Beta"),
        environment=environment,
        data_dir=data_dir,
        profile_dir=profile_dir,
        logs_dir=logs_dir,
        exports_dir=exports_dir,
        show_debug_errors=env_bool("OPENDOOR_SHOW_DEBUG_ERRORS", default=False),
        allow_profile_saving=env_bool("OPENDOOR_ALLOW_PROFILE_SAVING", default=True),
        allow_assignment_exports=env_bool("OPENDOOR_ALLOW_ASSIGNMENT_EXPORTS", default=False),
    )