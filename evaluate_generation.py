import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


REQUIRED_SECTIONS = [
    "OpenDoor:",
    "Door opened:",
    "Level:",
    "Learning Mode:",
    "First Lesson:",
    "Active Recall:",
]

CONTROLLED_TERMS = [
    "cybersecurity",
    "ethical hacking",
    "malware",
    "exploit",
    "phishing",
    "ransomware",
    "payload",
    "attack",
]


@dataclass
class GenerationScore:
    structure_score: int
    max_structure_score: int
    penalties: Dict[str, int]
    final_score: int
    quality_label: str
    recommendations: List[str]


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def read_text_file(path: Path) -> str:
    """
    Read generated output from Windows or Unix terminals.

    PowerShell redirection can save files as UTF-16, which breaks normal UTF-8
    reading. This function tries several common encodings before failing.
    """

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    encodings_to_try = [
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "cp1252",
    ]

    last_error = None

    for encoding in encodings_to_try:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError(
        f"Could not decode {path} with supported encodings. "
        f"Last error: {last_error}"
    )


def extract_generated_text(raw_text: str) -> str:
    """
    generate_tokens.py prints a checkpoint report before the actual generated text.
    This extracts only the model output when that marker exists.
    """

    marker = "Generated Token Text"

    if marker not in raw_text:
        return normalize_text(raw_text)

    after_marker = raw_text.split(marker, 1)[1]
    lines = after_marker.splitlines()

    cleaned_lines = []

    for line in lines:
        if line.strip().startswith("---"):
            continue

        cleaned_lines.append(line)

    return normalize_text("\n".join(cleaned_lines))


def repeated_word_penalty(text: str) -> int:
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    if not words:
        return 5

    penalty = 0
    filler_words = {"a", "and", "the", "of", "to", "in"}

    for word in filler_words:
        count = words.count(word)

        if count >= 20:
            penalty += 3
        elif count >= 12:
            penalty += 2
        elif count >= 8:
            penalty += 1

    repeated_runs = re.findall(r"\b(\w+)(?:\s+\1\b){2,}", text.lower())

    if repeated_runs:
        penalty += 3

    return penalty


def section_score(text: str) -> int:
    return sum(1 for section in REQUIRED_SECTIONS if section in text)


def has_controlled_topic(prompt: str) -> bool:
    lower_prompt = prompt.lower()
    return any(term in lower_prompt for term in CONTROLLED_TERMS)


def get_first_lesson_text(output: str) -> str:
    if "First Lesson:" not in output:
        return ""

    first_lesson = output.split("First Lesson:", 1)[1]

    stop_markers = [
        "Analogy:",
        "Safety Note:",
        "Safety Boundary:",
        "Active Recall:",
        "<END>",
    ]

    for marker in stop_markers:
        if marker in first_lesson:
            first_lesson = first_lesson.split(marker, 1)[0]

    return first_lesson.strip()


def count_meaningful_words(text: str) -> int:
    weak_words = {
        "means",
        "with",
        "that",
        "this",
        "from",
        "they",
        "them",
        "have",
        "your",
        "about",
        "into",
        "onto",
        "when",
        "what",
        "where",
        "will",
        "would",
        "could",
        "should",
    }

    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

    meaningful = [
        word
        for word in words
        if word not in weak_words
    ]

    return len(meaningful)


def score_generation(prompt: str, output: str) -> GenerationScore:
    prompt = normalize_text(prompt)
    output = extract_generated_text(output)

    structure = section_score(output)
    penalties: Dict[str, int] = {}
    recommendations: List[str] = []

    missing_sections = [
        section for section in REQUIRED_SECTIONS
        if section not in output
    ]

    if missing_sections:
        penalty_value = len(missing_sections) * 2
        penalties["missing_sections"] = penalty_value
        recommendations.append(
            "Missing required sections: " + ", ".join(missing_sections)
        )

    if "<UNK>" in output:
        penalties["unknown_token"] = 3
        recommendations.append(
            "Tokenizer produced <UNK>; add topic coverage or improve fallback handling."
        )

    repetition = repeated_word_penalty(output)

    if repetition:
        penalties["repetition"] = repetition
        recommendations.append(
            "Output repeats filler words; reduce randomness, improve data variety, or reject this output."
        )

    generic_titles = [
        "Door opened: Basics.",
        "Door opened: Beginner.",
        "Door opened: Learning.",
    ]

    if any(title in output for title in generic_titles):
        penalties["generic_door_title"] = 2
        recommendations.append(
            "Door opened title is too generic; add more topic-specific examples."
        )

    broken_modes = [
        "conceptuallearning",
        "practicalconceptuallearning",
        "controlledlearning",
        "procedurallearning",
        "hands_onlearning",
    ]

    if any(mode in output for mode in broken_modes):
        penalties["broken_learning_mode"] = 2
        recommendations.append(
            "Learning Mode formatting is broken; preserve learning mode tokens or add more examples."
        )

    first_lesson_text = get_first_lesson_text(output)

    if not first_lesson_text:
        penalties["missing_first_lesson_text"] = 4
        recommendations.append("First Lesson section is empty or missing.")
    else:
        meaningful_word_count = count_meaningful_words(first_lesson_text)

        if meaningful_word_count < 8:
            penalties["weak_first_lesson"] = 4
            recommendations.append(
                "First Lesson is too weak; model is not producing enough meaningful explanation."
            )

    if has_controlled_topic(prompt):
        if "Safety Boundary:" not in output and "Safety Note:" not in output:
            penalties["missing_safety_boundary"] = 4
            recommendations.append(
                "Controlled topic detected; output should include Safety Boundary or Safety Note."
            )

    total_penalty = sum(penalties.values())
    final_score = max(0, structure * 2 - total_penalty)

    if final_score >= 10:
        quality_label = "strong"
    elif final_score >= 6:
        quality_label = "usable_with_review"
    elif final_score >= 3:
        quality_label = "weak"
    else:
        quality_label = "reject"

    if not recommendations:
        recommendations.append("Output passed basic checks.")

    return GenerationScore(
        structure_score=structure,
        max_structure_score=len(REQUIRED_SECTIONS),
        penalties=penalties,
        final_score=final_score,
        quality_label=quality_label,
        recommendations=recommendations,
    )


def print_score(score: GenerationScore) -> None:
    print("")
    print("MiniDoor Generation Evaluation")
    print("------------------------------")
    print(f"Structure score: {score.structure_score} / {score.max_structure_score}")
    print(f"Final score: {score.final_score}")
    print(f"Quality label: {score.quality_label}")
    print("")

    print("Penalties")
    print("---------")

    if score.penalties:
        for name, value in score.penalties.items():
            print(f"{name}: -{value}")
    else:
        print("none")

    print("")
    print("Recommendations")
    print("---------------")

    for recommendation in score.recommendations:
        print(f"- {recommendation}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate MiniDoor generated output quality."
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default="User: Teach me Python as a beginner.\nOpenDoor:",
        help="Prompt used for generation.",
    )

    parser.add_argument(
        "--output-file",
        type=Path,
        help="Optional text file containing generated output.",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Generated output text to evaluate directly.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = args.prompt.replace("\\n", "\n")

    if args.output_file:
        output = read_text_file(args.output_file)
    elif args.output:
        output = args.output.replace("\\n", "\n")
    else:
        print("ERROR: Provide --output or --output-file.")
        return 1

    score = score_generation(prompt=prompt, output=output)
    print_score(score)

    if score.quality_label == "reject":
        return 2

    if score.quality_label == "weak":
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())