import re
from dataclasses import dataclass
from typing import List


@dataclass
class HomeworkReview:
    label: str
    score: int
    strengths: List[str]
    improvements: List[str]
    next_steps: List[str]


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def review_homework_response(topic: str, response: str) -> HomeworkReview:
    topic_clean = " ".join(str(topic or "").lower().split())
    response_clean = " ".join(str(response or "").lower().split())
    word_count = count_words(response)

    score = 0
    strengths: List[str] = []
    improvements: List[str] = []
    next_steps: List[str] = []

    if word_count >= 25:
        score += 2
        strengths.append("The response has enough length for a basic explanation.")
    else:
        improvements.append("The response is short. Add more explanation and one example.")

    if topic_clean and any(word in response_clean for word in topic_clean.split()[:3]):
        score += 2
        strengths.append("The response connects to the assigned topic.")
    else:
        improvements.append("Connect the answer back to the assigned topic more clearly.")

    if any(word in response_clean for word in ["because", "why", "means", "therefore"]):
        score += 2
        strengths.append("The response includes reasoning.")
    else:
        improvements.append("Add a because/why explanation, not just a statement.")

    if any(word in response_clean for word in ["for example", "example", "like", "similar"]):
        score += 2
        strengths.append("The response includes or hints at an example.")
    else:
        improvements.append("Add one concrete example or analogy.")

    if any(word in response_clean for word in ["confusing", "unclear", "question", "still"]):
        score += 1
        strengths.append("The learner identified uncertainty.")
    else:
        next_steps.append("List one part that still feels unclear.")

    if score >= 7:
        label = "strong_beta_review"
    elif score >= 4:
        label = "needs_more_detail"
    else:
        label = "incomplete"

    if not next_steps:
        next_steps.append("Revise once using one example, one analogy, and one self-check question.")

    return HomeworkReview(
        label=label,
        score=score,
        strengths=strengths,
        improvements=improvements,
        next_steps=next_steps,
    )


def format_homework_review(review: HomeworkReview) -> str:
    lines = [
        f"Review label: {review.label}",
        f"Score: {review.score}/9",
        "",
        "Strengths:",
    ]

    if review.strengths:
        for item in review.strengths:
            lines.append(f"- {item}")
    else:
        lines.append("- None detected yet.")

    lines.append("")
    lines.append("Improvements:")

    if review.improvements:
        for item in review.improvements:
            lines.append(f"- {item}")
    else:
        lines.append("- No major improvements detected in beta review.")

    lines.append("")
    lines.append("Next steps:")

    for item in review.next_steps:
        lines.append(f"- {item}")

    return "\n".join(lines)