import re
from dataclasses import dataclass
from typing import Dict, List


AI_BUZZWORDS = [
    "delve",
    "tapestry",
    "navigate",
    "moreover",
    "ultimately",
    "testament",
    "seamless",
    "leverage",
    "unlock",
    "empower",
    "transformative",
    "cutting-edge",
    "in today's fast-paced world",
    "in conclusion",
]

EMPTY_OPENINGS = [
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "in the modern era",
    "as we all know",
    "it is important to note",
]

SYCOPHANCY_PHRASES = [
    "great question",
    "excellent question",
    "you're absolutely right",
    "you are exactly right",
    "fantastic insight",
    "brilliant question",
]

VAGUE_WORDS = [
    "things",
    "stuff",
    "various",
    "many",
    "several",
    "important",
    "useful",
    "helpful",
    "effective",
    "better",
]


@dataclass
class ContentQualityDecision:
    passed: bool
    label: str
    score: int
    penalties: Dict[str, int]
    issues: List[str]
    recommendations: List[str]


def normalize_text(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def count_matches(text: str, phrases: List[str]) -> int:
    normalized = normalize_text(text)
    return sum(1 for phrase in phrases if phrase in normalized)


def sentence_lengths(text: str) -> List[int]:
    sentences = re.split(r"[.!?]+", text)
    lengths = []

    for sentence in sentences:
        words = re.findall(r"\b\w+\b", sentence)

        if words:
            lengths.append(len(words))

    return lengths


def has_phantom_citation_risk(text: str) -> bool:
    citation_patterns = [
        r"\[\d+\]",
        r"\(source:\s*[^)]+\)",
        r"https?://\S+",
        r"according to [A-Z][A-Za-z\s]+(?:University|Institute|Journal)",
    ]

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in citation_patterns)


def repeated_phrase_penalty(text: str) -> int:
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    if len(words) < 20:
        return 0

    penalty = 0

    for size in [2, 3, 4]:
        phrases = [
            tuple(words[index:index + size])
            for index in range(0, len(words) - size + 1)
        ]

        counts = {}

        for phrase in phrases:
            counts[phrase] = counts.get(phrase, 0) + 1

        if any(count >= 4 for count in counts.values()):
            penalty += 2

    return penalty


def evaluate_content_quality(text: str) -> ContentQualityDecision:
    penalties: Dict[str, int] = {}
    issues: List[str] = []
    recommendations: List[str] = []

    if not text or not text.strip():
        return ContentQualityDecision(
            passed=False,
            label="reject",
            score=0,
            penalties={"empty_output": 10},
            issues=["Output is empty."],
            recommendations=["Generate or provide real content before evaluation."],
        )

    buzzword_count = count_matches(text, AI_BUZZWORDS)

    if buzzword_count:
        penalties["ai_buzzwords"] = min(5, buzzword_count)
        issues.append(f"Detected {buzzword_count} AI-ish buzzword or phrase match(es).")
        recommendations.append("Use concrete words and specific examples instead of generic AI phrasing.")

    empty_opening_count = count_matches(text, EMPTY_OPENINGS)

    if empty_opening_count:
        penalties["empty_opening"] = 3
        issues.append("Detected generic opening phrase.")
        recommendations.append("Start directly with the learner's topic instead of a generic opening.")

    sycophancy_count = count_matches(text, SYCOPHANCY_PHRASES)

    if sycophancy_count:
        penalties["sycophancy"] = 2
        issues.append("Detected overly agreeable or flattering language.")
        recommendations.append("Use useful feedback instead of exaggerated praise.")

    vague_count = count_matches(text, VAGUE_WORDS)

    if vague_count >= 6:
        penalties["vague_language"] = 3
        issues.append("Detected lots of vague words.")
        recommendations.append("Replace vague words with concrete tasks, terms, or examples.")

    lengths = sentence_lengths(text)

    if lengths:
        short_sentences = [length for length in lengths if length <= 5]

        if len(short_sentences) >= 6:
            penalties["staccato_sentences"] = 2
            issues.append("Detected many very short sentences.")
            recommendations.append("Mix short instructions with fuller explanations.")

    repetition = repeated_phrase_penalty(text)

    if repetition:
        penalties["repetition"] = repetition
        issues.append("Detected repeated phrase patterns.")
        recommendations.append("Reduce repeated wording and add more specific content.")

    if has_phantom_citation_risk(text):
        penalties["citation_review_needed"] = 2
        issues.append("Detected citation-like content that needs source verification.")
        recommendations.append("Verify citations or remove source-looking claims before showing users.")

    score = max(0, 10 - sum(penalties.values()))

    if score >= 8:
        label = "clean"
    elif score >= 5:
        label = "needs_review"
    elif score >= 3:
        label = "weak"
    else:
        label = "reject"

    passed = label in {"clean", "needs_review"}

    if not issues:
        issues.append("No major AI-ism issues detected.")

    if not recommendations:
        recommendations.append("Content passed the beta style check.")

    return ContentQualityDecision(
        passed=passed,
        label=label,
        score=score,
        penalties=penalties,
        issues=issues,
        recommendations=recommendations,
    )


def format_content_quality_report(decision: ContentQualityDecision) -> str:
    status = "PASSED" if decision.passed else "REVIEW REQUIRED"

    lines = [
        f"Content Quality Guard: {status}",
        f"Label: {decision.label}",
        f"Score: {decision.score}/10",
        "",
        "Issues:",
    ]

    for issue in decision.issues:
        lines.append(f"- {issue}")

    lines.append("")
    lines.append("Recommendations:")

    for recommendation in decision.recommendations:
        lines.append(f"- {recommendation}")

    if decision.penalties:
        lines.append("")
        lines.append("Penalties:")

        for name, value in decision.penalties.items():
            lines.append(f"- {name}: -{value}")

    return "\n".join(lines)


if __name__ == "__main__":
    sample = (
        "Today we will learn soldering basics. "
        "A soldering iron heats a metal joint so solder can flow and connect parts. "
        "Practice by explaining why heat, safety, and clean contact matter."
    )

    decision = evaluate_content_quality(sample)
    print(format_content_quality_report(decision))