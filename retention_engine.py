from datetime import datetime, timedelta, timezone
from typing import Any, Dict


class RetentionEngine:
    """
    Modified SM2 spaced repetition engine for OpenDoor.

    Quality score:
    0 = complete blackout
    1 = incorrect, barely remembered
    2 = incorrect, but familiar
    3 = correct with difficulty
    4 = correct with some hesitation
    5 = perfect recall
    """

    MIN_EASINESS_FACTOR = 1.3
    DEFAULT_EASINESS_FACTOR = 2.5

    @staticmethod
    def calculate_next_review(
        current_state: Dict[str, Any],
        quality_score: int,
    ) -> Dict[str, Any]:
        if not isinstance(quality_score, int):
            raise TypeError("quality_score must be an integer from 0 to 5.")

        if quality_score < 0 or quality_score > 5:
            raise ValueError("quality_score must be between 0 and 5.")

        easiness_factor = float(
            current_state.get(
                "easiness_factor",
                RetentionEngine.DEFAULT_EASINESS_FACTOR,
            )
        )

        repetitions = int(current_state.get("repetitions", 0))
        interval_days = int(current_state.get("interval_days", 0))

        if quality_score >= 3:
            if repetitions == 0:
                interval_days = 1
            elif repetitions == 1:
                interval_days = 6
            else:
                interval_days = int(round(interval_days * easiness_factor))

            repetitions += 1
        else:
            repetitions = 0
            interval_days = 1

        easiness_factor = easiness_factor + (
            0.1 - (5 - quality_score) * (0.08 + (5 - quality_score) * 0.02)
        )

        if easiness_factor < RetentionEngine.MIN_EASINESS_FACTOR:
            easiness_factor = RetentionEngine.MIN_EASINESS_FACTOR

        last_reviewed = datetime.now(timezone.utc)
        next_review = last_reviewed + timedelta(days=interval_days)

        return {
            "easiness_factor": round(easiness_factor, 2),
            "repetitions": repetitions,
            "interval_days": interval_days,
            "last_reviewed_at": last_reviewed.isoformat(),
            "next_review_due": next_review.isoformat(),
        }


def run_demo() -> None:
    print("MiniDoorLM / OpenDoor Retention Engine Demo")
    print("------------------------------------------")

    current_stats = {
        "easiness_factor": 2.5,
        "repetitions": 1,
        "interval_days": 1,
    }

    print("Current retention state:")
    for key, value in current_stats.items():
        print(f"{key}: {value}")

    quality_score = 4
    print(f"\nUser recall quality score: {quality_score}")

    updated_stats = RetentionEngine.calculate_next_review(
        current_stats,
        quality_score=quality_score,
    )

    print("\nUpdated retention state:")
    for key, value in updated_stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    run_demo()