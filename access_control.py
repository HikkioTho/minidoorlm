from dataclasses import dataclass
from typing import Dict


@dataclass
class AccessDecision:
    allowed: bool
    reason: str
    required_role: str
    user_role: str
    feature_name: str


class AccessControl:
    """
    AccessControl decides who can use each OpenDoor feature.

    Core rule:
    new powerful features start locked.
    locked accounts cannot use learning, upload, export, or training features.
    """

    ROLE_LEVELS: Dict[str, int] = {
        "locked_pending_review": -1,
        "guest": 0,
        "user": 1,
        "trusted_user": 2,
        "moderator": 3,
        "admin": 4,
    }

    FEATURE_RULES: Dict[str, str] = {
        "text_learning": "guest",
        "memory_export": "user",
        "public_safe_export": "user",
        "media_upload_image": "trusted_user",
        "media_upload_audio": "trusted_user",
        "media_upload_video": "trusted_user",
        "training_candidate_create": "admin",
        "training_candidate_review": "admin",
        "backlog_scan": "admin",
        "admin_review_queue": "moderator",
    }

    @classmethod
    def can_access(cls, user_role: str, feature_name: str) -> AccessDecision:
        if user_role == "locked_pending_review":
            return AccessDecision(
                allowed=False,
                reason="Account is locked pending review.",
                required_role="review_clearance",
                user_role=user_role,
                feature_name=feature_name,
            )

        required_role = cls.FEATURE_RULES.get(feature_name)

        if required_role is None:
            return AccessDecision(
                allowed=False,
                reason="Unknown feature. Access denied by default.",
                required_role="admin",
                user_role=user_role,
                feature_name=feature_name,
            )

        user_level = cls.ROLE_LEVELS.get(user_role, 0)
        required_level = cls.ROLE_LEVELS.get(required_role, 999)

        if user_level >= required_level:
            return AccessDecision(
                allowed=True,
                reason="Access granted.",
                required_role=required_role,
                user_role=user_role,
                feature_name=feature_name,
            )

        return AccessDecision(
            allowed=False,
            reason="User role does not meet feature requirement.",
            required_role=required_role,
            user_role=user_role,
            feature_name=feature_name,
        )


def run_demo():
    tests = [
        ("guest", "text_learning"),
        ("guest", "media_upload_image"),
        ("user", "memory_export"),
        ("trusted_user", "media_upload_video"),
        ("locked_pending_review", "text_learning"),
        ("moderator", "admin_review_queue"),
        ("admin", "backlog_scan"),
        ("user", "unknown_feature"),
    ]

    for role, feature in tests:
        decision = AccessControl.can_access(role, feature)
        print(decision)


if __name__ == "__main__":
    run_demo()