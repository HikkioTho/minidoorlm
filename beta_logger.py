import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from beta_config import get_beta_config


def ensure_log_dir() -> Path:
    config = get_beta_config()
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    return config.logs_dir


def write_jsonl(filename: str, payload: Dict[str, Any]) -> Path:
    """
    Write one structured log event as JSONL.

    JSONL is easy to append, easy to inspect, and does not require a database
    for the beta demo.
    """

    log_dir = ensure_log_dir()
    path = log_dir / filename

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")

    return path


def log_beta_event(
    event_type: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Log normal beta activity.

    Examples:
        profile_saved
        assignment_created
        topic_rejected
        submission_checked
    """

    return write_jsonl(
        filename="beta_events.jsonl",
        payload={
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        },
    )


def log_beta_error(
    error: Exception,
    user_action: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Log errors without showing raw stack traces to demo users.
    """

    return write_jsonl(
        filename="beta_errors.jsonl",
        payload={
            "event_type": "error",
            "user_action": user_action,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "metadata": metadata or {},
        },
    )


def safe_error_message(error: Exception) -> str:
    """
    User-facing beta error message.

    The real traceback goes to logs/beta_errors.jsonl.
    """

    return (
        "Something went wrong during the beta demo. "
        "The error was logged so it can be reviewed later."
    )