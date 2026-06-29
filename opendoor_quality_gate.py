from dataclasses import dataclass
from typing import List

from evaluate_generation import GenerationScore, score_generation


PASSING_LABELS = {
    "strong",
    "usable_with_review",
}


@dataclass
class QualityGateDecision:
    approved: bool
    label: str
    final_score: int
    structure_score: int
    max_structure_score: int
    reason: str
    recommendations: List[str]


def review_minidoor_output(prompt: str, output: str) -> QualityGateDecision:
    score: GenerationScore = score_generation(
        prompt=prompt,
        output=output,
    )

    approved = score.quality_label in PASSING_LABELS

    if approved:
        reason = (
            "MiniDoor output passed the quality gate. "
            "It can be shown with review awareness."
        )
    else:
        reason = (
            "MiniDoor output did not pass the quality gate. "
            "Use LessonBuilder fallback instead."
        )

    return QualityGateDecision(
        approved=approved,
        label=score.quality_label,
        final_score=score.final_score,
        structure_score=score.structure_score,
        max_structure_score=score.max_structure_score,
        reason=reason,
        recommendations=score.recommendations,
    )


def format_quality_gate_report(decision: QualityGateDecision) -> str:
    status = "APPROVED" if decision.approved else "FALLBACK REQUIRED"

    lines = [
        f"MiniDoor Quality Gate: {status}",
        f"Label: {decision.label}",
        f"Final score: {decision.final_score}",
        f"Structure score: {decision.structure_score} / {decision.max_structure_score}",
        f"Reason: {decision.reason}",
        "",
        "Recommendations:",
    ]

    for recommendation in decision.recommendations:
        lines.append(f"- {recommendation}")

    return "\n".join(lines)